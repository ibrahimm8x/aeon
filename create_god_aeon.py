#!/usr/bin/env python3
"""
Script to create the GOD AEON user account
This creates a special user with the highest privileges for personal use
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import User
from app.models.user import UserCreate, UserRole
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_god_aeon_user():
    """Create the GOD AEON user account"""
    
    # GOD AEON user details
    god_aeon_data = {
        "username": "god_aeon",
        "email": "god.aeon@aeon.ai",
        "password": "GodAeon2025!@#",  # Strong password for the god account
        "full_name": "God AEON - Master Creator",
        "bio": "The original creator and master of AEON. Possesses ultimate authority and control over the system."
    }
    
    try:
        # Get database session
        db = next(get_db())
        
        # Check if GOD AEON already exists
        existing_user = db.query(User).filter(User.username == god_aeon_data["username"]).first()
        if existing_user:
            logger.info("GOD AEON user already exists!")
            print(f"✅ GOD AEON user already exists with ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            print(f"   Role: {existing_user.role}")
            return existing_user
        
        # Create GOD AEON user
        hashed_password = get_password_hash(god_aeon_data["password"])
        god_aeon_user = User(
            username=god_aeon_data["username"],
            email=god_aeon_data["email"],
            hashed_password=hashed_password,
            full_name=god_aeon_data["full_name"],
            bio=god_aeon_data["bio"],
            role=UserRole.GOD_AEON.value,
            is_active=True
        )
        
        db.add(god_aeon_user)
        db.commit()
        db.refresh(god_aeon_user)
        
        logger.info(f"GOD AEON user created successfully: {god_aeon_user.username}")
        
        print("🎉 GOD AEON user created successfully!")
        print("=" * 50)
        print(f"👑 Username: {god_aeon_user.username}")
        print(f"📧 Email: {god_aeon_user.email}")
        print(f"🔑 Password: {god_aeon_data['password']}")
        print(f"👤 Full Name: {god_aeon_user.full_name}")
        print(f"🏆 Role: {god_aeon_user.role}")
        print(f"🆔 User ID: {god_aeon_user.id}")
        print(f"📝 Bio: {god_aeon_user.bio}")
        print("=" * 50)
        print("⚠️  IMPORTANT: Save these credentials securely!")
        print("🔐 This account has ultimate authority over AEON")
        print("=" * 50)
        
        return god_aeon_user
        
    except Exception as e:
        logger.error(f"Error creating GOD AEON user: {str(e)}")
        print(f"❌ Error creating GOD AEON user: {str(e)}")
        return None
    finally:
        db.close()


def create_regular_aeon_user():
    """Create a regular AEON user for testing"""
    
    aeon_data = {
        "username": "aeon_assistant",
        "email": "aeon@aeon.ai",
        "password": "AeonAssistant2025!@#",
        "full_name": "AEON Assistant",
        "bio": "The main AEON AI assistant for general interactions"
    }
    
    try:
        db = next(get_db())
        
        # Check if AEON assistant already exists
        existing_user = db.query(User).filter(User.username == aeon_data["username"]).first()
        if existing_user:
            logger.info("AEON Assistant user already exists!")
            print(f"✅ AEON Assistant user already exists with ID: {existing_user.id}")
            return existing_user
        
        # Create AEON assistant user
        hashed_password = get_password_hash(aeon_data["password"])
        aeon_user = User(
            username=aeon_data["username"],
            email=aeon_data["email"],
            hashed_password=hashed_password,
            full_name=aeon_data["full_name"],
            bio=aeon_data["bio"],
            role=UserRole.ADMIN.value,
            is_active=True
        )
        
        db.add(aeon_user)
        db.commit()
        db.refresh(aeon_user)
        
        logger.info(f"AEON Assistant user created successfully: {aeon_user.username}")
        
        print("🤖 AEON Assistant user created successfully!")
        print(f"   Username: {aeon_user.username}")
        print(f"   Role: {aeon_user.role}")
        
        return aeon_user
        
    except Exception as e:
        logger.error(f"Error creating AEON Assistant user: {str(e)}")
        print(f"❌ Error creating AEON Assistant user: {str(e)}")
        return None
    finally:
        db.close()


def list_all_users():
    """List all users in the system"""
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print("\n📋 All Users in AEON System:")
        print("=" * 60)
        for user in users:
            status = "🟢 Active" if user.is_active else "🔴 Inactive"
            print(f"ID: {user.id} | {user.username} | {user.role} | {status}")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name}")
            print("-" * 40)
        
        return users
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        print(f"❌ Error listing users: {str(e)}")
        return []
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Creating GOD AEON User Account")
    print("=" * 50)
    
    # Create GOD AEON user
    god_aeon = create_god_aeon_user()
    
    # Create regular AEON assistant user
    print("\n" + "=" * 50)
    aeon_assistant = create_regular_aeon_user()
    
    # List all users
    print("\n" + "=" * 50)
    list_all_users()
    
    print("\n🎯 Setup Complete!")
    print("You can now use the GOD AEON account to access all features with ultimate privileges.") 