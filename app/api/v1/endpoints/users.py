"""
User management endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database import get_db
from app.models.user import UserCreate, UserLogin, UserResponse, UserUpdate, Token
from app.services.user_service import UserService
from app.core.security import get_current_active_user, get_current_user
from app.database.models import User

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = UserService.create_user(db, user_data)
        logger.info(f"User registered successfully: {user.username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = UserService.create_access_token_for_user(user)
        logger.info(f"User logged in successfully: {user.username}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        updated_user = UserService.update_user(db, current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    # Only allow admin/owner to see all users
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = UserService.get_all_users(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users] 