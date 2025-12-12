import logging
import sys
import datetime
import asyncio
import database

def setup_logging():
    """
    Configure logging for the application.
    """
    class MongoDBHandler(logging.Handler):
        def emit(self, record):
            if database.db_manager.db is not None:
                log_entry = self.format(record)
                log_document = {
                    "timestamp": datetime.datetime.now(datetime.timezone.utc),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "logger": record.name,
                    "raw": log_entry
                }
                # Use asyncio.create_task to run the async insert without blocking
                try:
                    asyncio.create_task(database.db_manager.db["logs"].insert_one(log_document))
                except Exception:
                    # Fallback or ignore if event loop is closed or other issues
                    pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            MongoDBHandler()
        ]
    )
    
    # Set lower level for some noisy libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
