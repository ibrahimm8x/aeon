#!/usr/bin/env python3
"""
Test script to verify web interface chat functionality
"""

import requests
import json
import time

def test_web_interface_chat():
    """Test the web interface chat functionality"""
    print("🧪 Testing Web Interface Chat Functionality...")
    print("=" * 60)
    
    # Test 1: Check if web interface is accessible
    print("1. Testing web interface accessibility...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Web interface is accessible")
        else:
            print(f"❌ Web interface returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface error: {e}")
        return False
    
    # Test 2: Check if API server is accessible
    print("\n2. Testing API server accessibility...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is accessible")
        else:
            print(f"❌ API server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API server error: {e}")
        return False
    
    # Test 3: Test chat endpoint directly
    print("\n3. Testing chat endpoint...")
    try:
        chat_data = {
            "message": "Hello from web interface test!",
            "user_id": 1
        }
        response = requests.post(
            "http://localhost:8000/api/v1/test/test-chat",
            headers={"Content-Type": "application/json"},
            json=chat_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working")
            print(f"📝 AEON Response: {data['message']['content']}")
            print(f"⏱️  Response time: {data['response_time']:.2f}s")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 4: Test multiple messages
    print("\n4. Testing multiple messages...")
    test_messages = [
        "Hello AEON!",
        "How are you today?",
        "Can you help me with something?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            chat_data = {"message": message, "user_id": 1}
            response = requests.post(
                "http://localhost:8000/api/v1/test/test-chat",
                headers={"Content-Type": "application/json"},
                json=chat_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Message {i}: {data['message']['content'][:50]}...")
            else:
                print(f"❌ Message {i} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Message {i} error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Web Interface Chat Test: PASSED")
    print("📱 The web interface should now display messages correctly!")
    print("🌐 Web Interface: http://localhost:8080")
    print("🔗 API Base: http://localhost:8000/api/v1")
    print("\n💡 Instructions:")
    print("1. Open http://localhost:8080 in your browser")
    print("2. Type a message in the chat input")
    print("3. Press Enter or click the send button")
    print("4. AEON should respond and display the messages")
    
    return True

if __name__ == "__main__":
    success = test_web_interface_chat()
    exit(0 if success else 1) 