from mongo.mongo_async import MongoLoaderAsync
from mongo.service import load_all_async
from datetime import datetime
import asyncio

async def watch_process_load(process, name, db_manager, logger, logger_output):
    results = db_manager.db.results_etl

    try:
        #save logs in mongoDB
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            msg = line.decode().strip()
            logger.info(msg, extra={"pid": process.pid})

        #wait to end the process
        returncode = await process.wait()

        if returncode == 0:
            try:
                # if everything it's fine launch de upload
                loader = MongoLoaderAsync(db_manager.client, db_manager.db.name)
                output = await load_all_async(loader)
                if not output:
                    output = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [mongo] [async] No new records"
                else:
                    output = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [mongo] [async] {output}"
                logger_output.info(output)
                await results.update_one(
                    {"_id": name},
                    {"$set": {
                        "status": "finished",
                        "finished_at": datetime.utcnow()
                    }}
                )

            except Exception as e:
                error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [mongo] [async] {str(e)}"
                logger_output.info(error_msg)
                await results.update_one(
                    {"_id": name},
                    {"$set": {
                        "status": "error",
                        "error": str(e)
                    }}
                )
        else:
            error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [mongo] [async] ETL process failed"
            logger_output.info(error_msg)
            await results.update_one(
                {"_id": name},
                {"$set": {
                    "status": "error",
                    "error": "ETL process failed"
                }}
            )

    except asyncio.CancelledError:
        try:
            import os, signal
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        error_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [mongo] [async] Cancelled by user"
        logger_output.info(error_msg)
        
        await results.update_one(
            {"_id": name},
            {"$set": {
                "status": "cancelled",
                "finished_at": datetime.utcnow(),
                "error": "Cancelled by user"
            }}
        )