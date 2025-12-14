from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
import schemas, utils.auth as auth
import asyncio
from mongo.mongo_async import MongoLoaderAsync
from mongo.service import load_all_async
from database import db_manager

import database
from bson import ObjectId
from fastapi import Body

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


@router.post("/admin/etl-api1", status_code=202)
async def run_sh_and_load(current_user: dict = Depends(auth.get_current_user)):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    # Run the shell script async
    process = await asyncio.create_subprocess_shell(
        "bash crontab_sh/run_etl_api1.sh",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Wait for the script to finish
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Error in script.sh: {stderr.decode()}"
        )

    # Once the script finishes, execute the CSV loading logic
    try:
        loader = MongoLoaderAsync(client=db_manager.client, db_name=db_manager.db.name)
        await load_all_async(loader)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in loader: {str(e)}")
    
    return {
        "status": "ok",
        "message": "Script executed and CSVs loaded"
    }

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




