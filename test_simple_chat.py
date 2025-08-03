#!/usr/bin/env python3
"""
Simple chat test without database
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_simple_chat():
    """Test simple chat without database complexity"""
    print("🔍 Testing simple chat...")
    
    # Login
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Login successful")
    
    # Test status endpoint first
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/aeon/status", headers=headers)
    print(f"📊 Status response: {response.status_code}")
    if response.status_code == 200:
        print(f"📊 Status data: {response.json()}")
    
    # Test chat with minimal data
    chat_data = {"message": "Hi"}
    print("📤 Testing chat...")
    response = requests.post(f"{BASE_URL}/aeon/chat", json=chat_data, headers=headers)
    
    print(f"📥 Chat response: {response.status_code}")
    print(f"📥 Chat body: {response.text}")

if __name__ == "__main__":
    test_simple_chat() 