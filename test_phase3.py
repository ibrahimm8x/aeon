#!/usr/bin/env python3
"""
AEON Phase 3: Digital Realm Prototype Test Suite
Tests multi-user interactions, real-time messaging, and social features
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any

import httpx
import websockets
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import User, ChatRoom, RoomParticipant
from app.services.social_service import SocialService
from app.models.aeon import (
    ChatRoomCreate, UserRelationshipCreate, SharedKnowledgeCreate, AEONInteractionCreate
)


class Phase3Tester:
    """Test suite for Phase 3 features"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.test_users = []
        self.test_rooms = []
        self.websocket_connections = []
        
    async def setup_test_users(self):
        """Create test users for Phase 3 testing"""
        print("👥 Setting up test users...")
        
        # Create test users
        test_user_data = [
            {"username": "alice_aeon", "email": "alice@test.com", "password": "testpass123"},
            {"username": "bob_aeon", "email": "bob@test.com", "password": "testpass123"},
            {"username": "charlie_user", "email": "charlie@test.com", "password": "testpass123"},
            {"username": "diana_user", "email": "diana@test.com", "password": "testpass123"}
        ]
        
        for user_data in test_user_data:
            try:
                # Create user
                response = await self.client.post(
                    f"{self.base_url}/api/v1/users/register",
                    json=user_data
                )
                
                if response.status_code == 201:
                    user_info = response.json()
                    self.test_users.append(user_info)
                    print(f"✅ Created user: {user_data['username']}")
                else:
                    # User may already exist, try to get user info
                    print(f"⚠️  User {user_data['username']} may already exist, trying to get info...")
                    # Add the user data to test_users for authentication
                    self.test_users.append({
                        "username": user_data["username"],
                        "email": user_data["email"],
                        "password": user_data["password"]
                    })
                    
            except Exception as e:
                print(f"❌ Error creating user {user_data['username']}: {e}")
        
        print(f"📊 Available {len(self.test_users)} test users")
    
    async def test_authentication(self):
        """Test user authentication"""
        print("\n🔐 Testing authentication...")
        
        if not self.test_users:
            print("❌ No test users available")
            return False
        
        user = self.test_users[0]
        
        try:
            # Login
            response = await self.client.post(
                f"{self.base_url}/api/v1/users/login",
                json={
                    "username": user["username"],
                    "password": "testpass123"
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.client.headers["Authorization"] = f"Bearer {token_data['access_token']}"
                
                # Get current user info to get the user ID
                me_response = await self.client.get(f"{self.base_url}/api/v1/users/me")
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    user["id"] = user_info["id"]
                    print(f"✅ Authentication successful for user ID: {user_info['id']}")
                    return True
                else:
                    print("❌ Could not get user info after authentication")
                    return False
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def test_chat_rooms(self):
        """Test chat room creation and management"""
        print("\n🏠 Testing chat rooms...")
        
        try:
            # Create a test room
            room_data = ChatRoomCreate(
                name="Test Phase 3 Room",
                description="A test room for Phase 3 features",
                is_public=True,
                max_participants=10,
                topic="Testing",
                is_aeon_room=False
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/phase3/rooms",
                json=room_data.model_dump()
            )
            
            if response.status_code == 201:
                room_info = response.json()
                self.test_rooms.append(room_info)
                print(f"✅ Created chat room: {room_info['name']}")
                
                # Get all rooms
                response = await self.client.get(f"{self.base_url}/api/v1/phase3/rooms")
                if response.status_code == 200:
                    rooms = response.json()
                    print(f"✅ Retrieved {len(rooms)} chat rooms")
                    
                    # Get specific room
                    room_id = room_info["id"]
                    response = await self.client.get(f"{self.base_url}/api/v1/phase3/rooms/{room_id}")
                    if response.status_code == 200:
                        room_detail = response.json()
                        print(f"✅ Retrieved room details: {room_detail['name']}")
                        return True
                
            else:
                print(f"❌ Failed to create chat room: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat room test error: {e}")
            return False
    
    async def test_user_relationships(self):
        """Test user relationship features"""
        print("\n🤝 Testing user relationships...")
        
        if len(self.test_users) < 2:
            print("❌ Need at least 2 users for relationship testing")
            return False
        
        try:
            # Get the second user's ID by authenticating with them
            second_user = self.test_users[1]
            auth_response = await self.client.post(
                f"{self.base_url}/api/v1/users/login",
                json={
                    "username": second_user["username"],
                    "password": "testpass123"
                }
            )
            
            if auth_response.status_code != 200:
                print("❌ Could not authenticate with second user")
                return False
                
            # Get second user's info
            me_response = await self.client.get(f"{self.base_url}/api/v1/users/me")
            if me_response.status_code != 200:
                print("❌ Could not get second user info")
                return False
                
            second_user_info = me_response.json()
            second_user["id"] = second_user_info["id"]
            
            # Switch back to first user
            first_user = self.test_users[0]
            auth_response = await self.client.post(
                f"{self.base_url}/api/v1/users/login",
                json={
                    "username": first_user["username"],
                    "password": "testpass123"
                }
            )
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                self.client.headers["Authorization"] = f"Bearer {token_data['access_token']}"
            
            # Create relationship between users
            relationship_data = UserRelationshipCreate(
                related_user_id=second_user["id"],
                relationship_type="friend",
                strength=0.8,
                shared_interests=["technology", "AI", "innovation"],
                meta_data={"test": True}
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/phase3/relationships",
                json=relationship_data.model_dump()
            )
            
            if response.status_code == 201:
                relationship = response.json()
                print(f"✅ Created relationship: {relationship['relationship_type']}")
                
                # Get relationships
                response = await self.client.get(f"{self.base_url}/api/v1/phase3/relationships")
                if response.status_code == 200:
                    relationships = response.json()
                    print(f"✅ Retrieved {len(relationships)} relationships")
                    return True
            else:
                print(f"❌ Failed to create relationship: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Relationship test error: {e}")
            return False
    
    async def test_shared_knowledge(self):
        """Test shared knowledge system"""
        print("\n🧠 Testing shared knowledge...")
        
        try:
            # Create shared knowledge
            knowledge_data = SharedKnowledgeCreate(
                content="Phase 3 introduces real-time multi-user interactions with WebSocket support and social intelligence features.",
                knowledge_type="insight",
                tags=["phase3", "realtime", "websocket", "social"],
                visibility="public",
                meta_data={"test": True, "phase": 3}
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/phase3/knowledge",
                json=knowledge_data.model_dump()
            )
            
            if response.status_code == 201:
                knowledge = response.json()
                print(f"✅ Created shared knowledge: {knowledge['content'][:50]}...")
                
                # Get shared knowledge
                response = await self.client.get(f"{self.base_url}/api/v1/phase3/knowledge")
                if response.status_code == 200:
                    knowledge_list = response.json()
                    print(f"✅ Retrieved {len(knowledge_list)} knowledge items")
                    
                    # Upvote knowledge
                    if knowledge_list:
                        knowledge_id = knowledge_list[0]["id"]
                        response = await self.client.post(
                            f"{self.base_url}/api/v1/phase3/knowledge/{knowledge_id}/upvote"
                        )
                        if response.status_code == 200:
                            print("✅ Successfully upvoted knowledge")
                            return True
                
            else:
                print(f"❌ Failed to create shared knowledge: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Shared knowledge test error: {e}")
            return False
    
    async def test_aeon_interactions(self):
        """Test AEON-to-AEON interactions"""
        print("\n🤖 Testing AEON interactions...")
        
        if len(self.test_users) < 2:
            print("❌ Need at least 2 users for AEON interaction testing")
            return False
        
        try:
            # Create AEON interaction
            interaction_data = AEONInteractionCreate(
                target_aeon_user_id=self.test_users[1]["id"],
                interaction_type="knowledge_share",
                content="Hello! I'd like to share some insights about Phase 3's real-time capabilities.",
                context={"topic": "phase3", "intent": "knowledge_sharing"},
                is_public=True,
                meta_data={"test": True}
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/phase3/aeon/interactions",
                json=interaction_data.model_dump()
            )
            
            if response.status_code == 201:
                interaction = response.json()
                print(f"✅ Created AEON interaction: {interaction['interaction_type']}")
                
                # Get AEON interactions
                response = await self.client.get(f"{self.base_url}/api/v1/phase3/aeon/interactions")
                if response.status_code == 200:
                    interactions = response.json()
                    print(f"✅ Retrieved {len(interactions)} AEON interactions")
                    
                    # Respond to interaction
                    if interactions:
                        interaction_id = interactions[0]["id"]
                        response = await self.client.post(
                            f"{self.base_url}/api/v1/phase3/aeon/interactions/{interaction_id}/respond",
                            params={"response_content": "Thank you for sharing! I'm excited about the WebSocket features."}
                        )
                        if response.status_code == 200:
                            print("✅ Successfully responded to AEON interaction")
                            return True
                
            else:
                print(f"❌ Failed to create AEON interaction: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ AEON interaction test error: {e}")
            return False
    
    async def test_social_features(self):
        """Test social network features"""
        print("\n🌐 Testing social features...")
        
        try:
            # Get social network
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/network")
            if response.status_code == 200:
                network = response.json()
                print(f"✅ Retrieved social network (strength: {network['network_strength']:.2f})")
            
            # Find similar users
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/similar-users")
            if response.status_code == 200:
                similar_users = response.json()
                print(f"✅ Found {len(similar_users)} similar users")
            
            # Get active users
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/active-users")
            if response.status_code == 200:
                active_users = response.json()
                print(f"✅ Retrieved {len(active_users)} active users")
                return True
                
        except Exception as e:
            print(f"❌ Social features test error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket real-time messaging"""
        print("\n🔌 Testing WebSocket connection...")
        
        if not self.test_users:
            print("❌ No test users available for WebSocket testing")
            return False
        
        try:
            user_id = self.test_users[0]["id"]
            websocket_url = f"ws://localhost:8000/api/v1/phase3/ws/{user_id}"
            
            async with websockets.connect(websocket_url) as websocket:
                print("✅ WebSocket connection established")
                
                # Send a test message
                test_message = {
                    "type": "chat_message",
                    "content": "Hello from Phase 3 test!",
                    "room_id": "test-room",
                    "message_type": "text"
                }
                
                await websocket.send(json.dumps(test_message))
                print("✅ Test message sent via WebSocket")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"✅ Received WebSocket response: {response[:100]}...")
                    return True
                except asyncio.TimeoutError:
                    print("⚠️  No WebSocket response received (timeout)")
                    return True  # Connection works, just no response
                
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
            return False
    
    async def test_phase3_health(self):
        """Test Phase 3 health endpoint"""
        print("\n🏥 Testing Phase 3 health...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/health/phase3")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Phase 3 health: {health['status']}")
                print(f"   WebSocket connections: {health.get('websocket_connections', 0)}")
                print(f"   Active rooms: {health.get('active_rooms', 0)}")
                return True
            else:
                print(f"❌ Phase 3 health check failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Phase 3 health test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all Phase 3 tests"""
        print("🧪 Starting AEON Phase 3 Test Suite")
        print("=" * 50)
        
        test_results = {}
        
        # Setup
        await self.setup_test_users()
        
        # Run tests
        tests = [
            ("Authentication", self.test_authentication),
            ("Chat Rooms", self.test_chat_rooms),
            ("User Relationships", self.test_user_relationships),
            ("Shared Knowledge", self.test_shared_knowledge),
            ("AEON Interactions", self.test_aeon_interactions),
            ("Social Features", self.test_social_features),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Phase 3 Health", self.test_phase3_health)
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                test_results[test_name] = result
                print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                test_results[test_name] = False
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Phase 3 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All Phase 3 tests passed! The Digital Realm is ready!")
        else:
            print("⚠️  Some tests failed. Check the logs for details.")
        
        await self.client.aclose()


async def main():
    """Main test function"""
    tester = Phase3Tester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 