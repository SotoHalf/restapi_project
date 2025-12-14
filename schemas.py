from pydantic import BaseModel, BeforeValidator, Field
from typing import Optional, List, Annotated

# --- ObjectId Helper ---
# MongoDB uses ObjectIds, but JSON uses strings. This helper converts them.
PyObjectId = Annotated[str, BeforeValidator(str)]

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "role_user"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None  

class UserResponse(UserBase):
    # Map MongoDB's '_id' to 'id' in the JSON response
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    is_active: bool
    role: str

    class Config:
        populate_by_name = True
        from_attributes = True