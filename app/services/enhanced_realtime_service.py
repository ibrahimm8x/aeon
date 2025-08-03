"""
Enhanced real-time service for AEON with email and web activity integration
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.email_service import email_service, EmailMessage
from app.services.web_activity_service import web_activity_tracker, WebActivity, WebSession
from app.services.realtime_service import ConnectionManager, RealTimeService
from app.database.models import User

logger = get_logger(__name__)


class EnhancedConnectionManager(ConnectionManager):
    """Enhanced connection manager with email and web activity tracking"""
    
    def __init__(self):
        super().__init__()
        self.user_email_configs: Dict[int, Dict] = {}
        self.user_activity_sessions: Dict[int, Dict] = {}
        self.activity_monitoring_tasks: Dict[int, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, username: str):
        """Connect a user and start monitoring their activities"""
        await super().connect(websocket, user_id, username)
        
        # Start activity monitoring
        await self.start_activity_monitoring(user_id)
        
        logger.info(f"Enhanced connection established for user {username} (ID: {user_id})")
    
    def disconnect(self, user_id: int):
        """Disconnect a user and stop monitoring"""
        # Stop activity monitoring
        self.stop_activity_monitoring(user_id)
        
        # End web session
        asyncio.create_task(web_activity_tracker.end_session(user_id))
        
        super().disconnect(user_id)
        
        logger.info(f"Enhanced disconnection for user {user_id}")
    
    async def start_activity_monitoring(self, user_id: int):
        """Start monitoring user's email and web activities"""
        if user_id in self.activity_monitoring_tasks:
            return
        
        # Create monitoring task
        task = asyncio.create_task(self._monitor_user_activities(user_id))
        self.activity_monitoring_tasks[user_id] = task
        
        logger.info(f"Started activity monitoring for user {user_id}")
    
    def stop_activity_monitoring(self, user_id: int):
        """Stop monitoring user's activities"""
        if user_id in self.activity_monitoring_tasks:
            self.activity_monitoring_tasks[user_id].cancel()
            del self.activity_monitoring_tasks[user_id]
            
            logger.info(f"Stopped activity monitoring for user {user_id}")
    
    async def _monitor_user_activities(self, user_id: int):
        """Monitor user's email and web activities in real-time"""
        try:
            while user_id in self.active_connections:
                # Check for new emails (every 5 minutes)
                if user_id in self.user_email_configs:
                    await self._check_new_emails(user_id)
                
                # Check for web activity updates (every 30 seconds)
                await self._check_web_activity_updates(user_id)
                
                # Wait before next check
                await asyncio.sleep(30)
                
        except asyncio.CancelledError:
            logger.info(f"Activity monitoring cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Error in activity monitoring for user {user_id}: {str(e)}")
    
    async def _check_new_emails(self, user_id: int):
        """Check for new emails and notify user"""
        try:
            # Fetch recent unread emails
            emails = await email_service.fetch_recent_emails(
                folder="INBOX",
                limit=10,
                days_back=1,
                include_read=False
            )
            
            if emails:
                # Send email summary to user
                await self._send_email_summary(user_id, emails)
                
                # Check for urgent emails
                urgent_emails = [e for e in emails if e.importance >= 4]
                if urgent_emails:
                    await self._send_urgent_email_alert(user_id, urgent_emails)
                    
        except Exception as e:
            logger.error(f"Error checking emails for user {user_id}: {str(e)}")
    
    async def _check_web_activity_updates(self, user_id: int):
        """Check for web activity updates and provide insights"""
        try:
            # Get recent activity summary
            summary = await web_activity_tracker.get_user_activity_summary(user_id, days=1)
            
            # Send activity insights if significant
            if summary["total_activities"] > 10:
                await self._send_activity_insights(user_id, summary)
            
            # Check for productivity patterns
            if summary["productivity_score"] < 30:
                await self._send_productivity_reminder(user_id, summary)
                
        except Exception as e:
            logger.error(f"Error checking web activity for user {user_id}: {str(e)}")
    
    async def _send_email_summary(self, user_id: int, emails: List[EmailMessage]):
        """Send email summary to user"""
        if user_id not in self.active_connections:
            return
        
        summary = {
            "type": "email_summary",
            "data": {
                "total_emails": len(emails),
                "unread_count": len([e for e in emails if not e.is_read]),
                "important_count": len([e for e in emails if e.importance >= 4]),
                "top_senders": {},
                "recent_emails": [
                    {
                        "subject": email.subject,
                        "sender": email.sender,
                        "importance": email.importance,
                        "sentiment": email.sentiment,
                        "timestamp": email.timestamp.isoformat()
                    }
                    for email in emails[:5]
                ]
            }
        }
        
        try:
            await self.active_connections[user_id].send_text(json.dumps(summary))
        except Exception as e:
            logger.error(f"Error sending email summary to user {user_id}: {str(e)}")
    
    async def _send_urgent_email_alert(self, user_id: int, urgent_emails: List[EmailMessage]):
        """Send urgent email alert to user"""
        if user_id not in self.active_connections:
            return
        
        alert = {
            "type": "urgent_email_alert",
            "data": {
                "message": f"You have {len(urgent_emails)} urgent emails",
                "emails": [
                    {
                        "subject": email.subject,
                        "sender": email.sender,
                        "importance": email.importance
                    }
                    for email in urgent_emails
                ]
            }
        }
        
        try:
            await self.active_connections[user_id].send_text(json.dumps(alert))
        except Exception as e:
            logger.error(f"Error sending urgent email alert to user {user_id}: {str(e)}")
    
    async def _send_activity_insights(self, user_id: int, summary: Dict[str, Any]):
        """Send web activity insights to user"""
        if user_id not in self.active_connections:
            return
        
        insights = {
            "type": "activity_insights",
            "data": {
                "total_activities": summary["total_activities"],
                "productivity_score": summary["productivity_score"],
                "top_topics": summary["top_topics"],
                "domains_visited": len(summary["domains_visited"]),
                "recommendations": await web_activity_tracker.get_recommendations(user_id)
            }
        }
        
        try:
            await self.active_connections[user_id].send_text(json.dumps(insights))
        except Exception as e:
            logger.error(f"Error sending activity insights to user {user_id}: {str(e)}")
    
    async def _send_productivity_reminder(self, user_id: int, summary: Dict[str, Any]):
        """Send productivity reminder to user"""
        if user_id not in self.active_connections:
            return
        
        reminder = {
            "type": "productivity_reminder",
            "data": {
                "message": "Your productivity score is low. Consider focusing on work-related activities.",
                "productivity_score": summary["productivity_score"],
                "suggestions": [
                    "Switch to work-related websites",
                    "Take a break from social media",
                    "Focus on learning activities"
                ]
            }
        }
        
        try:
            await self.active_connections[user_id].send_text(json.dumps(reminder))
        except Exception as e:
            logger.error(f"Error sending productivity reminder to user {user_id}: {str(e)}")
    
    async def handle_web_activity_event(self, user_id: int, activity_data: Dict[str, Any]):
        """Handle web activity events from browser extension"""
        try:
            activity_type = activity_data.get("type")
            
            if activity_type == "page_view":
                activity = await web_activity_tracker.track_page_view(
                    user_id=user_id,
                    url=activity_data["url"],
                    title=activity_data["title"],
                    referrer=activity_data.get("referrer"),
                    user_agent=activity_data.get("user_agent"),
                    duration=activity_data.get("duration")
                )
                
            elif activity_type == "search":
                activity = await web_activity_tracker.track_search(
                    user_id=user_id,
                    search_query=activity_data["query"],
                    search_engine=activity_data["engine"],
                    results_count=activity_data.get("results_count")
                )
                
            elif activity_type == "click":
                activity = await web_activity_tracker.track_click(
                    user_id=user_id,
                    url=activity_data["url"],
                    element_type=activity_data["element_type"],
                    element_text=activity_data.get("element_text")
                )
            
            # Send confirmation back to user
            if user_id in self.active_connections:
                confirmation = {
                    "type": "activity_tracked",
                    "data": {
                        "activity_type": activity_type,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                await self.active_connections[user_id].send_text(json.dumps(confirmation))
                
        except Exception as e:
            logger.error(f"Error handling web activity event for user {user_id}: {str(e)}")
    
    async def configure_email_access(self, user_id: int, email_config: Dict[str, Any]):
        """Configure email access for a user"""
        try:
            await email_service.configure_email_access(
                email_address=email_config["email"],
                password=email_config["password"],
                imap_server=email_config.get("imap_server", "imap.gmail.com"),
                imap_port=email_config.get("imap_port", 993),
                smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_config.get("smtp_port", 587)
            )
            
            self.user_email_configs[user_id] = email_config
            
            # Send confirmation
            if user_id in self.active_connections:
                confirmation = {
                    "type": "email_configured",
                    "data": {
                        "email": email_config["email"],
                        "status": "success"
                    }
                }
                await self.active_connections[user_id].send_text(json.dumps(confirmation))
                
        except Exception as e:
            logger.error(f"Error configuring email for user {user_id}: {str(e)}")
            
            # Send error notification
            if user_id in self.active_connections:
                error_msg = {
                    "type": "email_config_error",
                    "data": {
                        "error": str(e)
                    }
                }
                await self.active_connections[user_id].send_text(json.dumps(error_msg))


class EnhancedRealTimeService(RealTimeService):
    """Enhanced real-time service with email and web activity integration"""
    
    def __init__(self):
        super().__init__()
        self.connection_manager = EnhancedConnectionManager()
    
    async def handle_websocket_connection(
        self, 
        websocket: WebSocket, 
        user_id: int, 
        username: str,
        db: Session
    ):
        """Handle enhanced WebSocket connection"""
        try:
            await self.connection_manager.connect(websocket, user_id, username)
            
            # Send initial status
            await self._send_initial_status(user_id, db)
            
            # Main message loop
            while True:
                try:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    await self._handle_enhanced_message(message_data, user_id, username, db)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling enhanced message from user {user_id}: {e}")
                    await self.send_error_message(user_id, "Error processing message")
        
        except WebSocketDisconnect:
            logger.info(f"Enhanced WebSocket disconnected for user {user_id}")
        except Exception as e:
            logger.error(f"Enhanced WebSocket error for user {user_id}: {e}")
        finally:
            self.connection_manager.disconnect(user_id)
    
    async def _send_initial_status(self, user_id: int, db: Session):
        """Send initial status including email and web activity summary"""
        try:
            # Get email summary if configured
            email_summary = None
            if user_id in self.connection_manager.user_email_configs:
                email_summary = await email_service.get_email_summary(days=1)
            
            # Get web activity summary
            web_summary = await web_activity_tracker.get_user_activity_summary(user_id, days=1)
            
            # Send combined status
            status = {
                "type": "initial_status",
                "data": {
                    "email_summary": email_summary,
                    "web_activity_summary": web_summary,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            if user_id in self.connection_manager.active_connections:
                await self.connection_manager.active_connections[user_id].send_text(json.dumps(status))
                
        except Exception as e:
            logger.error(f"Error sending initial status to user {user_id}: {str(e)}")
    
    async def _handle_enhanced_message(self, message_data: Dict[str, Any], user_id: int, username: str, db: Session):
        """Handle enhanced message types"""
        message_type = message_data.get("type")
        
        if message_type == "web_activity":
            await self.connection_manager.handle_web_activity_event(user_id, message_data.get("data", {}))
        elif message_type == "configure_email":
            await self.connection_manager.configure_email_access(user_id, message_data.get("data", {}))
        elif message_type == "get_email_summary":
            await self._handle_email_summary_request(user_id, message_data.get("data", {}))
        elif message_type == "get_activity_summary":
            await self._handle_activity_summary_request(user_id, message_data.get("data", {}))
        else:
            # Handle standard message types
            await super().handle_message(message_data, user_id, username, db)
    
    async def _handle_email_summary_request(self, user_id: int, data: Dict[str, Any]):
        """Handle email summary request"""
        try:
            days = data.get("days", 7)
            summary = await email_service.get_email_summary(days=days)
            
            response = {
                "type": "email_summary_response",
                "data": summary
            }
            
            if user_id in self.connection_manager.active_connections:
                await self.connection_manager.active_connections[user_id].send_text(json.dumps(response))
                
        except Exception as e:
            logger.error(f"Error handling email summary request for user {user_id}: {str(e)}")
    
    async def _handle_activity_summary_request(self, user_id: int, data: Dict[str, Any]):
        """Handle activity summary request"""
        try:
            days = data.get("days", 7)
            summary = await web_activity_tracker.get_user_activity_summary(user_id, days=days)
            
            response = {
                "type": "activity_summary_response",
                "data": summary
            }
            
            if user_id in self.connection_manager.active_connections:
                await self.connection_manager.active_connections[user_id].send_text(json.dumps(response))
                
        except Exception as e:
            logger.error(f"Error handling activity summary request for user {user_id}: {str(e)}")


# Global enhanced real-time service instance
enhanced_realtime_service = EnhancedRealTimeService() 