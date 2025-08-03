#!/usr/bin/env python3
"""
Test service layer directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.services.aeon_service import AEONService
from app.models.aeon import ChatRequest, MessageRole

def test_service():
    """Test service layer directly"""
    print("🔍 Testing service layer...")
    
    try:
        db = SessionLocal()
        
        # Test creating a conversation
        print("📝 Creating conversation...")
        conversation = AEONService.create_conversation(db, user_id=1, title="Test Conversation")
        print(f"✅ Conversation created: {conversation.id}")
        
        # Test adding a message
        print("💬 Adding message...")
        message = AEONService.add_message_to_conversation(
            db, conversation.id, 1, "Hello AEON!", MessageRole.USER
        )
        print(f"✅ Message added: {message.id}")
        
        # Test generating response
        print("🤖 Generating response...")
        response = AEONService.generate_aeon_response(db, 1, "Hello AEON!", conversation.id)
        print(f"✅ Response generated: {response}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service() 