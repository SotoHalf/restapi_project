from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
import schemas, utils.auth as auth
import asyncio
import os
import signal
from mongo.mongo_async import MongoLoaderAsync
from mongo.service import load_all_async
from database import db_manager
from datetime import datetime
from utils.process_manager import watch_process_load

import database
from bson import ObjectId
from fastapi import Body
import logging

router = APIRouter()

# PROTECTED ROUTES

@router.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: dict = Depends(auth.get_current_user)):
    # Get details of the currently logged-in user.
    return current_user

@router.get("/system/status")
async def get_system_status(current_user: dict = Depends(auth.get_current_user)):
    """
    Simulates a secure command endpoint for distributed nodes.
    """
    return {
        "status": "operational",
        "secret_data": "Whatever you want to hide",
        "authenticated_as": current_user["username"],
        "role": current_user["role"],
        "backend": "MongoDB Atlas"
    }

# API 1

# ------------------------------------------------------------

@router.get("/admin/etl-api1/logs")
async def get_etl_api1_logs(limit: int = 10, current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    name_etl_log = "etl_api1"
    results = db_manager.db.results_etl
    logs = db_manager.db.logs

    etl = await results.find_one({"_id": name_etl_log})

    if not etl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETL not found"
        )

    pid = etl.get("pid")
    if not pid:
        return {"lines": []}
    
    cursor = (
        logs.find(
            {
                "pid": pid,
                "logger": name_etl_log
            },
            {
                "_id": 0,
                "timestamp": 1,
                "level": 1,
                "message": 1
            }
        )
        .sort("timestamp", -1)
        .limit(limit)
    )

    docs = await cursor.to_list(length=limit)

    docs.reverse()

    return {
        "pid": pid,
        "lines": [
            f"[{d['timestamp']}] [{d['level']}] {d['message']}"
            for d in docs
        ]
    }

@router.post("/admin/etl-api1/cancel", status_code=200)
async def cancel_etl_api1(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    logger = logging.getLogger("etl-api1-cancel")

    name_etl_log = "etl_api1"
    results = db_manager.db.results_etl

    # gets the ETL in execution
    etl = await results.find_one({
        "_id": name_etl_log,
        "status": "running"
    })

    if not etl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETL api1 is not running"
        )

    pid = etl.get("pid")
    if not pid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ETL running but PID not found"
        )

    try:
        os.killpg(pid, signal.SIGTERM)  # kill
        logger.warning("ETL api1 cancelled (SIGTERM) pid=%s", pid)
    except ProcessLookupError:
        logger.warning("ETL api1 pid=%s not found", pid)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to kill this process"
        )

    await results.update_one(
        {"_id": name_etl_log},
        {"$set": {
            "status": "cancelled",
            "finished_at": datetime.utcnow(),
            "error": "Cancelled by admin"
        }}
    )

    return {
        "status": "cancelled",
        "pid": pid
    }

@router.post("/admin/etl-api1/run", status_code=202)
async def run_sh_and_load(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    name_etl_log = "etl_api1"
    results = db_manager.db.results_etl

    # avoid two ETL at the same time
    running = await results.find_one({
        "_id": name_etl_log,
        "status": "running"
    })

    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ETL api1 is already running by you or other user"
        )

    # launch process
    process = await asyncio.create_subprocess_exec(
        "python3", "-m", "etl.pipelines.themealdb_pipeline",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True
    )


    # save initial state
    await results.update_one(
        {"_id": name_etl_log},
        {"$set": {
            "status": "running",
            "started_at": datetime.utcnow(),
            "finished_at": None,
            "pid": process.pid,
            "error": None
        }},
        upsert=True
    )

    #launch a watcher when the scrap ends launch de loader
    logger = logging.getLogger(name_etl_log)

    #final output
    timestamp = datetime.utcnow()
    logger_output = logging.getLogger(f"etl_api1_{timestamp}")

    asyncio.create_task(
        watch_process_load(process, name_etl_log, db_manager, logger, logger_output)
    )

    return {
        "status": "accepted",
        "message": "ETL api1 started",
        "pid": process.pid
    }

