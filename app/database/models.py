"""
SQLAlchemy database models for AEON
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User database model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String(20), default="owner", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("MemoryEntry", back_populates="user", cascade="all, delete-orphan")
    # Phase 3 relationships
    chat_rooms_created = relationship("ChatRoom", back_populates="creator", cascade="all, delete-orphan")
    user_relationships = relationship("UserRelationship", foreign_keys="UserRelationship.user_id", back_populates="user", cascade="all, delete-orphan")
    shared_knowledge = relationship("SharedKnowledge", back_populates="creator", cascade="all, delete-orphan")
    aeon_interactions_sent = relationship("AEONInteraction", foreign_keys="AEONInteraction.aeon_user_id", back_populates="aeon_user", cascade="all, delete-orphan")
    # Email and Web Activity relationships
    email_configs = relationship("EmailConfig", back_populates="user", cascade="all, delete-orphan")
    web_activities = relationship("WebActivity", back_populates="user", cascade="all, delete-orphan")
    web_sessions = relationship("WebSession", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation database model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message database model"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, aeon, system
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class MemoryEntry(Base):
    """Memory entry database model"""
    __tablename__ = "memory_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(String(50), nullable=False)
    importance = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="memories")


class AEONPersonality(Base):
    """AEON personality traits database model"""
    __tablename__ = "aeon_personalities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    personality_traits = Column(JSON, nullable=True)
    learning_progress = Column(JSON, nullable=True)
    last_active = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# Phase 3: Multi-User and Real-time Models

class ChatRoom(Base):
    """Chat room database model for multi-user conversations"""
    __tablename__ = "chat_rooms"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    max_participants = Column(Integer, default=50, nullable=False)
    current_participants = Column(Integer, default=0, nullable=False)
    topic = Column(String(255), nullable=True)
    is_aeon_room = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="chat_rooms_created")
    real_time_messages = relationship("RealTimeMessage", back_populates="room", cascade="all, delete-orphan")
    room_participants = relationship("RoomParticipant", back_populates="room", cascade="all, delete-orphan")


class RealTimeMessage(Base):
    """Real-time message database model for WebSocket communication"""
    __tablename__ = "real_time_messages"
    
    id = Column(String(50), primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text", nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    room_id = Column(String(50), ForeignKey("chat_rooms.id"), nullable=True)
    is_aeon_message = Column(Boolean, default=False, nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    sender = relationship("User")
    room = relationship("ChatRoom", back_populates="real_time_messages")


class RoomParticipant(Base):
    """Room participant database model for tracking who's in which room"""
    __tablename__ = "room_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="room_participants")
    user = relationship("User")


class UserPresence(Base):
    """User presence database model for real-time status tracking"""
    __tablename__ = "user_presence"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String(20), default="connected", nullable=False)  # connected, disconnected, typing, away
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    current_room = Column(String(50), ForeignKey("chat_rooms.id"), nullable=True)
    is_aeon = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User")
    room = relationship("ChatRoom")


class UserRelationship(Base):
    """User relationship database model for social intelligence"""
    __tablename__ = "user_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    related_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # friend, acquaintance, etc.
    strength = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    interaction_count = Column(Integer, default=0, nullable=False)
    shared_interests = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_relationships")
    related_user = relationship("User", foreign_keys=[related_user_id])


class SharedKnowledge(Base):
    """Shared knowledge database model for cross-user learning"""
    __tablename__ = "shared_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    knowledge_type = Column(String(50), nullable=False)  # fact, insight, etc.
    tags = Column(JSON, nullable=True)
    visibility = Column(String(20), default="public", nullable=False)  # public, friends, private
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="shared_knowledge")


class AEONInteraction(Base):
    """AEON-to-AEON interaction database model"""
    __tablename__ = "aeon_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    aeon_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_aeon_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # chat, knowledge_share, etc.
    content = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_content = Column(Text, nullable=True)
    response_at = Column(DateTime(timezone=True), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    aeon_user = relationship("User", foreign_keys=[aeon_user_id], back_populates="aeon_interactions_sent")
    target_aeon_user = relationship("User", foreign_keys=[target_aeon_user_id])


# Phase 4: Email and Web Activity Models

class EmailConfig(Base):
    """Email configuration database model"""
    __tablename__ = "email_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_address = Column(String(255), nullable=False)
    imap_server = Column(String(255), default="imap.gmail.com", nullable=False)
    imap_port = Column(Integer, default=993, nullable=False)
    smtp_server = Column(String(255), default="smtp.gmail.com", nullable=False)
    smtp_port = Column(Integer, default=587, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="email_configs")


class WebActivity(Base):
    """Web activity database model"""
    __tablename__ = "web_activities"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)
    activity_type = Column(String(50), nullable=False)  # page_view, search, click, etc.
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    duration = Column(Integer, nullable=True)  # seconds spent
    referrer = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    meta_data = Column(JSON, nullable=True)
    extracted_content = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)
    topics = Column(JSON, nullable=True)
    importance = Column(Integer, default=1, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="web_activities")


class WebSession(Base):
    """Web browsing session database model"""
    __tablename__ = "web_sessions"
    
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_pages = Column(Integer, default=0, nullable=False)
    total_duration = Column(Integer, default=0, nullable=False)  # seconds
    domains_visited = Column(JSON, nullable=True)
    primary_topics = Column(JSON, nullable=True)
    session_type = Column(String(50), default="general", nullable=False)  # work, personal, research, etc.
    
    # Relationships
    user = relationship("User", back_populates="web_sessions") 