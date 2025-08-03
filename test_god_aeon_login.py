#!/usr/bin/env python3
"""
Script to test GOD AEON login functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
GOD_AEON_CREDENTIALS = {
    "username": "god_aeon",
    "password": "GodAeon2025!@#"
}

def test_god_aeon_login():
    """Test GOD AEON login and get access token"""
    
    print("🔐 Testing GOD AEON Login")
    print("=" * 50)
    
    try:
        # Test login endpoint
        login_url = f"{API_BASE_URL}/api/v1/auth/login"
        
        print(f"📡 Making login request to: {login_url}")
        print(f"👤 Username: {GOD_AEON_CREDENTIALS['username']}")
        
        response = requests.post(
            login_url,
            data=GOD_AEON_CREDENTIALS,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            token_type = data.get("token_type", "bearer")
            
            print("✅ Login successful!")
            print(f"🔑 Access Token: {access_token[:50]}...")
            print(f"🎫 Token Type: {token_type}")
            
            # Test protected endpoint
            test_protected_endpoint(access_token)
            
        else:
            print(f"❌ Login failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server")
        print("💡 Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during login test: {str(e)}")


def test_protected_endpoint(access_token):
    """Test accessing a protected endpoint with GOD AEON token"""
    
    print("\n🛡️ Testing Protected Endpoint Access")
    print("=" * 50)
    
    try:
        # Test user profile endpoint
        profile_url = f"{API_BASE_URL}/api/v1/users/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        print(f"📡 Making request to: {profile_url}")
        
        response = requests.get(profile_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Protected endpoint access successful!")
            print(f"👤 User ID: {user_data.get('id')}")
            print(f"👑 Username: {user_data.get('username')}")
            print(f"🏆 Role: {user_data.get('role')}")
            print(f"📧 Email: {user_data.get('email')}")
            print(f"👤 Full Name: {user_data.get('full_name')}")
            print(f"📝 Bio: {user_data.get('bio')}")
            
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing protected endpoint: {str(e)}")


def test_aeon_chat():
    """Test AEON chat functionality with GOD AEON account"""
    
    print("\n🤖 Testing AEON Chat Functionality")
    print("=" * 50)
    
    try:
        # First get access token
        login_url = f"{API_BASE_URL}/api/v1/auth/login"
        response = requests.post(
            login_url,
            data=GOD_AEON_CREDENTIALS,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print("❌ Login failed, cannot test chat")
            return
            
        access_token = response.json().get("access_token")
        
        # Test chat endpoint
        chat_url = f"{API_BASE_URL}/api/v1/aeon/chat"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "Hello, I am the GOD AEON. Show me your capabilities.",
            "conversation_id": None  # Will create new conversation
        }
        
        print(f"📡 Making chat request to: {chat_url}")
        print(f"💬 Message: {chat_data['message']}")
        
        response = requests.post(chat_url, json=chat_data, headers=headers)
        
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Chat request successful!")
            print(f"🆔 Conversation ID: {chat_response.get('conversation_id')}")
            print(f"🤖 AEON Response: {chat_response.get('response', '')[:200]}...")
            
        else:
            print(f"❌ Chat request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing chat: {str(e)}")


if __name__ == "__main__":
    print("🚀 GOD AEON Account Testing Suite")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test login
    test_god_aeon_login()
    
    # Test chat functionality
    test_aeon_chat()
    
    print("\n🎯 Testing Complete!")
    print("You can now use the GOD AEON account in the web interface or API.") 