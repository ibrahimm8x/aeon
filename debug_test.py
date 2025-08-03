#!/usr/bin/env python3
"""
Quick diagnostic test to identify the login issue
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USERNAME = "test_phase2_user"
TEST_EMAIL = "test_phase2@aeon.ai" 
TEST_PASSWORD = "test_phase2_password123"

def test_login_step_by_step():
    """Test login process step by step"""
    print("🔍 Debugging login process...")
    
    # Step 1: Try to register (should fail with user exists)
    print("\n1️⃣ Testing registration...")
    register_data = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Phase 2 Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/users/register", json=register_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Expected: User already exists")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Registration error: {e}")
    
    # Step 2: Try to login
    print("\n2️⃣ Testing login...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/users/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("   ✅ Login successful")
            print(f"   Token: {token[:20]}...")
            
            # Step 3: Get user info
            print("\n3️⃣ Testing user info retrieval...")
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers, timeout=10)
            print(f"   Status: {user_response.status_code}")
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_id = user_data["id"]
                print(f"   ✅ User info retrieved, user_id: {user_id}")
                return True
            else:
                print(f"   ❌ User info failed: {user_response.text}")
        else:
            print(f"   ❌ Login failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Login error: {e}")
    
    return False

def test_health_endpoints():
    """Test health endpoints"""
    print("\n🏥 Testing health endpoints...")
    
    # Test basic health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Basic health: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Basic health error: {e}")
    
    # Test hybrid health
    try:
        response = requests.get(f"{BASE_URL}/api/v1/aeon/health/hybrid", timeout=10)
        print(f"   Hybrid health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   All healthy: {data.get('all_healthy', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Hybrid health error: {e}")

if __name__ == "__main__":
    print("🚀 Starting diagnostic test...")
    
    # Test health endpoints first
    test_health_endpoints()
    
    # Test login process
    success = test_login_step_by_step()
    
    if success:
        print("\n✅ Login process is working correctly!")
    else:
        print("\n❌ Login process has issues!")
    
    print("\n🔍 Diagnostic complete!") 