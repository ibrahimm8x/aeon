#!/usr/bin/env python3
"""
Test database connections for Phase 2
"""

import asyncio
import requests
from app.services.vector_service import get_vector_service
from app.services.graph_service import get_graph_service

async def test_connections():
    print("🔍 Testing Database Connections...")
    
    # Test ChromaDB
    try:
        print("Testing ChromaDB connection...")
        vector_service = await get_vector_service()
        health = await vector_service.get_health_status()
        print(f"✅ ChromaDB: {health}")
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")
    
    # Test Neo4j
    try:
        print("Testing Neo4j connection...")
        graph_service = await get_graph_service()
        health = await graph_service.get_health_status()
        print(f"✅ Neo4j: {health}")
    except Exception as e:
        print(f"❌ Neo4j Error: {e}")
    
    # Test API endpoints
    try:
        print("Testing API endpoints...")
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Basic Health: {response.status_code}")
        
        response = requests.get("http://localhost:8000/api/v1/aeon/health/hybrid")
        print(f"✅ Hybrid Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connections()) 