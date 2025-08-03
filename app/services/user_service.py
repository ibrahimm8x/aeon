"""
User service layer for AEON
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.database.models import User
from app.models.user import UserCreate, UserUpdate, UserResponse, UserRole
from app.core.security import get_password_hash, authenticate_user, create_access_token
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """User service class"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == user_data.username) | (User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already registered"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            # Create new user
            hashed_password = get_password_hash(user_data.password)
            
            # Check if this is the first user (make them GOD_AEON) or assign appropriate role
            existing_users = db.query(User).count()
            if existing_users == 0:
                role = UserRole.GOD_AEON.value  # First user becomes GOD_AEON
            else:
                role = UserRole.OWNER.value  # Subsequent users become owners
                
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                bio=user_data.bio,
                role=role
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"New user created: {user_data.username}")
            return UserResponse.model_validate(db_user)
            
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed"
            )
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object"""
        return authenticate_user(db, username, password)
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user information"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None
        
        # Update fields if provided
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User updated: {db_user.username}")
        return UserResponse.model_validate(db_user)
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        
        logger.info(f"User deleted: {db_user.username}")
        return True
    
    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        """Create access token for user"""
        access_token_expires = None  # Use default from settings
        return create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        ) 