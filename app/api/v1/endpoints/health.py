"""
Health check endpoints
"""

from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.services.database import check_database_health

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "aeon-api",
        "version": "0.1.0"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including database connectivity"""
    try:
        # Check database health
        db_status = await check_database_health()
        
        return {
            "status": "healthy" if db_status["all_healthy"] else "degraded",
            "service": "aeon-api",
            "version": "0.1.0",
            "databases": db_status
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy") 