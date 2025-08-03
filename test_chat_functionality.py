#!/usr/bin/env python3
"""
Test script to verify chat functionality
"""

import requests
import json
import time

def test_chat_functionality():
    """Test the chat functionality"""
    print("🧪 Testing AEON Chat Functionality...")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health/")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test 2: Test status endpoint
    print("\n2. Testing AEON status...")
    try:
        response = requests.get(f"{base_url}/test/test-status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AEON status: {data}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False
    
    # Test 3: Test chat endpoint
    print("\n3. Testing chat endpoint...")
    try:
        chat_data = {
            "message": "Hello AEON! How are you today?",
            "user_id": 1
        }
        response = requests.post(
            f"{base_url}/test/test-chat",
            headers={"Content-Type": "application/json"},
            json=chat_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working")
            print(f"📝 Response: {data['message']['content']}")
            print(f"⏱️  Response time: {data['response_time']:.2f}s")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 4: Test web interface
    print("\n4. Testing web interface...")
    try:
        response = requests.get("http://localhost:8080")
        if response.status_code == 200:
            print("✅ Web interface accessible")
            print("🌐 URL: http://localhost:8080")
        else:
            print(f"❌ Web interface failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Web interface error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Chat Functionality Test: PASSED")
    print("📱 You can now use the web interface to chat with AEON!")
    print("🌐 Web Interface: http://localhost:8080")
    print("🔗 API Base: http://localhost:8000/api/v1")
    
    return True

if __name__ == "__main__":
    success = test_chat_functionality()
    exit(0 if success else 1) 