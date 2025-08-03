#!/usr/bin/env python3
"""
Test database services
"""

import asyncio
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService

async def test_database_services():
    """Test both database services"""
    print("🔗 Testing Database Services...")
    
    # Test Neo4j
    try:
        graph_service = GraphService()
        await graph_service.initialize()
        print("✅ Neo4j service initialized successfully")
        await graph_service.close()
    except Exception as e:
        print(f"❌ Neo4j service failed: {str(e)}")
        return False
    
    # Test ChromaDB
    try:
        vector_service = VectorService()
        await vector_service.initialize()
        print("✅ ChromaDB service initialized successfully")
        await vector_service.close()
    except Exception as e:
        print(f"❌ ChromaDB service failed: {str(e)}")
        return False
    
    print("🎉 All database services working!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_database_services())
    exit(0 if success else 1) 