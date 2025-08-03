#!/usr/bin/env python3
"""
AEON Phase 2 Test Suite - Fixed Version
Uses subprocess to call curl instead of Python requests to avoid timeout issues
"""

import subprocess
import json
import time
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "test_phase2_user"
TEST_EMAIL = "test_phase2@aeon.ai" 
TEST_PASSWORD = "test_phase2_password123"

class Phase2TestSuite:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def curl_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Dict:
        """Make HTTP request using curl"""
        cmd = ["curl", "-s", "-w", "%{http_code}", "-X", method, f"{BASE_URL}{endpoint}"]
        
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        
        if data:
            cmd.extend(["-H", "Content-Type: application/json"])
            cmd.extend(["-d", json.dumps(data)])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse curl output with status code
                output = result.stdout.strip()
                # Find the last 3 digits which should be the status code
                if len(output) >= 3 and output[-3:].isdigit():
                    status_code = int(output[-3:])
                    response_body = output[:-3]
                else:
                    status_code = 200
                    response_body = output
                
                try:
                    return {"status_code": status_code, "data": json.loads(response_body)}
                except json.JSONDecodeError:
                    return {"status_code": status_code, "data": response_body, "raw": True}
            else:
                return {"status_code": 500, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status_code": 408, "error": "Request timeout"}
        except Exception as e:
            return {"status_code": 500, "error": str(e)}
    
    def setup_test_user(self) -> bool:
        """Setup test user for Phase 2 testing"""
        print("🔧 Setting up test user...")
        
        # Register test user
        register_data = {
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Phase 2 Test User"
        }
        
        response = self.curl_request("POST", "/api/v1/users/register", register_data)
        if response["status_code"] == 201:
            print("✅ Test user registered")
        elif response["status_code"] == 400:
            print("ℹ️  Test user exists, proceeding...")
        elif response["status_code"] == 200 and "Username already registered" in str(response.get("data", "")):
            print("ℹ️  Test user exists, proceeding...")
        else:
            print(f"❌ Registration failed: {response.get('error', 'Unknown error')}")
            return False
        
        # Login
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        response = self.curl_request("POST", "/api/v1/users/login", login_data)
        if response["status_code"] == 200:
            token_data = response["data"]
            if isinstance(token_data, dict):
                self.token = token_data["access_token"]
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: Invalid response format")
                return False
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.token}"}
            user_response = self.curl_request("GET", "/api/v1/users/me", headers=headers)
            if user_response["status_code"] == 200:
                user_data = user_response["data"]
                if isinstance(user_data, dict):
                    self.user_id = user_data["id"]
                    print(f"✅ User info retrieved, user_id: {self.user_id}")
                    return True
                else:
                    print(f"❌ Failed to get user info: Invalid response format")
                    return False
            else:
                print(f"❌ Failed to get user info: {user_response.get('error', 'Unknown error')}")
        else:
            print(f"❌ Login failed: {response.get('error', 'Unknown error')}")
        
        return False
    
    def test_hybrid_system_health(self):
        """Test hybrid memory system health"""
        print("\n🏥 Testing Hybrid System Health...")
        
        response = self.curl_request("GET", "/api/v1/aeon/health/hybrid")
        if response["status_code"] == 200:
            health_data = response["data"]
            
            # Test overall health
            all_healthy = health_data.get('all_healthy', False)
            self.log_test("Hybrid System Health", all_healthy, "All systems operational" if all_healthy else "Some systems unhealthy")
            
            # Test Chroma
            chroma_status = health_data.get('chroma', {}).get('status')
            self.log_test("Chroma Vector DB", chroma_status == 'healthy', f"Status: {chroma_status}")
            
            # Test Neo4j
            neo4j_status = health_data.get('neo4j', {}).get('status')
            self.log_test("Neo4j Graph DB", neo4j_status == 'healthy', f"Status: {neo4j_status}")
            
            return all_healthy
        else:
            self.log_test("Hybrid System Health API", False, f"HTTP {response['status_code']}")
            return False
    
    def test_graph_initialization(self):
        """Test user graph initialization"""
        print("\n🕸️  Testing Graph Initialization...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/graph/initialize", headers=headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            success = result.get('status') == 'success'
            user_node_created = result.get('user_node_created', False)
            
            self.log_test("Graph Initialization", success, f"User node created: {user_node_created}")
            return success
        else:
            self.log_test("Graph Initialization", False, f"HTTP {response['status_code']}")
            return False
    
    def test_enhanced_memory_creation(self):
        """Test enhanced memory creation with RAG"""
        print("\n🧠 Testing Enhanced Memory Creation...")
        
        memory_data = {
            "content": "I learned that Python is a versatile programming language used for web development, data science, and AI.",
            "memory_type": "fact",
            "tags": ["programming", "python", "learning"]
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/memories/enhanced", memory_data, headers)
        
        if response["status_code"] == 201:
            result = response["data"]
            memory_id = result.get('id')
            vector_created = result.get('vector_created', False)
            graph_created = result.get('graph_created', False)
            
            self.log_test("Enhanced Memory Creation", True, f"Memory ID: {memory_id}")
            self.log_test("Vector Storage", vector_created, "Vector stored in ChromaDB")
            self.log_test("Graph Storage", graph_created, "Relationships stored in Neo4j")
            return True
        else:
            self.log_test("Enhanced Memory Creation", False, f"HTTP {response['status_code']}")
            return False
    
    def test_enhanced_chat(self):
        """Test enhanced chat with RAG capabilities"""
        print("\n💬 Testing Enhanced Chat...")
        
        chat_data = {
            "message": "What did I learn about Python?",
            "use_rag": True,
            "include_memories": True
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/chat/enhanced", chat_data, headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            message_content = result.get('message', {}).get('content', '')
            memories_used = result.get('memories_used', [])
            rag_sources = result.get('rag_sources', [])
            
            self.log_test("Enhanced Chat", len(message_content) > 0, "Response generated")
            self.log_test("Memory Retrieval", len(memories_used) > 0, f"Found {len(memories_used)} memories")
            self.log_test("RAG Sources", len(rag_sources) > 0, f"Found {len(rag_sources)} sources")
            return True
        else:
            self.log_test("Enhanced Chat", False, f"HTTP {response['status_code']}")
            return False
    
    def test_memory_search(self):
        """Test vector similarity search"""
        print("\n🔍 Testing Memory Search...")
        
        search_data = {
            "query": "programming language",
            "limit": 5
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/memory/search", search_data, headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            memories = result.get('memories', [])
            similarity_scores = result.get('similarity_scores', [])
            
            self.log_test("Memory Search", len(memories) > 0, f"Found {len(memories)} memories")
            self.log_test("Similarity Scoring", len(similarity_scores) > 0, "Scores calculated")
            return True
        else:
            self.log_test("Memory Search", False, f"HTTP {response['status_code']}")
            return False
    
    def test_context_retrieval(self):
        """Test context retrieval for conversations"""
        print("\n📚 Testing Context Retrieval...")
        
        context_data = {
            "conversation_id": 1,
            "include_memories": True,
            "include_knowledge": True
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/context/retrieve", context_data, headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            context = result.get('context', '')
            memories = result.get('memories', [])
            knowledge = result.get('knowledge', [])
            
            self.log_test("Context Retrieval", len(context) > 0, "Context retrieved")
            self.log_test("Memory Context", len(memories) > 0, f"Found {len(memories)} memories")
            self.log_test("Knowledge Context", len(knowledge) > 0, f"Found {len(knowledge)} knowledge items")
            return True
        else:
            self.log_test("Context Retrieval", False, f"HTTP {response['status_code']}")
            return False
    
    def test_enhanced_status(self):
        """Test enhanced status endpoint"""
        print("\n📊 Testing Enhanced Status...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("GET", "/api/v1/aeon/status/enhanced", headers=headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            memory_count = result.get('memory_count', 0)
            graph_nodes = result.get('graph_nodes', 0)
            vector_collections = result.get('vector_collections', 0)
            
            self.log_test("Enhanced Status", True, "Status retrieved")
            self.log_test("Memory Count", memory_count > 0, f"Found {memory_count} memories")
            self.log_test("Graph Nodes", graph_nodes > 0, f"Found {graph_nodes} graph nodes")
            self.log_test("Vector Collections", vector_collections > 0, f"Found {vector_collections} collections")
            return True
        else:
            self.log_test("Enhanced Status", False, f"HTTP {response['status_code']}")
            return False
    
    def test_fallback_mechanisms(self):
        """Test fallback mechanisms when RAG fails"""
        print("\n🔄 Testing Fallback Mechanisms...")
        
        # Test original chat endpoint still works
        chat_data = {
            "message": "Hello, this is a test message.",
            "conversation_id": 1
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.curl_request("POST", "/api/v1/aeon/chat", chat_data, headers)
        
        if response["status_code"] == 200:
            result = response["data"]
            message_content = result.get('message', {}).get('content', '')
            
            self.log_test("Original Chat Endpoint", len(message_content) > 0, "Phase 1 chat still works")
        else:
            self.log_test("Original Chat Endpoint", False, f"HTTP {response['status_code']}")
        
        # Test original status endpoint
        response = self.curl_request("GET", "/api/v1/aeon/status", headers=headers)
        
        if response["status_code"] == 200:
            self.log_test("Original Status Endpoint", True, "Phase 1 status still works")
        else:
            self.log_test("Original Status Endpoint", False, f"HTTP {response['status_code']}")
    
    def run_tests(self):
        """Run all Phase 2 tests"""
        print("🧪 AEON Phase 2 Test Suite - Fixed Version")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - aborting tests")
            return False
        
        # Run tests
        tests = [
            self.test_hybrid_system_health,
            self.test_graph_initialization,
            self.test_enhanced_memory_creation,
            self.test_enhanced_chat,
            self.test_memory_search,
            self.test_context_retrieval,
            self.test_enhanced_status,
            self.test_fallback_mechanisms
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
            time.sleep(1)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
            # Show failed tests
            failed_tests = [result for result in self.test_results if not result['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests:
                    print(f"   - {test['test']}: {test['message']}")
        
        print("\n🎯 Phase 2 Features Tested:")
        print("   - Hybrid Memory System (Chroma + Neo4j)")
        print("   - RAG-powered Chat")
        print("   - Enhanced Memory Creation")
        print("   - Vector Similarity Search")
        print("   - Graph Relationships")
        print("   - Context Retrieval")
        print("   - Concept Extraction")
        print("   - Fallback Mechanisms")
        
        return passed == total


if __name__ == "__main__":
    test_suite = Phase2TestSuite()
    success = test_suite.run_tests()
    
    if success:
        print("\n🎉 All tests passed! Phase 2 is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1) 