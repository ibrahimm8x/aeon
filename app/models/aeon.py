"""
AEON AI twin models and schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    AEON = "aeon"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Types of messages"""
    TEXT = "text"
    MEMORY = "memory"
    REFLECTION = "reflection"
    LEARNING = "learning"


class ChatMessage(BaseModel):
    """Chat message model"""
    id: Optional[int] = None
    user_id: int
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    meta_data: Optional[Dict[str, Any]] = None


class ChatMessageCreate(BaseModel):
    """Create chat message model"""
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: MessageType = MessageType.TEXT
    meta_data: Optional[Dict[str, Any]] = None


class ChatMessageResponse(ChatMessage):
    """Chat message response model"""
    
    model_config = {"from_attributes": True}


class Conversation(BaseModel):
    """Conversation model"""
    id: Optional[int] = None
    user_id: int
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    is_active: bool = True


class ConversationResponse(Conversation):
    """Conversation response model"""
    messages: Optional[List[ChatMessageResponse]] = []
    
    model_config = {"from_attributes": True}


class MemoryEntry(BaseModel):
    """Memory entry model for Phase 2 preparation"""
    id: Optional[int] = None
    user_id: int
    content: str = Field(..., min_length=1)
    memory_type: str = Field(..., description="Type of memory (fact, experience, preference, etc.)")
    importance: int = Field(1, ge=1, le=10, description="Memory importance (1-10)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    meta_data: Optional[Dict[str, Any]] = None


class MemoryEntryCreate(BaseModel):
    """Create memory entry model"""
    content: str = Field(..., min_length=1)
    memory_type: str = Field(..., description="Type of memory")
    importance: int = Field(1, ge=1, le=10)
    meta_data: Optional[Dict[str, Any]] = None


class MemoryEntryResponse(MemoryEntry):
    """Memory entry response model"""
    
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: ChatMessageResponse
    conversation_id: int
    memory_accessed: Optional[List[MemoryEntryResponse]] = None
    response_time: float
    tokens_used: Optional[int] = None


class AEONStatus(BaseModel):
    """AEON status information"""
    user_id: int
    total_conversations: int
    total_messages: int
    total_memories: int
    last_active: Optional[datetime] = None
    personality_traits: Optional[Dict[str, Any]] = None
    learning_progress: Optional[Dict[str, Any]] = None


# Phase 3: Multi-User and Real-time Models

class ConnectionStatus(str, Enum):
    """WebSocket connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    TYPING = "typing"
    AWAY = "away"


class RealTimeMessage(BaseModel):
    """Real-time message model for WebSocket communication"""
    message_id: str
    sender_id: int
    sender_name: str
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    room_id: Optional[str] = None
    is_aeon_message: bool = False
    meta_data: Optional[Dict[str, Any]] = None


class RealTimeMessageCreate(BaseModel):
    """Create real-time message model"""
    content: str = Field(..., min_length=1, max_length=4000)
    message_type: MessageType = MessageType.TEXT
    room_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class UserPresence(BaseModel):
    """User presence model for real-time status"""
    user_id: int
    username: str
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    current_room: Optional[str] = None
    is_aeon: bool = False


class ChatRoom(BaseModel):
    """Chat room model for multi-user conversations"""
    id: str
    name: str
    description: Optional[str] = None
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_public: bool = True
    max_participants: int = 50
    current_participants: int = 0
    topic: Optional[str] = None
    is_aeon_room: bool = False  # Room where AEONs can interact


class ChatRoomCreate(BaseModel):
    """Create chat room model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = True
    max_participants: int = 50
    topic: Optional[str] = None
    is_aeon_room: bool = False


class ChatRoomResponse(ChatRoom):
    """Chat room response model"""
    participants: Optional[List[UserPresence]] = []
    
    model_config = {"from_attributes": True}


class UserRelationship(BaseModel):
    """User relationship model for social intelligence"""
    id: Optional[int] = None
    user_id: int
    related_user_id: int
    relationship_type: str = Field(..., description="Type of relationship (friend, acquaintance, etc.)")
    strength: float = Field(1.0, ge=0.0, le=1.0, description="Relationship strength (0-1)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_interaction: datetime = Field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    shared_interests: Optional[List[str]] = []
    meta_data: Optional[Dict[str, Any]] = None


class UserRelationshipCreate(BaseModel):
    """Create user relationship model"""
    related_user_id: int
    relationship_type: str = Field(..., description="Type of relationship")
    strength: float = Field(1.0, ge=0.0, le=1.0)
    shared_interests: Optional[List[str]] = []
    meta_data: Optional[Dict[str, Any]] = None


class SharedKnowledge(BaseModel):
    """Shared knowledge model for cross-user learning"""
    id: Optional[int] = None
    creator_id: int
    content: str = Field(..., min_length=1)
    knowledge_type: str = Field(..., description="Type of knowledge (fact, insight, etc.)")
    tags: Optional[List[str]] = []
    visibility: str = Field("public", description="Visibility level (public, friends, private)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    upvotes: int = 0
    downvotes: int = 0
    share_count: int = 0
    meta_data: Optional[Dict[str, Any]] = None


class SharedKnowledgeCreate(BaseModel):
    """Create shared knowledge model"""
    content: str = Field(..., min_length=1)
    knowledge_type: str = Field(..., description="Type of knowledge")
    tags: Optional[List[str]] = []
    visibility: str = Field("public", description="Visibility level")
    meta_data: Optional[Dict[str, Any]] = None


class SharedKnowledgeResponse(SharedKnowledge):
    """Shared knowledge response model"""
    creator_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class AEONInteraction(BaseModel):
    """AEON-to-AEON interaction model"""
    id: Optional[int] = None
    aeon_user_id: int
    target_aeon_user_id: int
    interaction_type: str = Field(..., description="Type of interaction (chat, knowledge_share, etc.)")
    content: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    response_content: Optional[str] = None
    response_at: Optional[datetime] = None
    is_public: bool = False
    meta_data: Optional[Dict[str, Any]] = None


class AEONInteractionCreate(BaseModel):
    """Create AEON interaction model"""
    target_aeon_user_id: int
    interaction_type: str = Field(..., description="Type of interaction")
    content: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None
    is_public: bool = False
    meta_data: Optional[Dict[str, Any]] = None


class AEONInteractionResponse(AEONInteraction):
    """AEON interaction response model"""
    aeon_name: Optional[str] = None
    target_aeon_name: Optional[str] = None
    
    model_config = {"from_attributes": True}


class SocialNetwork(BaseModel):
    """Social network model for user connections"""
    user_id: int
    connections: List[UserRelationship] = []
    shared_knowledge: List[SharedKnowledge] = []
    aeon_interactions: List[AEONInteraction] = []
    network_strength: float = 0.0
    influence_score: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow) 