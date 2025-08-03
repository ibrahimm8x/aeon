"""
Test chat endpoints for web interface testing (no authentication required)
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database import get_db
from app.models.aeon import ChatRequest, ChatResponse
from app.services.aeon_service import AEONService
from app.database.models import User

router = APIRouter()
logger = get_logger(__name__)


@router.post("/test-chat", response_model=ChatResponse)
async def test_chat_with_aeon(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Test chat with AEON (no authentication required)"""
    try:
        # Get the first user for testing
        user = db.query(User).first()
        if not user:
            # Create a test user if none exists
            from app.core.security import get_password_hash
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                full_name="Test User",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        response = AEONService.chat_with_aeon(db, user.id, chat_request)
        logger.info(f"Test chat completed for user {user.username}")
        return response
    except Exception as e:
        logger.error(f"Test chat failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test chat failed: {str(e)}"
        )


@router.get("/test-status")
async def test_aeon_status(db: Session = Depends(get_db)):
    """Test AEON status (no authentication required)"""
    try:
        # Get the first user for testing
        user = db.query(User).first()
        if not user:
            return {"status": "no_users", "message": "No users found in database"}
        
        aeon_status = AEONService.get_aeon_status(db, user.id)
        return aeon_status
    except Exception as e:
        logger.error(f"Error getting test AEON status: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.get("/test-health")
async def test_health():
    """Test health endpoint"""
    return {
        "status": "healthy",
        "service": "aeon-test-api",
        "version": "0.1.0",
        "message": "Test endpoints are working"
    } 