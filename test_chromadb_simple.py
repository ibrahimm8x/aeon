#!/usr/bin/env python3
"""
Simple ChromaDB connection test
"""

import chromadb

def test_chromadb_simple():
    """Test ChromaDB connection without tenant"""
    print("🔗 Testing ChromaDB connection...")
    
    try:
        # Create ChromaDB client without specifying tenant
        client = chromadb.HttpClient(
            host="localhost",
            port=8001
        )
        
        # Test the connection by listing collections
        collections = client.list_collections()
        print(f"✅ ChromaDB connection successful! Found {len(collections)} collections")
        
        # Test creating a simple collection
        test_collection = client.create_collection(
            name="test_collection_simple",
            metadata={"description": "Test collection"}
        )
        print("✅ Test collection created successfully")
        
        # Clean up - delete the test collection
        client.delete_collection("test_collection_simple")
        print("✅ Test collection cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chromadb_simple()
    exit(0 if success else 1) 