from fastapi import APIRouter, Depends, HTTPException, status, Request
import schemas, utils.auth as auth
import asyncio
from mongo.mongo_async import MongoLoaderAsync
from mongo.service import load_all_async
from database import db_manager

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
