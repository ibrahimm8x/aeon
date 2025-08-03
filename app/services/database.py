"""
Database service for health checks and connections
"""

import asyncio
from typing import Dict, Any
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


async def check_database_health() -> Dict[str, Any]:
    """
    Check health of all databases
    Returns status for Chroma and Neo4j
    """
    from app.services.vector_service import get_vector_service
    from app.services.graph_service import get_graph_service
    
    health_status = {
        "all_healthy": True,
        "chroma": {"status": "unknown", "error": None},
        "neo4j": {"status": "unknown", "error": None}
    }
    
    # Check Chroma health
    try:
        vector_service = await get_vector_service()
        chroma_health = await vector_service.get_health_status()
        health_status["chroma"] = chroma_health
        
        if chroma_health["status"] != "healthy":
            health_status["all_healthy"] = False
            
        logger.info("Chroma database health check completed")
    except Exception as e:
        health_status["chroma"]["status"] = "unhealthy"
        health_status["chroma"]["error"] = str(e)
        health_status["all_healthy"] = False
        logger.error("Chroma database health check failed", error=str(e))
    
    # Check Neo4j health
    try:
        graph_service = await get_graph_service()
        neo4j_health = await graph_service.get_health_status()
        health_status["neo4j"] = neo4j_health
        
        if neo4j_health["status"] != "healthy":
            health_status["all_healthy"] = False
            
        logger.info("Neo4j database health check completed")
    except Exception as e:
        health_status["neo4j"]["status"] = "unhealthy"
        health_status["neo4j"]["error"] = str(e)
        health_status["all_healthy"] = False
        logger.error("Neo4j database health check failed", error=str(e))
    
    return health_status


async def get_chroma_client():
    """Get Chroma client for Phase 2"""
    from app.services.vector_service import get_vector_service
    vector_service = await get_vector_service()
    return vector_service.client


async def get_neo4j_driver():
    """Get Neo4j driver for Phase 2"""
    from app.services.graph_service import get_graph_service
    graph_service = await get_graph_service()
    return graph_service.driver 