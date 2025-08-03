#!/usr/bin/env python3
"""
Debug Users Endpoint
"""

import requests
import json

def debug_users_endpoint():
    """Debug the users endpoint step by step"""
    base_url = "http://localhost:8000/api/v1"
    
    print("🔍 Debugging Users Endpoint...")
    
    # Test 1: Check if the endpoint exists
    print("\n1. Testing endpoint existence...")
    try:
        response = requests.get(f"{base_url}/users/")
        print(f"GET /users/ - Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 2: Test registration with detailed logging
    print("\n2. Testing registration with detailed logging...")
    register_data = {
        "username": "debug_user",
        "email": "debug@example.com",
        "password": "testpass123",
        "full_name": "Debug User"
    }
    
    print(f"URL: {base_url}/users/register")
    print(f"Data: {json.dumps(register_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/users/register", 
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            user_data = response.json()
            
            # Test 3: Test login
            print("\n3. Testing login...")
            login_data = {
                "username": "debug_user",
                "password": "testpass123"
            }
            
            response = requests.post(f"{base_url}/users/login", json=login_data)
            print(f"Login Status: {response.status_code}")
            print(f"Login Response: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print("✅ Login successful!")
                
                # Test 4: Test users endpoint with auth
                print("\n4. Testing users endpoint with auth...")
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(f"{base_url}/users/", headers=headers)
                print(f"Users Status: {response.status_code}")
                print(f"Users Response: {response.text[:200]}...")  # Truncate for readability
                
        else:
            print("❌ Registration failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_users_endpoint() 