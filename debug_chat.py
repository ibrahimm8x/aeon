#!/usr/bin/env python3
"""
Debug script for chat functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_chat():
    """Test chat functionality"""
    print("🔍 Testing chat functionality...")
    
    # First, login to get a token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return
    
    token = response.json()["access_token"]
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # Test chat
    headers = {"Authorization": f"Bearer {token}"}
    chat_data = {"message": "Hello AEON!"}
    
    print("📤 Sending chat request...")
    response = requests.post(f"{BASE_URL}/aeon/chat", json=chat_data, headers=headers)
    
    print(f"📥 Response status: {response.status_code}")
    print(f"📥 Response headers: {dict(response.headers)}")
    print(f"📥 Response body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Chat successful!")
        result = response.json()
        print(f"🤖 AEON: {result['message']['content']}")
    else:
        print("❌ Chat failed!")

if __name__ == "__main__":
    test_chat() 