#!/usr/bin/env python3
"""
Local Neo4j connection test
"""

from neo4j import GraphDatabase

def test_local_connection():
    """Test local Neo4j connection"""
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "aeon123456"  # Default password from docker-compose
    
    print(f"🔗 Testing local Neo4j connection to: {uri}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test the connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record["test"] == 1:
                print("✅ Local Neo4j connection successful!")
                driver.close()
                return True
            else:
                print("❌ Connection test failed")
                driver.close()
                return False
                
    except Exception as e:
        print(f"❌ Local Neo4j connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_local_connection()
    exit(0 if success else 1) 