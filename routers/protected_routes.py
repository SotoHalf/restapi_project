from fastapi import APIRouter, Depends
import schemas, utils.auth as auth

router = APIRouter()

# PROTECTED ROUTES

@router.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: dict = Depends(auth.get_current_user)):
    """
    Get details of the currently logged-in user.
    """
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