@router.get("/admin/etl-api1/status")
async def get_etl_status(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.results_etl
    etl_name = "etl_api1"

    status_doc = await logs.find_one({"_id": etl_name})

    if not status_doc:
        return {
            "status": "idle",
            "message": "ETL has not been started yet"
        }

    return {
        "status": status_doc.get("status", "unknown"),
        "started_at": status_doc.get("started_at"),
        "finished_at": status_doc.get("finished_at"),
        "error": status_doc.get("error")
    }

@router.get("/admin/etl-api1/results")
async def get_last_etl_result(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.logs
    etl_prefix = "etl_api1_"

    # last log with etl_api1_
    last_log = await logs.find_one(
        {"logger": {"$regex": f"^{etl_prefix}"}},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "message": 1}
    )

    if not last_log:
        return {"message": "Never has been run an ETL"}

    return {"message": last_log["message"]}

@router.get("/admin/etl-api1/history")
async def get_etl_history(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.logs
    etl_prefix = "etl_api1_"

    cursor = logs.find(
        {"logger": {"$regex": f"^{etl_prefix}"}},
        projection={"_id": 0, "message": 1}
    ).sort("timestamp", -1)

    all_logs = await cursor.to_list(length=None)

    messages = [log["message"] for log in all_logs]

    if not messages:
        messages = ["Never has been run an ETL"]

    return {"messages": messages}

# API 2

@router.get("/admin/etl-api2/logs")
async def get_etl_api2_logs(limit: int = 10, current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    name_etl_log = "etl_api2"
    results = db_manager.db.results_etl
    logs = db_manager.db.logs

    etl = await results.find_one({"_id": name_etl_log})

    if not etl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETL not found"
        )

    pid = etl.get("pid")
    if not pid:
        return {"lines": []}
    
    cursor = (
        logs.find(
            {
                "pid": pid,
                "logger": name_etl_log
            },
            {
                "_id": 0,
                "timestamp": 1,
                "level": 1,
                "message": 1
            }
        )
        .sort("timestamp", -1)
        .limit(limit)
    )

    docs = await cursor.to_list(length=limit)

    docs.reverse()

    return {
        "pid": pid,
        "lines": [
            f"[{d['timestamp']}] [{d['level']}] {d['message']}"
            for d in docs
        ]
    }

@router.post("/admin/etl-api2/cancel", status_code=200)
async def cancel_etl_api2(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    logger = logging.getLogger("etl-api2-cancel")

    name_etl_log = "etl_api2"
    results = db_manager.db.results_etl

    # gets the ETL in execution
    etl = await results.find_one({
        "_id": name_etl_log,
        "status": "running"
    })

    if not etl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ETL api2 is not running"
        )

    pid = etl.get("pid")
    if not pid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ETL running but PID not found"
        )

    try:
        os.killpg(pid, signal.SIGTERM)  # kill
        logger.warning("ETL api2 cancelled (SIGTERM) pid=%s", pid)
    except ProcessLookupError:
        logger.warning("ETL api2 pid=%s not found", pid)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to kill this process"
        )

    await results.update_one(
        {"_id": name_etl_log},
        {"$set": {
            "status": "cancelled",
            "finished_at": datetime.utcnow(),
            "error": "Cancelled by admin"
        }}
    )

    return {
        "status": "cancelled",
        "pid": pid
    }

@router.post("/admin/etl-api2/run", status_code=202)
async def run_sh_and_load(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    name_etl_log = "etl_api2"
    results = db_manager.db.results_etl

    # avoid two ETL at the same time
    running = await results.find_one({
        "_id": name_etl_log,
        "status": "running"
    })

    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ETL api2 is already running by you or other user"
        )

    # launch process
    process = await asyncio.create_subprocess_exec(
        "python3", "-m", "etl.pipelines.openfoodfacts_pipeline",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True
    )


    # save initial state
    await results.update_one(
        {"_id": name_etl_log},
        {"$set": {
            "status": "running",
            "started_at": datetime.utcnow(),
            "finished_at": None,
            "pid": process.pid,
            "error": None
        }},
        upsert=True
    )

    #launch a watcher when the scrap ends launch de loader
    logger = logging.getLogger(name_etl_log)

    #final output
    timestamp = datetime.utcnow()
    logger_output = logging.getLogger(f"etl_api2_{timestamp}")

    asyncio.create_task(
        watch_process_load(process, name_etl_log, db_manager, logger, logger_output)
    )

    return {
        "status": "accepted",
        "message": "ETL api2 started",
        "pid": process.pid
    }

