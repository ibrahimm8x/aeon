#!/usr/bin/env python3
"""
AEON Phase 2 Test Script
Tests hybrid memory system and RAG capabilities
"""

import asyncio
import requests
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
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/users/register", json=register_data)
            if response.status_code == 201:
                print("✅ Test user registered")
            elif response.status_code == 400:
                print("ℹ️  Test user exists, proceeding...")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
        
        # Login
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/users/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                print("✅ Login successful")
                
                # Get user info
                headers = {"Authorization": f"Bearer {self.token}"}
                user_response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.user_id = user_data["id"]
                    print(f"✅ User info retrieved, user_id: {self.user_id}")
                    return True
                else:
                    print(f"❌ Failed to get user info: HTTP {user_response.status_code}")
            else:
                print(f"❌ Login failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Login failed: {e}")
        
        return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_hybrid_system_health(self):
        """Test hybrid memory system health"""
        print("\n🏥 Testing Hybrid System Health...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/aeon/health/hybrid")
            if response.status_code == 200:
                health_data = response.json()
                
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
                self.log_test("Hybrid System Health API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Hybrid System Health", False, f"Exception: {e}")
            return False
    
    def test_graph_initialization(self):
        """Test user graph initialization"""
        print("\n🕸️  Testing Graph Initialization...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/graph/initialize",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('status') == 'success'
                user_node_created = result.get('user_node_created', False)
                
                self.log_test("Graph Initialization", success, f"User node created: {user_node_created}")
                return success
            else:
                self.log_test("Graph Initialization", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Graph Initialization", False, f"Exception: {e}")
            return False
    
    def test_enhanced_memory_creation(self):
        """Test enhanced memory creation with vector and graph storage"""
        print("\n🧠 Testing Enhanced Memory Creation...")
        
        test_memory = {
            "content": "Test memory: I enjoy reading science fiction novels, especially works by Isaac Asimov",
            "memory_type": "preference",
            "importance": 7,
            "metadata": {"category": "books", "genre": "science_fiction", "author": "asimov"}
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/memories/enhanced",
                json=test_memory,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('status') == 'success'
                vector_id = result.get('vector_id')
                concepts_extracted = result.get('concepts_extracted', 0)
                
                self.log_test("Enhanced Memory Creation", success, f"Vector ID: {vector_id[:12] if vector_id else 'None'}...")
                self.log_test("Concept Extraction", concepts_extracted > 0, f"Extracted {concepts_extracted} concepts")
                
                return success and vector_id is not None
            else:
                self.log_test("Enhanced Memory Creation", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Memory Creation", False, f"Exception: {e}")
            return False
    
    def test_enhanced_chat(self):
        """Test enhanced chat with RAG capabilities"""
        print("\n💬 Testing Enhanced Chat...")
        
        # First create a memory to retrieve
        setup_memory = {
            "content": "I love playing guitar and have been learning for 3 years",
            "memory_type": "hobby",
            "importance": 8,
            "metadata": {"category": "music", "instrument": "guitar"}
        }
        
        requests.post(
            f"{BASE_URL}/api/v1/aeon/memories/enhanced",
            json=setup_memory,
            headers=self.get_headers()
        )
        
        time.sleep(2)  # Allow indexing
        
        # Test enhanced chat
        chat_data = {
            "message": "What musical instruments do I play?",
            "conversation_id": None
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/chat/enhanced",
                json=chat_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                message_content = result.get('message', {}).get('content', '')
                
                # Check if the response mentions guitar
                contains_guitar = 'guitar' in message_content.lower()
                
                self.log_test("Enhanced Chat Response", len(message_content) > 0, f"Response length: {len(message_content)}")
                self.log_test("Memory Retrieval in Chat", contains_guitar, "Response contains retrieved memory about guitar")
                
                return len(message_content) > 0
            else:
                self.log_test("Enhanced Chat", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Chat", False, f"Exception: {e}")
            return False
    
    def test_memory_search(self):
        """Test enhanced memory search capabilities"""
        print("\n🔍 Testing Memory Search...")
        
        # Create searchable memories
        test_memories = [
            {
                "content": "I work remotely as a Python developer",
                "memory_type": "work",
                "importance": 9,
                "metadata": {"skill": "python", "work_style": "remote"}
            },
            {
                "content": "My favorite programming language is Python for its simplicity",
                "memory_type": "preference", 
                "importance": 7,
                "metadata": {"skill": "python", "category": "programming"}
            }
        ]
        
        for memory in test_memories:
            requests.post(
                f"{BASE_URL}/api/v1/aeon/memories/enhanced",
                json=memory,
                headers=self.get_headers()
            )
        
        time.sleep(3)  # Allow indexing
        
        # Test traditional search
        try:
            params = {
                "query": "python programming",
                "enhanced": False,
                "limit": 5
            }
            
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/memories/search",
                params=params,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                traditional_results = len(result.get('results', []))
                self.log_test("Traditional Memory Search", traditional_results > 0, f"Found {traditional_results} results")
            else:
                self.log_test("Traditional Memory Search", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Traditional Memory Search", False, f"Exception: {e}")
        
        # Test enhanced search
        try:
            params = {
                "query": "python programming development",
                "enhanced": True,
                "limit": 5
            }
            
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/memories/search",
                params=params,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                rag_results = result.get('rag_results', {})
                vector_memories = rag_results.get('sources', {}).get('vector_memories', 0)
                
                self.log_test("Enhanced Memory Search", vector_memories > 0, f"Found {vector_memories} vector matches")
                return vector_memories > 0
            else:
                self.log_test("Enhanced Memory Search", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Memory Search", False, f"Exception: {e}")
            return False
    
    def test_context_retrieval(self):
        """Test direct context retrieval"""
        print("\n🧩 Testing Context Retrieval...")
        
        try:
            params = {
                "query": "programming and development skills",
                "max_memories": 3,
                "include_graph": True
            }
            
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/context/retrieve",
                params=params,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                context = result.get('context', '')
                sources = result.get('sources', {})
                
                has_context = len(context) > 0
                has_sources = sum(sources.values()) > 0
                
                self.log_test("Context Retrieval", has_context, f"Context length: {len(context)}")
                self.log_test("Context Sources", has_sources, f"Sources: {sources}")
                
                return has_context
            else:
                self.log_test("Context Retrieval", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Context Retrieval", False, f"Exception: {e}")
            return False
    
    def test_enhanced_status(self):
        """Test enhanced status endpoint"""
        print("\n📊 Testing Enhanced Status...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/status/enhanced",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                status = response.json()
                
                has_basic_status = 'basic_status' in status
                has_hybrid_memory = 'hybrid_memory' in status
                has_capabilities = 'capabilities' in status
                rag_enabled = status.get('capabilities', {}).get('rag_enabled', False)
                
                self.log_test("Enhanced Status Endpoint", True, "Successfully retrieved")
                self.log_test("Basic Status Present", has_basic_status, "Contains basic status")
                self.log_test("Hybrid Memory Status", has_hybrid_memory, "Contains hybrid memory info")
                self.log_test("RAG Capabilities", rag_enabled, f"RAG enabled: {rag_enabled}")
                
                return True
            else:
                self.log_test("Enhanced Status", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Enhanced Status", False, f"Exception: {e}")
            return False
    
    def test_fallback_mechanisms(self):
        """Test fallback to Phase 1 when Phase 2 fails"""
        print("\n🔄 Testing Fallback Mechanisms...")
        
        # Test that original endpoints still work
        try:
            # Original chat endpoint
            chat_data = {
                "message": "Hello, this is a test of the original chat endpoint",
                "conversation_id": None
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/chat",
                json=chat_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                message_content = result.get('message', {}).get('content', '')
                
                self.log_test("Original Chat Endpoint", len(message_content) > 0, "Phase 1 chat still works")
            else:
                self.log_test("Original Chat Endpoint", False, f"HTTP {response.status_code}")
            
            # Original status endpoint
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/status",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                self.log_test("Original Status Endpoint", True, "Phase 1 status still works")
            else:
                self.log_test("Original Status Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Fallback Mechanisms", False, f"Exception: {e}")
    
    def run_tests(self):
        """Run all Phase 2 tests"""
        print("🧪 AEON Phase 2 Test Suite")
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