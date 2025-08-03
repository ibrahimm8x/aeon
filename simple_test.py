#!/usr/bin/env python3
"""
Very simple test to isolate the requests issue
"""

import requests

def test_simple():
    """Test simple requests"""
    print("🔍 Testing simple requests...")
    
    # Test basic health
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health error: {e}")
    
    # Test login with minimal data
    try:
        data = {"username": "test_phase2_user", "password": "test_phase2_password123"}
        response = requests.post("http://localhost:8000/api/v1/users/login", json=data, timeout=5)
        print(f"✅ Login: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login successful!")
    except Exception as e:
        print(f"❌ Login error: {e}")

if __name__ == "__main__":
    test_simple() 