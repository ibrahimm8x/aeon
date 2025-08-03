#!/usr/bin/env python3
"""
Test ChromaDB connection
"""

import chromadb
from app.core.config import settings

def test_chromadb_connection():
    """Test ChromaDB connection"""
    print("🔗 Testing ChromaDB connection...")
    print(f"ChromaDB Host: {settings.chroma_host}")
    print(f"ChromaDB Port: {settings.chroma_port}")
    
    try:
        # Create ChromaDB client
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        
        # Test the connection by listing collections
        collections = client.list_collections()
        print(f"✅ ChromaDB connection successful! Found {len(collections)} collections")
        
        # Test creating a test collection
        test_collection = client.create_collection(
            name="test_connection",
            metadata={"description": "Test collection for connection verification"}
        )
        print("✅ Test collection created successfully")
        
        # Clean up - delete the test collection
        client.delete_collection(name="test_connection")
        print("✅ Test collection cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chromadb_connection()
    exit(0 if success else 1) 