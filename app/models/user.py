"""
User models and schemas for AEON
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles"""
    OWNER = "owner"
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="User's full name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, description="User password")


class UserLogin(BaseModel):
    """User login model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """User response model"""
    id: int
    role: UserRole = UserRole.OWNER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Authentication token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[int] = None 