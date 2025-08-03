#!/usr/bin/env python3
"""
Test script for Phase 1 functionality
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_user_registration():
    """Test user registration"""
    print("🔍 Testing user registration...")
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "bio": "A test user for Phase 1"
    }
    
    response = requests.post(f"{BASE_URL}/users/register", json=user_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.json() if response.status_code == 201 else None


def test_user_login():
    """Test user login"""
    print("🔍 Testing user login...")
    
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.json() if response.status_code == 200 else None


def test_aeon_chat(token: str):
    """Test AEON chat functionality"""
    print("🔍 Testing AEON chat...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    chat_data = {
        "message": "Hello AEON! How are you today?"
    }
    
    response = requests.post(f"{BASE_URL}/aeon/chat", json=chat_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.json() if response.status_code == 200 else None


def test_aeon_status(token: str):
    """Test AEON status endpoint"""
    print("🔍 Testing AEON status...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/aeon/status", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def main():
    """Run all tests"""
    print("🚀 Starting Phase 1 Tests...")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test user registration
    user = test_user_registration()
    
    # Test user login
    login_result = test_user_login()
    
    if login_result and "access_token" in login_result:
        token = login_result["access_token"]
        
        # Test AEON chat
        chat_result = test_aeon_chat(token)
        
        # Test AEON status
        test_aeon_status(token)
        
        print("✅ Phase 1 tests completed successfully!")
    else:
        print("❌ Login failed, skipping AEON tests")


if __name__ == "__main__":
    main() 