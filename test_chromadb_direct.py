#!/usr/bin/env python3
"""
Direct ChromaDB connection test
"""

import chromadb
import requests

def test_chromadb_direct():
    """Test ChromaDB connection directly"""
    print("🔗 Testing ChromaDB direct connection...")
    
    # First test if the server is responding
    try:
        response = requests.get("http://localhost:8001/api/v1/heartbeat", timeout=5)
        print(f"✅ ChromaDB server responding: {response.status_code}")
    except Exception as e:
        print(f"❌ ChromaDB server not responding: {str(e)}")
        return False
    
    try:
        # Try with persistent client
        client = chromadb.PersistentClient(path="/tmp/chroma_test")
        print("✅ ChromaDB persistent client created")
        
        # Test basic operations
        collections = client.list_collections()
        print(f"✅ Found {len(collections)} collections")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB persistent client failed: {str(e)}")
        
        try:
            # Try with HTTP client and different settings
            client = chromadb.HttpClient(
                host="localhost",
                port=8001,
                ssl=False
            )
            print("✅ ChromaDB HTTP client created")
            
            collections = client.list_collections()
            print(f"✅ Found {len(collections)} collections")
            
            return True
            
        except Exception as e2:
            print(f"❌ ChromaDB HTTP client also failed: {str(e2)}")
            return False

if __name__ == "__main__":
    success = test_chromadb_direct()
    exit(0 if success else 1) 