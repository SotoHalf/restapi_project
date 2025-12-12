from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import models, schemas, utils.auth as auth, database, logging

router = APIRouter()

# PUBLIC ROUTES

@router.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db = Depends(database.get_db)):
    """
    Register a new Compute Node or Admin.
    Note the 'async def' and 'await' usage.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Registering user: {user.username}")
    # Check if user exists
    existing_user = await db["users"].find_one({"username": user.username})
    if existing_user:
        logger.warning(f"Registration failed: Username {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    
    # Create User Dict (MongoDB Document)
    user_doc = models.UserInDB(
        username=user.username,
        hashed_password=hashed_password
    ).model_dump()
    
    # Insert into MongoDB
    new_user = await db["users"].insert_one(user_doc)
    
    # Fetch the created user to return it (to get the generated _id)
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    
    logger.info(f"User registered successfully: {user.username}")
    return created_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(database.get_db)):
    """
    OAuth2 compliant token login.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt for user: {form_data.username}")
    user = await db["users"].find_one({"username": form_data.username})
    
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    refresh_token = auth.create_refresh_token(
        data={"sub": user["username"]}
    )
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(refresh_token: str = Depends(auth.oauth2_scheme), db = Depends(database.get_db)):
    """
    Get a new access token using a refresh token.
    """
    logger = logging.getLogger(__name__)
    try:
        username = auth.verify_refresh_token(refresh_token)
    except HTTPException:
        logger.warning("Refresh token validation failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user still exists
    user = await db["users"].find_one({"username": username})
    if not user:
        logger.warning(f"Refresh failed: User {username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    # Optionally rotate refresh token here
    new_refresh_token = auth.create_refresh_token(
        data={"sub": username}
    )
    
    logger.info(f"Token refreshed for user: {username}")
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
