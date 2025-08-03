"""
Phase 3 API endpoints for multi-user interactions, real-time messaging, and social features
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.logging import get_logger
from app.database import get_db
from app.models.aeon import (
    ChatRoomCreate, ChatRoomResponse, UserPresence, RealTimeMessageCreate,
    UserRelationshipCreate, SharedKnowledgeCreate, AEONInteractionCreate,
    AEONInteractionResponse, SocialNetwork
)
from app.services.realtime_service import realtime_service
from app.services.social_service import SocialService
from app.core.security import get_current_active_user
from app.database.models import User, ChatRoom, RoomParticipant

router = APIRouter()
logger = get_logger(__name__)


# WebSocket endpoint for real-time communication
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time messaging"""
    try:
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4004, reason="User not found")
            return
        
        # Handle WebSocket connection
        await realtime_service.handle_websocket_connection(
            websocket, user_id, user.username, db
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")


# Chat Room Management
@router.post("/rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat room"""
    try:
        import uuid
        
        # Generate room ID
        room_id = str(uuid.uuid4())
        
        # Create room
        room = ChatRoom(
            id=room_id,
            name=room_data.name,
            description=room_data.description,
            created_by=current_user.id,
            is_public=room_data.is_public,
            max_participants=room_data.max_participants,
            topic=room_data.topic,
            is_aeon_room=room_data.is_aeon_room
        )
        
        db.add(room)
        db.commit()
        db.refresh(room)
        
        # Add creator as first participant
        participant = RoomParticipant(
            room_id=room_id,
            user_id=current_user.id,
            is_active=True
        )
        db.add(participant)
        room.current_participants = 1
        db.commit()
        
        response = ChatRoomResponse.model_validate(room)
        response.participants = []
        
        logger.info(f"Created chat room '{room_data.name}' by user {current_user.username}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating chat room: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat room"
        )


@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_chat_rooms(
    is_public: Optional[bool] = Query(None, description="Filter by public/private rooms"),
    is_aeon_room: Optional[bool] = Query(None, description="Filter by AEON rooms"),
    limit: int = Query(50, description="Maximum number of rooms to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available chat rooms"""
    try:
        query = db.query(ChatRoom)
        
        if is_public is not None:
            query = query.filter(ChatRoom.is_public == is_public)
        
        if is_aeon_room is not None:
            query = query.filter(ChatRoom.is_aeon_room == is_aeon_room)
        
        rooms = query.limit(limit).all()
        
        result = []
        for room in rooms:
            # Get participants for each room
            participants = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room.id,
                    RoomParticipant.is_active == True
                )
            ).all()
            
            participant_data = []
            for participant in participants:
                user = db.query(User).filter(User.id == participant.user_id).first()
                if user:
                    participant_data.append(UserPresence(
                        user_id=user.id,
                        username=user.username,
                        current_room=room.id,
                        is_aeon=False
                    ))
            
            response = ChatRoomResponse.model_validate(room)
            response.participants = participant_data
            result.append(response)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting chat rooms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat rooms"
        )


@router.get("/rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific chat room details"""
    try:
        room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat room not found"
            )
        
        # Get participants
        participants = db.query(RoomParticipant).filter(
            and_(
                RoomParticipant.room_id == room_id,
                RoomParticipant.is_active == True
            )
        ).all()
        
        participant_data = []
        for participant in participants:
            user = db.query(User).filter(User.id == participant.user_id).first()
            if user:
                participant_data.append(UserPresence(
                    user_id=user.id,
                    username=user.username,
                    current_room=room_id,
                    is_aeon=False
                ))
        
        response = ChatRoomResponse.model_validate(room)
        response.participants = participant_data
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat room: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat room"
        )


