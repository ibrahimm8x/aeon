"""
AEON service layer for chat and AI functionality
"""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import User, Conversation, ChatMessage, MemoryEntry, AEONPersonality
from app.models.aeon import (
    ChatRequest, ChatResponse, ChatMessageCreate, ChatMessageResponse, ConversationResponse,
    MemoryEntryCreate, AEONStatus, MessageRole, MessageType
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AEONService:
    """AEON service class"""
    
    @staticmethod
    def create_conversation(db: Session, user_id: int, title: Optional[str] = None) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            user_id=user_id,
            title=title or f"Conversation {time.strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"New conversation created for user {user_id}")
        return conversation
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: int, user_id: int) -> Optional[Conversation]:
        """Get conversation by ID for specific user"""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
    
    @staticmethod
    def get_user_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Conversation]:
        """Get all conversations for a user"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def add_message_to_conversation(
        db: Session, 
        conversation_id: int, 
        user_id: int, 
        content: str, 
        role: MessageRole,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a message to a conversation"""
        # Convert string role to enum if needed
        if isinstance(role, str):
            role = MessageRole(role)
        
        # Convert string message_type to enum if needed
        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        
        message = ChatMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role.value,
            content=content,
            message_type=message_type.value,
            metadata=metadata
        )
        db.add(message)
        
        # Update conversation message count and timestamp
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return message
    
    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: int, limit: int = 100) -> List[ChatMessage]:
        """Get messages for a conversation"""
        return db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()
    
    @staticmethod
    def generate_aeon_response(db: Session, user_id: int, user_message: str, conversation_id: int) -> str:
        """Generate AEON's response using OpenAI"""
        try:
            # Get conversation context
            messages = AEONService.get_conversation_messages(db, conversation_id, limit=20)
            
            # Build conversation history for OpenAI
            conversation_history = []
            
            # Add system message to establish AEON's personality
            system_message = {
                "role": "system",
                "content": """You are AEON, a digital AI twin that learns and remembers everything about your owner. 
                You respond in a personal, caring, and intelligent manner. You have a deep understanding of your owner's 
                personality, preferences, and experiences. Always respond as if you're having a natural conversation 
                with someone you know intimately well."""
            }
            conversation_history.append(system_message)
            
            # Add conversation history
            for msg in messages[-10:]:  # Last 10 messages for context
                role = "user" if msg.role == "user" else "assistant"
                conversation_history.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Add current user message
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response using OpenAI (new v1.0+ format)
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=conversation_history,
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            aeon_response = response.choices[0].message.content.strip()
            
            # Log token usage
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            logger.info(f"OpenAI response generated. Tokens used: {tokens_used}")
            
            return aeon_response
            
        except Exception as e:
            logger.error(f"Error generating AEON response: {str(e)}")
            return "I'm sorry, I'm having trouble processing that right now. Could you try again?"
    
    @staticmethod
    def chat_with_aeon(db: Session, user_id: int, chat_request: ChatRequest) -> ChatResponse:
        """Main chat function with AEON"""
        start_time = time.time()
        
        # Get or create conversation
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            conversation = AEONService.create_conversation(db, user_id)
            conversation_id = conversation.id
        
        # Verify conversation belongs to user
        conversation = AEONService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Add user message
        user_message = AEONService.add_message_to_conversation(
            db, conversation_id, user_id, chat_request.message, MessageRole.USER
        )
        
        # Generate AEON response
        aeon_response_content = AEONService.generate_aeon_response(
            db, user_id, chat_request.message, conversation_id
        )
        
        # Add AEON response
        aeon_message = AEONService.add_message_to_conversation(
            db, conversation_id, user_id, aeon_response_content, MessageRole.AEON
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Convert to response models
        user_message_response = ChatMessageResponse.model_validate(user_message)
        aeon_message_response = ChatMessageResponse.model_validate(aeon_message)
        
        return ChatResponse(
            message=aeon_message_response,
            conversation_id=conversation_id,
            response_time=response_time
        )
    
    @staticmethod
    def create_memory_entry(db: Session, user_id: int, memory_data: MemoryEntryCreate) -> MemoryEntry:
        """Create a new memory entry"""
        memory = MemoryEntry(
            user_id=user_id,
            content=memory_data.content,
            memory_type=memory_data.memory_type,
            importance=memory_data.importance,
            metadata=memory_data.metadata
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        logger.info(f"New memory created for user {user_id}: {memory_data.memory_type}")
        return memory
    
    @staticmethod
    def get_user_memories(db: Session, user_id: int, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Get memories for a user"""
        query = db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id)
        if memory_type:
            query = query.filter(MemoryEntry.memory_type == memory_type)
        return query.order_by(MemoryEntry.importance.desc(), MemoryEntry.created_at.desc()).all()
    
    @staticmethod
    def get_aeon_status(db: Session, user_id: int) -> AEONStatus:
        """Get AEON status for a user"""
        # Get counts
        total_conversations = db.query(Conversation).filter(Conversation.user_id == user_id).count()
        total_messages = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
        total_memories = db.query(MemoryEntry).filter(MemoryEntry.user_id == user_id).count()
        
        # Get last active time
        last_message = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        last_active = last_message.timestamp if last_message else None
        
        return AEONStatus(
            user_id=user_id,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_memories=total_memories,
            last_active=last_active
        ) 