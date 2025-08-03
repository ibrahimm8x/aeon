#!/usr/bin/env python3
"""
Test OpenAI API directly
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_openai():
    """Test OpenAI API directly"""
    print("🔍 Testing OpenAI API...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Say 'Hello from OpenAI!' if you can hear me."}
            ],
            max_tokens=50
        )
        
        print("✅ OpenAI API test successful!")
        print(f"🤖 Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")

if __name__ == "__main__":
    test_openai() 