#!/usr/bin/env python3
"""
Test Neo4j connection
"""

import asyncio
from app.services.graph_service import GraphService
from app.core.config import settings

async def test_neo4j_connection():
    """Test Neo4j connection"""
    print("🔗 Testing Neo4j connection...")
    print(f"URI: {settings.neo4j_uri}")
    print(f"User: {settings.neo4j_user}")
    print(f"Password: {settings.neo4j_password[:3]}***")
    
    try:
        graph_service = GraphService()
        await graph_service.initialize()
        print("✅ Neo4j connection successful!")
        await graph_service.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_connection())
    exit(0 if success else 1) 