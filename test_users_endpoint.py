#!/usr/bin/env python3
"""
Test Users Endpoint with Authentication
"""

import requests
import json

def test_users_endpoint():
    """Test the users endpoint with proper authentication"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🔐 Testing Users Endpoint with Authentication...")
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "username": "testadmin",
        "email": "testadmin@example.com",
        "password": "testpass123",
        "full_name": "Test Admin User"
    }
    
    try:
        response = requests.post(f"{base_url}/users/register", json=register_data)
        if response.status_code == 201:
            print("✅ User registered successfully")
            user_data = response.json()
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return False
    
    # Step 2: Login to get access token
    print("\n2. Logging in to get access token...")
    login_data = {
        "username": "testadmin",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/users/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            token_data = response.json()
            access_token = token_data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Step 3: Test users endpoint with authentication
    print("\n3. Testing users endpoint with authentication...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{base_url}/users/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Users endpoint working with authentication!")
            return True
        elif response.status_code == 403:
            print("❌ Users endpoint requires admin role")
            # Let's check what role the user has
            print("\n4. Checking user role...")
            me_response = requests.get(f"{base_url}/users/me", headers=headers)
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"User role: {user_info.get('role', 'No role')}")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Users endpoint error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_users_endpoint()
    exit(0 if success else 1) 