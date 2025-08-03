"""
Models package for AEON
"""

from .user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserRole,
    Token,
    TokenData
)

from .aeon import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageResponse,
    Conversation,
    ConversationResponse,
    MemoryEntry,
    MemoryEntryCreate,
    MemoryEntryResponse,
    ChatRequest,
    ChatResponse,
    AEONStatus,
    MessageRole,
    MessageType
)

__all__ = [
    # User models
    "UserBase",
    "UserCreate", 
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserRole",
    "Token",
    "TokenData",
    
    # AEON models
    "ChatMessage",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "Conversation",
    "ConversationResponse",
    "MemoryEntry",
    "MemoryEntryCreate",
    "MemoryEntryResponse",
    "ChatRequest",
    "ChatResponse",
    "AEONStatus",
    "MessageRole",
    "MessageType"
] 