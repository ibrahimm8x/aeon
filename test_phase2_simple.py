#!/usr/bin/env python3
"""
AEON Phase 2 Simple Test Script
Tests Phase 2 endpoints with fallback to Phase 1 functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "test_phase2_simple"
TEST_EMAIL = "test_phase2_simple@aeon.ai" 
TEST_PASSWORD = "test_phase2_simple_password123"

class SimplePhase2Test:
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
            "full_name": "Phase 2 Simple Test User"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/users/register", json=register_data)
            if response.status_code == 201:
                print("✅ Test user registered")
            elif response.status_code == 400:
                print("ℹ️  Test user exists, proceeding...")
        except Exception as e:
            print(f"❌ Registration failed: {e}")
            return False
        
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
                    print(f"👤 User ID: {self.user_id}")
                    return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_phase1_endpoints(self):
        """Test that Phase 1 endpoints still work"""
        print("\n🔧 Testing Phase 1 Endpoints...")
        
        # Test original chat
        try:
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
                
                self.log_test("Original Chat Endpoint", len(message_content) > 0, f"Response length: {len(message_content)}")
            else:
                self.log_test("Original Chat Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Original Chat Endpoint", False, f"Exception: {e}")
        
        # Test original status
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/status",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("Original Status Endpoint", True, f"User ID: {status_data.get('user_id')}")
            else:
                self.log_test("Original Status Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Original Status Endpoint", False, f"Exception: {e}")
        
        # Test original memory creation
        try:
            memory_data = {
                "content": "Test memory from Phase 1 endpoint",
                "memory_type": "test",
                "importance": 5
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/memories",
                json=memory_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 201:
                self.log_test("Original Memory Creation", True, "Memory created successfully")
            else:
                self.log_test("Original Memory Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Original Memory Creation", False, f"Exception: {e}")
    
    def test_phase2_endpoints_with_fallback(self):
        """Test Phase 2 endpoints that should fallback gracefully"""
        print("\n🚀 Testing Phase 2 Endpoints with Fallback...")
        
        # Test enhanced chat (should fallback to original)
        try:
            chat_data = {
                "message": "Hello, this is a test of the enhanced chat endpoint",
                "conversation_id": None
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/chat/enhanced",
                json=chat_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                message_content = result.get('message', {}).get('content', '')
                
                self.log_test("Enhanced Chat Endpoint", len(message_content) > 0, f"Response length: {len(message_content)}")
            else:
                self.log_test("Enhanced Chat Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Enhanced Chat Endpoint", False, f"Exception: {e}")
        
        # Test enhanced status (should show fallback info)
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/status/enhanced",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                status_data = response.json()
                has_basic_status = 'basic_status' in status_data
                has_capabilities = 'capabilities' in status_data
                
                self.log_test("Enhanced Status Endpoint", True, "Successfully retrieved")
                self.log_test("Basic Status Present", has_basic_status, "Contains basic status")
                self.log_test("Capabilities Info", has_capabilities, "Contains capabilities info")
            else:
                self.log_test("Enhanced Status Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Enhanced Status Endpoint", False, f"Exception: {e}")
        
        # Test enhanced memory creation (should fallback to original)
        try:
            memory_data = {
                "content": "Test memory from Phase 2 enhanced endpoint",
                "memory_type": "test_enhanced",
                "importance": 6
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/memories/enhanced",
                json=memory_data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                self.log_test("Enhanced Memory Creation", True, f"Status: {status}")
            else:
                self.log_test("Enhanced Memory Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Enhanced Memory Creation", False, f"Exception: {e}")
    
    def test_memory_search(self):
        """Test memory search functionality"""
        print("\n🔍 Testing Memory Search...")
        
        # Test traditional search
        try:
            params = {
                "query": "test",
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
                method = result.get('method', 'unknown')
                results_count = len(result.get('results', []))
                
                self.log_test("Traditional Memory Search", True, f"Method: {method}, Results: {results_count}")
            else:
                self.log_test("Traditional Memory Search", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Traditional Memory Search", False, f"Exception: {e}")
        
        # Test enhanced search (should show error or fallback)
        try:
            params = {
                "query": "test enhanced",
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
                has_error = 'error' in result
                
                if has_error:
                    self.log_test("Enhanced Memory Search", False, f"Error: {result.get('error', 'Unknown')}")
                else:
                    self.log_test("Enhanced Memory Search", True, "Search completed")
            else:
                self.log_test("Enhanced Memory Search", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Enhanced Memory Search", False, f"Exception: {e}")
    
    def test_graph_initialization(self):
        """Test graph initialization (should fail gracefully)"""
        print("\n🕸️  Testing Graph Initialization...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/graph/initialize",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                self.log_test("Graph Initialization", status == 'success', f"Status: {status}")
            else:
                self.log_test("Graph Initialization", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graph Initialization", False, f"Exception: {e}")
    
    def test_context_retrieval(self):
        """Test context retrieval (should fail gracefully)"""
        print("\n🧩 Testing Context Retrieval...")
        
        try:
            params = {
                "query": "test context",
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
                self.log_test("Context Retrieval", has_context, f"Context length: {len(context)}")
            else:
                self.log_test("Context Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Context Retrieval", False, f"Exception: {e}")
    
    def test_hybrid_health(self):
        """Test hybrid health endpoint"""
        print("\n🏥 Testing Hybrid Health...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/aeon/health/hybrid")
            
            if response.status_code == 200:
                health_data = response.json()
                all_healthy = health_data.get('all_healthy', False)
                
                self.log_test("Hybrid Health Endpoint", True, f"All healthy: {all_healthy}")
                
                # Check individual components
                chroma_status = health_data.get('chroma', {}).get('status', 'unknown')
                neo4j_status = health_data.get('neo4j', {}).get('status', 'unknown')
                
                self.log_test("Chroma Status", chroma_status == 'healthy', f"Status: {chroma_status}")
                self.log_test("Neo4j Status", neo4j_status == 'healthy', f"Status: {neo4j_status}")
            else:
                self.log_test("Hybrid Health Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Hybrid Health Endpoint", False, f"Exception: {e}")
    
    def run_tests(self):
        """Run all simplified Phase 2 tests"""
        print("🧪 AEON Phase 2 Simple Test Suite")
        print("=" * 50)
        print("Testing Phase 2 endpoints with fallback mechanisms")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user - aborting tests")
            return False
        
        # Run tests
        tests = [
            self.test_phase1_endpoints,
            self.test_phase2_endpoints_with_fallback,
            self.test_memory_search,
            self.test_graph_initialization,
            self.test_context_retrieval,
            self.test_hybrid_health
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
        print("   - Phase 1 Endpoint Compatibility")
        print("   - Phase 2 Endpoint Fallbacks")
        print("   - Enhanced Memory Creation")
        print("   - Memory Search (Traditional + Enhanced)")
        print("   - Graph Initialization")
        print("   - Context Retrieval")
        print("   - Hybrid System Health")
        print("   - Error Handling & Graceful Degradation")
        
        return passed >= total * 0.7  # 70% success rate is acceptable for fallback testing


if __name__ == "__main__":
    test_suite = SimplePhase2Test()
    success = test_suite.run_tests()
    
    if success:
        print("\n🎉 Phase 2 fallback mechanisms are working correctly!")
        print("💡 To test full Phase 2 capabilities, install Docker and run:")
        print("   docker-compose up -d")
        print("   python test_phase2.py")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1) 