@router.get("/admin/etl-api2/status")
async def get_etl_status(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.results_etl
    etl_name = "etl_api2"

    status_doc = await logs.find_one({"_id": etl_name})

    if not status_doc:
        return {
            "status": "idle",
            "message": "ETL has not been started yet"
        }

    return {
        "status": status_doc.get("status", "unknown"),
        "started_at": status_doc.get("started_at"),
        "finished_at": status_doc.get("finished_at"),
        "error": status_doc.get("error")
    }

@router.get("/admin/etl-api2/results")
async def get_last_etl_result(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.logs
    etl_prefix = "etl_api2_"

    # last log with etl_api2_
    last_log = await logs.find_one(
        {"logger": {"$regex": f"^{etl_prefix}"}},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "message": 1}
    )

    if not last_log:
        return {"message": "Never has been run an ETL"}

    return {"message": last_log["message"]}

@router.get("/admin/etl-api2/history")
async def get_etl_history(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )

    logs = db_manager.db.logs
    etl_prefix = "etl_api2_"

    cursor = logs.find(
        {"logger": {"$regex": f"^{etl_prefix}"}},
        projection={"_id": 0, "message": 1}
    ).sort("timestamp", -1)

    all_logs = await cursor.to_list(length=None)

    messages = [log["message"] for log in all_logs]

    if not messages:
        messages = ["Never has been run an ETL"]

    return {"messages": messages}

# ------------------------------------------------------------

@router.get("/admin/users", response_model=list[schemas.UserResponse])
async def admin_list_users(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")

    users = await db_manager.db["users"].find().to_list(1000)
    return users

@router.get("/admin/users/{user_id}", response_model=schemas.UserResponse)
async def admin_get_user(
    user_id: str,
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")

    user = await db_manager.db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.put("/admin/users/{user_id}", response_model=schemas.UserResponse)
async def update_user(user_id: str, user: schemas.UserCreate, current_user: dict = Depends(auth.get_current_user), db = Depends(database.get_db)):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    update_data = {k: v for k, v in user.dict().items() if v is not None}
    result = await db["users"].find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")

    result = await db_manager.db["users"].delete_one(
        {"_id": ObjectId(user_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/admin/collections")
async def list_collections(current_user: dict = Depends(auth.get_current_user)):
    """
    Get all collections in the database
    """
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        collections = await db_manager.db.list_collection_names()
        
        # Get basic info for each collection
        collections_info = []
        for coll_name in collections:
            try:
                coll = db_manager.db[coll_name]
                count = await coll.count_documents({})
                
                # Get sample document to show structure
                sample = await coll.find_one()
                sample_fields = list(sample.keys())[:5] if sample else []
                
                collections_info.append({
                    "name": coll_name,
                    "document_count": count,
                    "sample_fields": sample_fields[:3],  # First 3 fields
                    "has_id_field": "_id" in sample if sample else False
                })
            except Exception as coll_error:
                # Skip problematic collections
                continue
        
        return {
            "database": db_manager.db.name,
            "total_collections": len(collections_info),
            "collections": collections_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/admin/collection/{collection_name}")
async def get_collection_data(
    collection_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Get paginated data from a collection
    """
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    try:
        # Check if collection exists
        if collection_name not in await db_manager.db.list_collection_names():
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
        collection = db_manager.db[collection_name]
        
        # Calculate pagination
        skip = (page - 1) * limit
        total = await collection.count_documents({})
        
        # Get data with pagination
        cursor = collection.find().skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON
        for doc in documents:
            if "_id" in doc and isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])
        
        return {
            "collection": collection_name,
            "page": page,
            "limit": limit,
            "total_documents": total,
            "total_pages": (total + limit - 1) // limit,
            "has_next_page": page < ((total + limit - 1) // limit),
            "has_prev_page": page > 1,
            "documents": documents
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")




