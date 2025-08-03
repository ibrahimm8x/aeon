#!/usr/bin/env python3
"""
Demo script for Phase 1 functionality
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


class AEONDemo:
    def __init__(self):
        self.token = None
        self.user_data = {
            "username": "demo_user",
            "email": "demo@aeon.com",
            "password": "demo123456",
            "full_name": "Demo User",
            "bio": "Demo user for AEON Phase 1"
        }
    
    def setup_user(self):
        """Setup demo user (register or login)"""
        print("🔧 Setting up demo user...")
        
        # Try to login first
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/users/login", json=login_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                print("✅ Login successful!")
                return True
        except:
            pass
        
        # If login fails, try to register
        try:
            response = requests.post(f"{BASE_URL}/users/register", json=self.user_data)
            if response.status_code == 201:
                print("✅ Registration successful!")
                # Now login
                response = requests.post(f"{BASE_URL}/users/login", json=login_data)
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    print("✅ Login successful!")
                    return True
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
        
        return False
    
    def get_headers(self):
        """Get headers with authentication token"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def show_status(self):
        """Show AEON status"""
        try:
            response = requests.get(f"{BASE_URL}/aeon/status", headers=self.get_headers())
            if response.status_code == 200:
                status = response.json()
                print(f"\n📊 AEON Status:")
                print(f"   Conversations: {status['total_conversations']}")
                print(f"   Messages: {status['total_messages']}")
                print(f"   Memories: {status['total_memories']}")
                if status['last_active']:
                    print(f"   Last Active: {status['last_active']}")
        except Exception as e:
            print(f"❌ Failed to get status: {e}")
    
    def chat_with_aeon(self, message: str):
        """Chat with AEON"""
        try:
            chat_data = {"message": message}
            response = requests.post(f"{BASE_URL}/aeon/chat", json=chat_data, headers=self.get_headers())
            
            if response.status_code == 200:
                result = response.json()
                aeon_response = result["message"]["content"]
                response_time = result["response_time"]
                
                print(f"\n🤖 AEON: {aeon_response}")
                print(f"⏱️  Response time: {response_time:.2f}s")
                return True
            else:
                print(f"❌ Chat failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return False
    
    def interactive_chat(self):
        """Start interactive chat session"""
        print("\n💬 Starting interactive chat with AEON...")
        print("Type 'quit' to exit, 'status' to see AEON status")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'status':
                    self.show_status()
                    continue
                elif not user_input:
                    continue
                
                self.chat_with_aeon(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def run_demo(self):
        """Run the complete demo"""
        print("🚀 AEON Phase 1 Demo")
        print("=" * 50)
        
        # Setup user
        if not self.setup_user():
            print("❌ Failed to setup user. Make sure the server is running.")
            return
        
        # Show initial status
        self.show_status()
        
        # Start interactive chat
        self.interactive_chat()


def main():
    """Main function"""
    demo = AEONDemo()
    demo.run_demo()


if __name__ == "__main__":
    main() 