# User Relationships
@router.post("/relationships", status_code=status.HTTP_201_CREATED)
async def create_user_relationship(
    relationship_data: UserRelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a user relationship"""
    try:
        relationship = SocialService.create_user_relationship(
            db, current_user.id, relationship_data
        )
        return relationship
        
    except Exception as e:
        logger.error(f"Error creating user relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user relationship"
        )


@router.get("/relationships")
async def get_user_relationships(
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user relationships"""
    try:
        relationships = SocialService.get_user_relationships(
            db, current_user.id, relationship_type
        )
        return relationships
        
    except Exception as e:
        logger.error(f"Error getting user relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user relationships"
        )


# Shared Knowledge
@router.post("/knowledge", status_code=status.HTTP_201_CREATED)
async def create_shared_knowledge(
    knowledge_data: SharedKnowledgeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create shared knowledge"""
    try:
        knowledge = SocialService.create_shared_knowledge(
            db, current_user.id, knowledge_data
        )
        return knowledge
        
    except Exception as e:
        logger.error(f"Error creating shared knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shared knowledge"
        )


@router.get("/knowledge")
async def get_shared_knowledge(
    knowledge_type: Optional[str] = Query(None, description="Filter by knowledge type"),
    visibility: str = Query("public", description="Visibility filter (public, friends, private)"),
    limit: int = Query(50, description="Maximum number of knowledge items to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get shared knowledge"""
    try:
        knowledge = SocialService.get_shared_knowledge(
            db, current_user.id, knowledge_type, visibility, limit
        )
        return knowledge
        
    except Exception as e:
        logger.error(f"Error getting shared knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get shared knowledge"
        )


@router.post("/knowledge/{knowledge_id}/upvote")
async def upvote_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upvote shared knowledge"""
    try:
        success = SocialService.upvote_knowledge(db, knowledge_id, current_user.id)
        if success:
            return {"message": "Knowledge upvoted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upvoting knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upvote knowledge"
        )


@router.post("/knowledge/{knowledge_id}/downvote")
async def downvote_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Downvote shared knowledge"""
    try:
        success = SocialService.downvote_knowledge(db, knowledge_id, current_user.id)
        if success:
            return {"message": "Knowledge downvoted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downvoting knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to downvote knowledge"
        )


# AEON Interactions
@router.post("/aeon/interactions", status_code=status.HTTP_201_CREATED)
async def create_aeon_interaction(
    interaction_data: AEONInteractionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create AEON-to-AEON interaction"""
    try:
        interaction = SocialService.create_aeon_interaction(
            db, current_user.id, interaction_data
        )
        return interaction
        
    except Exception as e:
        logger.error(f"Error creating AEON interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create AEON interaction"
        )


@router.get("/aeon/interactions")
async def get_aeon_interactions(
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    is_public: bool = Query(True, description="Filter by public/private interactions"),
    limit: int = Query(50, description="Maximum number of interactions to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AEON interactions"""
    try:
        interactions = SocialService.get_aeon_interactions(
            db, current_user.id, interaction_type, is_public, limit
        )
        return interactions
        
    except Exception as e:
        logger.error(f"Error getting AEON interactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AEON interactions"
        )


@router.post("/aeon/interactions/{interaction_id}/respond")
async def respond_to_aeon_interaction(
    interaction_id: int,
    response_content: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Respond to an AEON interaction"""
    try:
        success = SocialService.respond_to_aeon_interaction(
            db, interaction_id, response_content
        )
        if success:
            return {"message": "Response sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found or already responded to"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to AEON interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to AEON interaction"
        )


# Social Network
@router.get("/social/network")
async def get_social_network(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's social network information"""
    try:
        network = SocialService.get_social_network(db, current_user.id)
        return network
        
    except Exception as e:
        logger.error(f"Error getting social network: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get social network"
        )


@router.get("/social/similar-users")
async def find_similar_users(
    limit: int = Query(10, description="Maximum number of similar users to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Find users with similar interests"""
    try:
        similar_users = SocialService.find_similar_users(db, current_user.id, limit)
        return similar_users
        
    except Exception as e:
        logger.error(f"Error finding similar users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar users"
        )


@router.get("/social/active-users")
async def get_active_users(
    limit: int = Query(20, description="Maximum number of active users to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get most active users"""
    try:
        active_users = SocialService.get_active_users(db, limit)
        return active_users
        
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active users"
        )


# Health and Status
@router.get("/health/phase3")
async def get_phase3_health():
    """Get Phase 3 system health status"""
    try:
        return {
            "status": "healthy",
            "phase": "3",
            "features": {
                "real_time_messaging": "active",
                "chat_rooms": "active",
                "social_features": "active",
                "aeon_interactions": "active",
                "shared_knowledge": "active"
            },
            "websocket_connections": len(realtime_service.connection_manager.active_connections),
            "active_rooms": len(realtime_service.connection_manager.room_connections)
        }
        
    except Exception as e:
        logger.error(f"Error getting Phase 3 health: {e}")
        return {
            "status": "unhealthy",
            "phase": "3",
            "error": str(e)
        } 