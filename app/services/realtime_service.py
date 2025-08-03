"""
Real-time service for Phase 3 WebSocket communication and chat rooms
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.logging import get_logger
from app.database.models import (
    User, ChatRoom, RealTimeMessage, RoomParticipant, UserPresence
)
from app.models.aeon import (
    RealTimeMessage as RealTimeMessageModel,
    UserPresence as UserPresenceModel,
    ChatRoom as ChatRoomModel,
    ConnectionStatus
)

logger = get_logger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and real-time messaging"""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.room_connections: Dict[str, Set[int]] = {}
        self.user_presence: Dict[int, UserPresenceModel] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, username: str):
        """Connect a user to the WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Update user presence
        presence = UserPresenceModel(
            user_id=user_id,
            username=username,
            status=ConnectionStatus.CONNECTED,
            last_seen=datetime.utcnow(),
            is_aeon=False
        )
        self.user_presence[user_id] = presence
        
        # Notify others of user connection
        await self.broadcast_presence_update(presence, exclude_user=user_id)
        
        logger.info(f"User {username} (ID: {user_id}) connected")
    
    def disconnect(self, user_id: int):
        """Disconnect a user from the WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Update user presence
        if user_id in self.user_presence:
            self.user_presence[user_id].status = ConnectionStatus.DISCONNECTED
            self.user_presence[user_id].last_seen = datetime.utcnow()
        
        # Remove from all rooms
        for room_id in list(self.room_connections.keys()):
            if user_id in self.room_connections[room_id]:
                self.room_connections[room_id].discard(user_id)
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
        
        logger.info(f"User ID {user_id} disconnected")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send a personal message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending personal message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_room(self, message: str, room_id: str, exclude_user: Optional[int] = None):
        """Broadcast a message to all users in a room"""
        if room_id in self.room_connections:
            disconnected_users = []
            for user_id in self.room_connections[room_id]:
                if user_id != exclude_user:
                    try:
                        await self.active_connections[user_id].send_text(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
                        disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(user_id)
    
    async def broadcast_presence_update(self, presence: UserPresenceModel, exclude_user: Optional[int] = None):
        """Broadcast user presence update to all connected users"""
        message = {
            "type": "presence_update",
            "data": presence.model_dump()
        }
        
        for user_id in list(self.active_connections.keys()):
            if user_id != exclude_user:
                try:
                    await self.active_connections[user_id].send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting presence update to user {user_id}: {e}")
                    self.disconnect(user_id)


class RealTimeService:
    """Service for managing real-time messaging and chat rooms"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
    
    async def handle_websocket_connection(
        self, 
        websocket: WebSocket, 
        user_id: int, 
        username: str,
        db: Session
    ):
        """Handle WebSocket connection for a user"""
        try:
            await self.connection_manager.connect(websocket, user_id, username)
            
            # Update database presence
            await self.update_user_presence(db, user_id, ConnectionStatus.CONNECTED)
            
            # Send current room participants
            await self.send_room_participants(user_id, db)
            
            # Main message loop
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    await self.handle_message(message_data, user_id, username, db)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling message from user {user_id}: {e}")
                    await self.send_error_message(user_id, "Error processing message")
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            self.connection_manager.disconnect(user_id)
            await self.update_user_presence(db, user_id, ConnectionStatus.DISCONNECTED)
    
    async def handle_message(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle incoming WebSocket message"""
        message_type = message_data.get("type")
        
        if message_type == "chat_message":
            await self.handle_chat_message(message_data, user_id, username, db)
        elif message_type == "join_room":
            await self.handle_join_room(message_data, user_id, username, db)
        elif message_type == "leave_room":
            await self.handle_leave_room(message_data, user_id, username, db)
        elif message_type == "typing":
            await self.handle_typing(message_data, user_id, username, db)
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def handle_chat_message(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle chat message"""
        content = message_data.get("content", "")
        room_id = message_data.get("room_id")
        message_type = message_data.get("message_type", "text")
        
        if not content or not room_id:
            await self.send_error_message(user_id, "Invalid message format")
            return
        
        # Create message ID
        message_id = str(uuid.uuid4())
        
        # Save to database
        db_message = RealTimeMessage(
            id=message_id,
            sender_id=user_id,
            content=content,
            message_type=message_type,
            room_id=room_id,
            is_aeon_message=False,
            meta_data=message_data.get("meta_data")
        )
        db.add(db_message)
        db.commit()
        
        # Create response message
        response_message = RealTimeMessageModel(
            message_id=message_id,
            sender_id=user_id,
            sender_name=username,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
            room_id=room_id,
            is_aeon_message=False,
            meta_data=message_data.get("meta_data")
        )
        
        # Broadcast to room
        message_json = {
            "type": "chat_message",
            "data": response_message.model_dump()
        }
        await self.connection_manager.broadcast_to_room(
            json.dumps(message_json), 
            room_id, 
            exclude_user=user_id
        )
        
        logger.info(f"Message sent by {username} in room {room_id}")
    
    async def handle_join_room(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle join room request"""
        room_id = message_data.get("room_id")
        
        if not room_id:
            await self.send_error_message(user_id, "Room ID required")
            return
        
        # Check if room exists
        room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room:
            await self.send_error_message(user_id, "Room not found")
            return
        
        # Check if user is already in room
        existing_participant = db.query(RoomParticipant).filter(
            and_(
                RoomParticipant.room_id == room_id,
                RoomParticipant.user_id == user_id,
                RoomParticipant.is_active == True
            )
        ).first()
        
        if existing_participant:
            await self.send_error_message(user_id, "Already in room")
            return
        
        # Add user to room
        participant = RoomParticipant(
            room_id=room_id,
            user_id=user_id,
            is_active=True
        )
        db.add(participant)
        
        # Update room participant count
        room.current_participants += 1
        db.commit()
        
        # Add to connection manager
        if room_id not in self.connection_manager.room_connections:
            self.connection_manager.room_connections[room_id] = set()
        self.connection_manager.room_connections[room_id].add(user_id)
        
        # Update user presence
        if user_id in self.connection_manager.user_presence:
            self.connection_manager.user_presence[user_id].current_room = room_id
        
        # Notify room of new participant
        join_message = {
            "type": "user_joined",
            "data": {
                "user_id": user_id,
                "username": username,
                "room_id": room_id
            }
        }
        await self.connection_manager.broadcast_to_room(
            json.dumps(join_message), 
            room_id, 
            exclude_user=user_id
        )
        
        # Send room info to user
        await self.send_room_info(user_id, room_id, db)
        
        logger.info(f"User {username} joined room {room_id}")
    
    async def handle_leave_room(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle leave room request"""
        room_id = message_data.get("room_id")
        
        if not room_id:
            await self.send_error_message(user_id, "Room ID required")
            return
        
        # Remove from database
        participant = db.query(RoomParticipant).filter(
            and_(
                RoomParticipant.room_id == room_id,
                RoomParticipant.user_id == user_id,
                RoomParticipant.is_active == True
            )
        ).first()
        
        if participant:
            participant.is_active = False
            participant.last_activity = datetime.utcnow()
            
            # Update room participant count
            room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
            if room and room.current_participants > 0:
                room.current_participants -= 1
            
            db.commit()
        
        # Remove from connection manager
        if room_id in self.connection_manager.room_connections:
            self.connection_manager.room_connections[room_id].discard(user_id)
            if not self.connection_manager.room_connections[room_id]:
                del self.connection_manager.room_connections[room_id]
        
        # Update user presence
        if user_id in self.connection_manager.user_presence:
            self.connection_manager.user_presence[user_id].current_room = None
        
        # Notify room of departure
        leave_message = {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "username": username,
                "room_id": room_id
            }
        }
        await self.connection_manager.broadcast_to_room(
            json.dumps(leave_message), 
            room_id, 
            exclude_user=user_id
        )
        
        logger.info(f"User {username} left room {room_id}")
    
    async def handle_typing(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle typing indicator"""
        room_id = message_data.get("room_id")
        is_typing = message_data.get("is_typing", False)
        
        if not room_id:
            return
        
        # Update user presence
        if user_id in self.connection_manager.user_presence:
            status = ConnectionStatus.TYPING if is_typing else ConnectionStatus.CONNECTED
            self.connection_manager.user_presence[user_id].status = status
        
        # Broadcast typing indicator
        typing_message = {
            "type": "typing_indicator",
            "data": {
                "user_id": user_id,
                "username": username,
                "room_id": room_id,
                "is_typing": is_typing
            }
        }
        await self.connection_manager.broadcast_to_room(
            json.dumps(typing_message), 
            room_id, 
            exclude_user=user_id
        )
    
    async def send_error_message(self, user_id: int, error_message: str):
        """Send error message to user"""
        error_data = {
            "type": "error",
            "data": {
                "message": error_message
            }
        }
        await self.connection_manager.send_personal_message(
            json.dumps(error_data), 
            user_id
        )
    
    async def send_room_info(self, user_id: int, room_id: str, db: Session):
        """Send room information to user"""
        room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room:
            return
        
        room_info = {
            "type": "room_info",
            "data": {
                "room_id": room.id,
                "name": room.name,
                "description": room.description,
                "topic": room.topic,
                "current_participants": room.current_participants,
                "max_participants": room.max_participants,
                "is_aeon_room": room.is_aeon_room
            }
        }
        await self.connection_manager.send_personal_message(
            json.dumps(room_info), 
            user_id
        )
    
    async def send_room_participants(self, user_id: int, db: Session):
        """Send current room participants to user"""
        # Get all active participants
        participants = db.query(RoomParticipant).filter(
            RoomParticipant.is_active == True
        ).all()
        
        participant_data = []
        for participant in participants:
            user = db.query(User).filter(User.id == participant.user_id).first()
            if user:
                participant_data.append({
                    "user_id": user.id,
                    "username": user.username,
                    "room_id": participant.room_id,
                    "joined_at": participant.joined_at.isoformat()
                })
        
        participants_message = {
            "type": "room_participants",
            "data": participant_data
        }
        await self.connection_manager.send_personal_message(
            json.dumps(participants_message), 
            user_id
        )
    
    async def update_user_presence(self, db: Session, user_id: int, status: ConnectionStatus):
        """Update user presence in database"""
        try:
            presence = db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
            
            if presence:
                presence.status = status.value
                presence.last_seen = datetime.utcnow()
            else:
                presence = UserPresence(
                    user_id=user_id,
                    status=status.value,
                    last_seen=datetime.utcnow(),
                    is_aeon=False
                )
                db.add(presence)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error updating user presence: {e}")
            db.rollback()


# Global instance
realtime_service = RealTimeService() 