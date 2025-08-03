#!/usr/bin/env python3
"""
Direct Neo4j connection test
"""

from neo4j import GraphDatabase

def test_direct_connection():
    """Test direct Neo4j connection"""
    uri = "neo4j+s://0c66b9bf.databases.neo4j.io"
    user = "neo4j"
    password = "y0GFVhFzmiDKDFGvqLIXYImDpbo79VfC7Jai-t9I04Y"
    
    print(f"🔗 Testing direct Neo4j connection to: {uri}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test the connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record["test"] == 1:
                print("✅ Direct Neo4j connection successful!")
                driver.close()
                return True
            else:
                print("❌ Connection test failed")
                driver.close()
                return False
                
    except Exception as e:
        print(f"❌ Direct Neo4j connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_direct_connection()
    exit(0 if success else 1) 