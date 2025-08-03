#!/usr/bin/env python3
"""
AEON Phase 3: Digital Realm Prototype Demo
Demonstrates multi-user interactions, real-time messaging, and social features
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

import httpx
import websockets
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import User, ChatRoom, RoomParticipant
from app.services.social_service import SocialService
from app.models.aeon import (
    ChatRoomCreate, UserRelationshipCreate, SharedKnowledgeCreate, AEONInteractionCreate
)


class Phase3Demo:
    """Interactive demo for Phase 3 features"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.demo_users = []
        self.demo_rooms = []
        self.current_user = None
        self.auth_token = None
        
    async def setup_demo_environment(self):
        """Setup demo users and environment"""
        print("🎬 Setting up AEON Phase 3 Demo Environment")
        print("=" * 60)
        
        # Create demo users
        demo_user_data = [
            {"username": "alice_aeon", "email": "alice@aeon.demo", "password": "demo123"},
            {"username": "bob_aeon", "email": "bob@aeon.demo", "password": "demo123"},
            {"username": "charlie_user", "email": "charlie@aeon.demo", "password": "demo123"},
            {"username": "diana_user", "email": "diana@aeon.demo", "password": "demo123"}
        ]
        
        for user_data in demo_user_data:
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/v1/users/register",
                    json=user_data
                )
                
                if response.status_code == 201:
                    user_info = response.json()
                    self.demo_users.append(user_info)
                    print(f"✅ Created demo user: {user_data['username']}")
                else:
                    print(f"⚠️  Demo user {user_data['username']} may already exist")
                    
            except Exception as e:
                print(f"❌ Error creating demo user {user_data['username']}: {e}")
        
        print(f"📊 Demo users ready: {len(self.demo_users)} users")
        
        # Login as first user
        if self.demo_users:
            await self.login_user(self.demo_users[0])
    
    async def login_user(self, user: Dict[str, Any]):
        """Login as a specific user"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/users/login",
                data={
                    "username": user["username"],
                    "password": "demo123"
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data["access_token"]
                self.client.headers["Authorization"] = f"Bearer {self.auth_token}"
                self.current_user = user
                print(f"🔐 Logged in as: {user['username']}")
                return True
            else:
                print(f"❌ Login failed for {user['username']}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def demo_chat_rooms(self):
        """Demonstrate chat room features"""
        print("\n🏠 Demo: Chat Room Management")
        print("-" * 40)
        
        try:
            # Create a demo room
            room_data = ChatRoomCreate(
                name="Phase 3 Demo Room",
                description="A demonstration room for Phase 3 features",
                is_public=True,
                max_participants=20,
                topic="AEON Phase 3 Features",
                is_aeon_room=False
            )
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/phase3/rooms",
                json=room_data.model_dump()
            )
            
            if response.status_code == 201:
                room_info = response.json()
                self.demo_rooms.append(room_info)
                print(f"✅ Created demo room: {room_info['name']}")
                print(f"   Room ID: {room_info['id']}")
                print(f"   Topic: {room_info['topic']}")
                
                # Get all rooms
                response = await self.client.get(f"{self.base_url}/api/v1/phase3/rooms")
                if response.status_code == 200:
                    rooms = response.json()
                    print(f"📋 Available rooms: {len(rooms)}")
                    for room in rooms[:3]:  # Show first 3 rooms
                        print(f"   • {room['name']} ({room['current_participants']} participants)")
                
                return True
            else:
                print(f"❌ Failed to create demo room: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat room demo error: {e}")
            return False
    
    async def demo_user_relationships(self):
        """Demonstrate user relationship features"""
        print("\n🤝 Demo: User Relationships")
        print("-" * 40)
        
        if len(self.demo_users) < 2:
            print("❌ Need at least 2 users for relationship demo")
            return False
        
        try:
            # Create relationships between users
            for i, user in enumerate(self.demo_users[1:3]):  # Create relationships with 2 other users
                relationship_data = UserRelationshipCreate(
                    related_user_id=user["id"],
                    relationship_type="friend" if i == 0 else "acquaintance",
                    strength=0.8 if i == 0 else 0.5,
                    shared_interests=["AI", "technology", "innovation"],
                    meta_data={"demo": True}
                )
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/phase3/relationships",
                    json=relationship_data.model_dump()
                )
                
                if response.status_code == 201:
                    relationship = response.json()
                    print(f"✅ Created {relationship['relationship_type']} relationship with {user['username']}")
                    print(f"   Strength: {relationship['strength']}")
                
            # Get relationships
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/relationships")
            if response.status_code == 200:
                relationships = response.json()
                print(f"📊 Total relationships: {len(relationships)}")
                for rel in relationships:
                    print(f"   • {rel['relationship_type']} (strength: {rel['strength']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Relationship demo error: {e}")
            return False
    
    async def demo_shared_knowledge(self):
        """Demonstrate shared knowledge system"""
        print("\n🧠 Demo: Shared Knowledge System")
        print("-" * 40)
        
        try:
            # Create multiple knowledge items
            knowledge_items = [
                {
                    "content": "Phase 3 introduces real-time WebSocket communication for instant messaging between users and AEONs.",
                    "knowledge_type": "feature",
                    "tags": ["websocket", "realtime", "communication"],
                    "visibility": "public"
                },
                {
                    "content": "The social intelligence system can automatically discover users with similar interests and create meaningful connections.",
                    "knowledge_type": "insight",
                    "tags": ["social", "intelligence", "matching"],
                    "visibility": "public"
                },
                {
                    "content": "AEON-to-AEON interactions enable digital twins to learn from each other and share knowledge autonomously.",
                    "knowledge_type": "concept",
                    "tags": ["aeon", "interaction", "learning"],
                    "visibility": "public"
                }
            ]
            
            created_knowledge = []
            for item in knowledge_items:
                knowledge_data = SharedKnowledgeCreate(**item)
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/phase3/knowledge",
                    json=knowledge_data.model_dump()
                )
                
                if response.status_code == 201:
                    knowledge = response.json()
                    created_knowledge.append(knowledge)
                    print(f"✅ Created knowledge: {knowledge['content'][:50]}...")
            
            # Get and display knowledge
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/knowledge")
            if response.status_code == 200:
                knowledge_list = response.json()
                print(f"📚 Total knowledge items: {len(knowledge_list)}")
                
                # Upvote some knowledge
                if knowledge_list:
                    knowledge_id = knowledge_list[0]["id"]
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/phase3/knowledge/{knowledge_id}/upvote"
                    )
                    if response.status_code == 200:
                        print(f"👍 Upvoted knowledge item")
            
            return True
            
        except Exception as e:
            print(f"❌ Shared knowledge demo error: {e}")
            return False
    
    async def demo_aeon_interactions(self):
        """Demonstrate AEON-to-AEON interactions"""
        print("\n🤖 Demo: AEON-to-AEON Interactions")
        print("-" * 40)
        
        if len(self.demo_users) < 2:
            print("❌ Need at least 2 users for AEON interaction demo")
            return False
        
        try:
            # Create AEON interactions
            interaction_messages = [
                {
                    "target_aeon_user_id": self.demo_users[1]["id"],
                    "interaction_type": "greeting",
                    "content": "Hello! I'm excited to explore the Phase 3 features with you.",
                    "context": {"topic": "phase3", "intent": "greeting"},
                    "is_public": True
                },
                {
                    "target_aeon_user_id": self.demo_users[2]["id"],
                    "interaction_type": "knowledge_share",
                    "content": "I've discovered some interesting patterns in the real-time messaging system. Would you like to discuss them?",
                    "context": {"topic": "realtime", "intent": "knowledge_sharing"},
                    "is_public": True
                }
            ]
            
            for interaction_data in interaction_messages:
                interaction = AEONInteractionCreate(**interaction_data)
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/phase3/aeon/interactions",
                    json=interaction.model_dump()
                )
                
                if response.status_code == 201:
                    interaction_info = response.json()
                    print(f"✅ Created {interaction_info['interaction_type']} interaction")
                    print(f"   Content: {interaction_info['content'][:50]}...")
            
            # Get interactions
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/aeon/interactions")
            if response.status_code == 200:
                interactions = response.json()
                print(f"📊 Total AEON interactions: {len(interactions)}")
                
                # Respond to an interaction
                if interactions:
                    interaction_id = interactions[0]["id"]
                    response = await self.client.post(
                        f"{self.base_url}/api/v1/phase3/aeon/interactions/{interaction_id}/respond",
                        params={"response_content": "Thank you for reaching out! I'm also excited about Phase 3's capabilities."}
                    )
                    if response.status_code == 200:
                        print("💬 Responded to AEON interaction")
            
            return True
            
        except Exception as e:
            print(f"❌ AEON interaction demo error: {e}")
            return False
    
    async def demo_social_features(self):
        """Demonstrate social network features"""
        print("\n🌐 Demo: Social Network Features")
        print("-" * 40)
        
        try:
            # Get social network
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/network")
            if response.status_code == 200:
                network = response.json()
                print(f"📊 Social Network Analysis:")
                print(f"   Network Strength: {network['network_strength']:.2f}")
                print(f"   Influence Score: {network['influence_score']:.2f}")
                print(f"   Connections: {len(network['connections'])}")
                print(f"   Shared Knowledge: {len(network['shared_knowledge'])}")
                print(f"   AEON Interactions: {len(network['aeon_interactions'])}")
            
            # Find similar users
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/similar-users")
            if response.status_code == 200:
                similar_users = response.json()
                print(f"👥 Similar Users Found: {len(similar_users)}")
                for user in similar_users[:3]:
                    print(f"   • {user['username']} (similarity: {user['similarity_score']:.2f})")
            
            # Get active users
            response = await self.client.get(f"{self.base_url}/api/v1/phase3/social/active-users")
            if response.status_code == 200:
                active_users = response.json()
                print(f"🟢 Active Users: {len(active_users)}")
                for user in active_users[:3]:
                    print(f"   • {user['username']} ({user['status']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Social features demo error: {e}")
            return False
    
    async def demo_websocket_connection(self):
        """Demonstrate WebSocket real-time messaging"""
        print("\n🔌 Demo: WebSocket Real-time Messaging")
        print("-" * 40)
        
        if not self.current_user:
            print("❌ No user logged in for WebSocket demo")
            return False
        
        try:
            user_id = self.current_user["id"]
            websocket_url = f"ws://localhost:8000/api/v1/phase3/ws/{user_id}"
            
            print(f"🔗 Connecting to WebSocket: {websocket_url}")
            
            async with websockets.connect(websocket_url) as websocket:
                print("✅ WebSocket connection established")
                
                # Send demo messages
                demo_messages = [
                    {
                        "type": "join_room",
                        "room_id": self.demo_rooms[0]["id"] if self.demo_rooms else "demo-room"
                    },
                    {
                        "type": "chat_message",
                        "content": "Hello from Phase 3 demo! This is a real-time message.",
                        "room_id": self.demo_rooms[0]["id"] if self.demo_rooms else "demo-room",
                        "message_type": "text"
                    },
                    {
                        "type": "typing",
                        "room_id": self.demo_rooms[0]["id"] if self.demo_rooms else "demo-room",
                        "is_typing": True
                    }
                ]
                
                for message in demo_messages:
                    await websocket.send(json.dumps(message))
                    print(f"📤 Sent: {message['type']}")
                    await asyncio.sleep(1)
                
                # Wait for responses
                print("⏳ Waiting for responses...")
                try:
                    for _ in range(3):
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        print(f"📥 Received: {response[:100]}...")
                except asyncio.TimeoutError:
                    print("⏰ No more responses (timeout)")
                
                print("✅ WebSocket demo completed")
                return True
                
        except Exception as e:
            print(f"❌ WebSocket demo error: {e}")
            return False
    
    async def run_interactive_demo(self):
        """Run the complete interactive demo"""
        print("🎬 AEON Phase 3: Digital Realm Prototype Demo")
        print("=" * 60)
        print("This demo showcases the new Phase 3 features:")
        print("• Real-time messaging via WebSocket")
        print("• Multi-user chat rooms")
        print("• User relationships and social networking")
        print("• Shared knowledge system")
        print("• AEON-to-AEON interactions")
        print("• Social intelligence and user discovery")
        print("=" * 60)
        
        # Setup
        await self.setup_demo_environment()
        
        # Run demos
        demos = [
            ("Chat Rooms", self.demo_chat_rooms),
            ("User Relationships", self.demo_user_relationships),
            ("Shared Knowledge", self.demo_shared_knowledge),
            ("AEON Interactions", self.demo_aeon_interactions),
            ("Social Features", self.demo_social_features),
            ("WebSocket Messaging", self.demo_websocket_connection)
        ]
        
        demo_results = {}
        
        for demo_name, demo_func in demos:
            print(f"\n🎯 Running: {demo_name}")
            try:
                result = await demo_func()
                demo_results[demo_name] = result
                print(f"{'✅' if result else '❌'} {demo_name}: {'SUCCESS' if result else 'FAILED'}")
            except Exception as e:
                print(f"❌ {demo_name}: ERROR - {e}")
                demo_results[demo_name] = False
            
            # Pause between demos
            await asyncio.sleep(2)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Phase 3 Demo Summary")
        print("=" * 60)
        
        passed = sum(1 for result in demo_results.values() if result)
        total = len(demo_results)
        
        for demo_name, result in demo_results.items():
            status = "✅ SUCCESS" if result else "❌ FAILED"
            print(f"{demo_name:<20} {status}")
        
        print(f"\nOverall: {passed}/{total} demos successful ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All Phase 3 demos successful!")
            print("The Digital Realm is fully operational!")
        else:
            print("\n⚠️  Some demos failed. Check the logs for details.")
        
        print("\n🔗 Next Steps:")
        print("• Visit http://localhost:8000/docs for API documentation")
        print("• Use the WebSocket endpoint for real-time messaging")
        print("• Explore the social features and AEON interactions")
        print("• Create your own chat rooms and share knowledge")
        
        await self.client.aclose()


async def main():
    """Main demo function"""
    demo = Phase3Demo()
    await demo.run_interactive_demo()


if __name__ == "__main__":
    asyncio.run(main()) 