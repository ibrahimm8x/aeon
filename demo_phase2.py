#!/usr/bin/env python3
"""
AEON Phase 2 Demo Script
Demonstrates hybrid memory system and RAG capabilities
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "demo_user"
EMAIL = "demo@aeon.ai"
PASSWORD = "demo_password123"

class AEONPhase2Demo:
    def __init__(self):
        self.token = None
        self.user_id = None
        
    def register_and_login(self) -> bool:
        """Register and login the demo user"""
        print("🔐 Setting up demo user...")
        
        # Try to register
        register_data = {
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "AEON Demo User"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/users/register", json=register_data)
            if response.status_code == 201:
                print("✅ User registered successfully")
            elif response.status_code == 400 and "already registered" in response.text:
                print("ℹ️  User already exists, proceeding to login")
        except Exception as e:
            print(f"Registration failed: {e}")
        
        # Login
        login_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/users/login", data=login_data)
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
        except Exception as e:
            print(f"Login failed: {e}")
        
        return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authorization token"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def check_hybrid_system_health(self):
        """Check the health of the hybrid memory system"""
        print("\n🏥 Checking Hybrid Memory System Health...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/aeon/health/hybrid")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Hybrid system health check passed")
                
                print(f"📊 Chroma (Vector DB): {health_data['chroma']['status']}")
                if health_data['chroma']['status'] == 'healthy':
                    print(f"   - Collections: {health_data['chroma'].get('collections', 0)}")
                    print(f"   - Memories: {health_data['chroma'].get('memory_count', 0)}")
                
                print(f"📊 Neo4j (Graph DB): {health_data['neo4j']['status']}")
                if health_data['neo4j']['status'] == 'healthy':
                    print(f"   - Total nodes: {health_data['neo4j'].get('total_nodes', 0)}")
                
                return health_data['all_healthy']
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def initialize_user_graph(self):
        """Initialize the user in the graph database"""
        print("\n🕸️  Initializing User Graph...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/aeon/graph/initialize",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ User graph initialized successfully")
                print(f"   - User node created: {result.get('user_node_created', False)}")
                print(f"   - Conversations migrated: {result.get('conversations_migrated', 0)}")
                return True
            else:
                print(f"❌ Graph initialization failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Graph initialization error: {e}")
            return False
    
    def create_sample_memories(self):
        """Create sample memories to demonstrate the system"""
        print("\n🧠 Creating Sample Memories...")
        
        sample_memories = [
            {
                "content": "I love Italian cuisine, especially pasta carbonara and tiramisu for dessert",
                "memory_type": "preference",
                "importance": 7,
                "metadata": {"category": "food", "cuisine": "italian"}
            },
            {
                "content": "I work as a software engineer at a tech startup in San Francisco",
                "memory_type": "personal_info",
                "importance": 9,
                "metadata": {"category": "career", "location": "san_francisco"}
            },
            {
                "content": "I enjoy hiking on weekends, especially in Marin County and Big Sur",
                "memory_type": "hobby",
                "importance": 6,
                "metadata": {"category": "outdoor_activities", "location": "california"}
            },
            {
                "content": "I'm learning Spanish and have been taking classes for 6 months",
                "memory_type": "goal",
                "importance": 8,
                "metadata": {"category": "education", "language": "spanish"}
            },
            {
                "content": "I prefer working in quiet environments and use noise-canceling headphones",
                "memory_type": "preference",
                "importance": 5,
                "metadata": {"category": "work_environment"}
            }
        ]
        
        created_memories = []
        for i, memory in enumerate(sample_memories):
            try:
                # Create enhanced memory (Phase 2)
                response = requests.post(
                    f"{BASE_URL}/api/v1/aeon/memories/enhanced",
                    json=memory,
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Memory {i+1} created (Vector ID: {result.get('vector_id', 'N/A')[:12]}...)")
                    print(f"   - Concepts extracted: {result.get('concepts_extracted', 0)}")
                    created_memories.append(result)
                else:
                    print(f"❌ Memory {i+1} creation failed: {response.status_code}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Memory {i+1} creation error: {e}")
        
        return created_memories
    
    def demonstrate_enhanced_chat(self):
        """Demonstrate enhanced chat with memory retrieval"""
        print("\n💬 Demonstrating Enhanced Chat with Memory Retrieval...")
        
        test_questions = [
            "What kind of food do I like?",
            "Where do I work?",
            "What do I do for fun on weekends?",
            "What am I learning right now?",
            "Tell me about my work preferences"
        ]
        
        for i, question in enumerate(test_questions):
            print(f"\n🤔 Question {i+1}: {question}")
            
            try:
                # Enhanced chat (Phase 2)
                chat_data = {
                    "message": question,
                    "conversation_id": None
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/aeon/chat/enhanced",
                    json=chat_data,
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"🤖 AEON: {result['message']['content']}")
                    
                    # Show context information if available
                    if hasattr(result, 'context_sources'):
                        print(f"📊 Context: {result.get('memories_referenced', 0)} memories referenced")
                else:
                    print(f"❌ Chat failed: {response.status_code}")
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Chat error: {e}")
    
    def demonstrate_memory_search(self):
        """Demonstrate enhanced memory search capabilities"""
        print("\n🔍 Demonstrating Enhanced Memory Search...")
        
        search_queries = [
            "food and cuisine",
            "work and career",
            "outdoor activities",
            "learning and education"
        ]
        
        for query in search_queries:
            print(f"\n🔎 Searching for: '{query}'")
            
            try:
                # Enhanced search (Phase 2)
                params = {
                    "query": query,
                    "enhanced": True,
                    "limit": 3
                }
                
                response = requests.get(
                    f"{BASE_URL}/api/v1/aeon/memories/search",
                    params=params,
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    rag_results = result.get('rag_results', {})
                    
                    print(f"📊 Found {rag_results.get('sources', {}).get('vector_memories', 0)} vector matches")
                    print(f"📊 Found {rag_results.get('sources', {}).get('graph_memories', 0)} graph relationships")
                    
                    # Show top results
                    for i, memory in enumerate(rag_results.get('memory_details', [])[:2]):
                        print(f"   {i+1}. {memory.get('content', '')[:80]}...")
                        print(f"      Relevance: {memory.get('relevance_score', 0):.2f}")
                else:
                    print(f"❌ Search failed: {response.status_code}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Search error: {e}")
    
    def demonstrate_context_retrieval(self):
        """Demonstrate direct context retrieval"""
        print("\n🧩 Demonstrating Context Retrieval...")
        
        queries = [
            "Tell me about Italian food",
            "What programming languages do you know?",
            "Outdoor activities in California"
        ]
        
        for query in queries:
            print(f"\n🎯 Context for: '{query}'")
            
            try:
                params = {
                    "query": query,
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
                    
                    print(f"📝 Context retrieved:")
                    context = result.get('context', '')
                    if context:
                        # Show first 200 characters of context
                        print(f"   {context[:200]}{'...' if len(context) > 200 else ''}")
                    else:
                        print("   No relevant context found")
                    
                    sources = result.get('sources', {})
                    print(f"📊 Sources: {sources}")
                else:
                    print(f"❌ Context retrieval failed: {response.status_code}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Context retrieval error: {e}")
    
    def get_enhanced_status(self):
        """Get enhanced status information"""
        print("\n📊 Getting Enhanced AEON Status...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/aeon/status/enhanced",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                status = response.json()
                
                print("✅ Enhanced status retrieved")
                
                # Basic status
                basic = status.get('basic_status', {})
                print(f"📈 Traditional memories: {basic.get('total_memories', 0)}")
                print(f"📈 Conversations: {basic.get('total_conversations', 0)}")
                
                # Hybrid memory status
                hybrid = status.get('hybrid_memory', {})
                vector_db = hybrid.get('vector_db', {})
                graph_db = hybrid.get('graph_db', {})
                
                print(f"🧠 Vector DB memories: {vector_db.get('memory_count', 0)}")
                print(f"🕸️  Graph DB nodes: {graph_db.get('total_nodes', 0)}")
                
                # Knowledge graph summary
                kg = graph_db.get('knowledge_graph', {})
                print(f"🎓 Concepts learned: {kg.get('concept_count', 0)}")
                
                # Capabilities
                capabilities = status.get('capabilities', {})
                print(f"⚡ RAG enabled: {capabilities.get('rag_enabled', False)}")
                print(f"⚡ Hybrid memory: {capabilities.get('hybrid_memory', False)}")
                
            else:
                print(f"❌ Status retrieval failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Status error: {e}")
    
    def run_demo(self):
        """Run the complete Phase 2 demo"""
        print("🎭 AEON Phase 2 Demo - Hybrid Memory & RAG System")
        print("=" * 60)
        
        # Setup
        if not self.register_and_login():
            print("❌ Failed to setup demo user")
            return
        
        # Check system health
        if not self.check_hybrid_system_health():
            print("⚠️  Hybrid system health issues detected, but continuing...")
        
        # Initialize user graph
        self.initialize_user_graph()
        
        # Create sample memories
        memories = self.create_sample_memories()
        if not memories:
            print("⚠️  No memories created, some demos may not work properly")
        
        # Wait for indexing
        print("\n⏳ Waiting for memory indexing...")
        time.sleep(5)
        
        # Demonstrate features
        self.demonstrate_enhanced_chat()
        self.demonstrate_memory_search()
        self.demonstrate_context_retrieval()
        self.get_enhanced_status()
        
        print("\n🎉 AEON Phase 2 Demo Complete!")
        print("\nKey features demonstrated:")
        print("✅ Hybrid Memory System (Vector + Graph)")
        print("✅ RAG-powered Chat Responses")
        print("✅ Intelligent Memory Search")
        print("✅ Context Retrieval")
        print("✅ Concept Extraction and Relationships")
        print("\n📚 Try the API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    demo = AEONPhase2Demo()
    demo.run_demo() 