"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, users, aeon, aeon_enhanced, phase3, test_chat

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(aeon.router, prefix="/aeon", tags=["aeon"])
api_router.include_router(aeon_enhanced.router, prefix="/aeon/enhanced", tags=["aeon_enhanced"])
api_router.include_router(phase3.router, prefix="/phase3", tags=["phase3"])
api_router.include_router(test_chat.router, prefix="/test", tags=["test"]) 