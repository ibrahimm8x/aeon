"""
Enhanced AEON endpoints for email and web activity integration
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.logging import get_logger
from app.database import get_db
from app.services.email_service import email_service, EmailMessage
from app.services.web_activity_service import web_activity_tracker, WebActivity, WebSession
from app.services.enhanced_realtime_service import enhanced_realtime_service
from app.core.security import get_current_active_user
from app.database.models import User, EmailConfig, WebActivity as WebActivityModel, WebSession as WebSessionModel

router = APIRouter()
logger = get_logger(__name__)


# Email Integration Endpoints

@router.post("/email/configure")
async def configure_email_access(
    email_config: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Configure email access for the user"""
    try:
        # Configure email service
        success = await email_service.configure_email_access(
            email_address=email_config["email"],
            password=email_config["password"],
            imap_server=email_config.get("imap_server", "imap.gmail.com"),
            imap_port=email_config.get("imap_port", 993),
            smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
            smtp_port=email_config.get("smtp_port", 587)
        )
        
        if success:
            # Save configuration to database
            db_config = EmailConfig(
                user_id=current_user.id,
                email_address=email_config["email"],
                imap_server=email_config.get("imap_server", "imap.gmail.com"),
                imap_port=email_config.get("imap_port", 993),
                smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_config.get("smtp_port", 587)
            )
            db.add(db_config)
            db.commit()
            
            return {"status": "success", "message": "Email access configured successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to configure email access"
            )
            
    except Exception as e:
        logger.error(f"Error configuring email for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure email access"
        )


@router.get("/email/summary")
async def get_email_summary(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get email summary for the user"""
    try:
        # Check if user has email configured
        email_config = db.query(EmailConfig).filter(
            EmailConfig.user_id == current_user.id,
            EmailConfig.is_active == True
        ).first()
        
        if not email_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not configured for this user"
            )
        
        # Configure email service with stored config
        await email_service.configure_email_access(
            email_address=email_config.email_address,
            password="",  # Password should be stored securely
            imap_server=email_config.imap_server,
            imap_port=email_config.imap_port,
            smtp_server=email_config.smtp_server,
            smtp_port=email_config.smtp_port
        )
        
        # Get email summary
        summary = await email_service.get_email_summary(days=days)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get email summary"
        )


@router.get("/email/recent")
async def get_recent_emails(
    limit: int = Query(20, description="Number of emails to fetch"),
    folder: str = Query("INBOX", description="Email folder to fetch from"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent emails for the user"""
    try:
        # Check if user has email configured
        email_config = db.query(EmailConfig).filter(
            EmailConfig.user_id == current_user.id,
            EmailConfig.is_active == True
        ).first()
        
        if not email_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not configured for this user"
            )
        
        # Configure email service
        await email_service.configure_email_access(
            email_address=email_config.email_address,
            password="",  # Password should be stored securely
            imap_server=email_config.imap_server,
            imap_port=email_config.imap_port,
            smtp_server=email_config.smtp_server,
            smtp_port=email_config.smtp_port
        )
        
        # Fetch recent emails
        emails = await email_service.fetch_recent_emails(
            folder=folder,
            limit=limit,
            days_back=7,
            include_read=True
        )
        
        # Convert to response format
        email_list = []
        for email in emails:
            email_list.append({
                "id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "timestamp": email.timestamp.isoformat(),
                "is_read": email.is_read,
                "importance": email.importance,
                "sentiment": email.sentiment,
                "topics": email.extracted_entities.get("topics", []) if email.extracted_entities else []
            })
        
        return {"emails": email_list}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent emails for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent emails"
        )


# Web Activity Endpoints

@router.get("/web-activity/summary")
async def get_web_activity_summary(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get web activity summary for the user"""
    try:
        summary = await web_activity_tracker.get_user_activity_summary(
            user_id=current_user.id,
            days=days
        )
        return summary
        
    except Exception as e:
        logger.error(f"Error getting web activity summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get web activity summary"
        )


@router.get("/web-activity/recent")
async def get_recent_web_activities(
    limit: int = Query(50, description="Number of activities to fetch"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent web activities for the user"""
    try:
        # Get activities from database
        query = db.query(WebActivityModel).filter(
            WebActivityModel.user_id == current_user.id
        )
        
        if activity_type:
            query = query.filter(WebActivityModel.activity_type == activity_type)
        
        activities = query.order_by(WebActivityModel.timestamp.desc()).limit(limit).all()
        
        # Convert to response format
        activity_list = []
        for activity in activities:
            activity_list.append({
                "id": activity.id,
                "url": activity.url,
                "domain": activity.domain,
                "title": activity.title,
                "activity_type": activity.activity_type,
                "timestamp": activity.timestamp.isoformat(),
                "duration": activity.duration,
                "topics": activity.topics,
                "importance": activity.importance,
                "sentiment": activity.sentiment
            })
        
        return {"activities": activity_list}
        
    except Exception as e:
        logger.error(f"Error getting recent web activities for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent web activities"
        )


@router.get("/web-activity/recommendations")
async def get_web_activity_recommendations(
    based_on: str = Query("recent_activity", description="Basis for recommendations"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personalized recommendations based on web activity"""
    try:
        recommendations = await web_activity_tracker.get_recommendations(
            user_id=current_user.id,
            based_on=based_on
        )
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.post("/web-activity/track")
async def track_web_activity(
    activity_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Track a web activity event"""
    try:
        activity_type = activity_data.get("type")
        
        if activity_type == "page_view":
            activity = await web_activity_tracker.track_page_view(
                user_id=current_user.id,
                url=activity_data["url"],
                title=activity_data["title"],
                referrer=activity_data.get("referrer"),
                user_agent=activity_data.get("user_agent"),
                duration=activity_data.get("duration")
            )
            
        elif activity_type == "search":
            activity = await web_activity_tracker.track_search(
                user_id=current_user.id,
                search_query=activity_data["query"],
                search_engine=activity_data["engine"],
                results_count=activity_data.get("results_count")
            )
            
        elif activity_type == "click":
            activity = await web_activity_tracker.track_click(
                user_id=current_user.id,
                url=activity_data["url"],
                element_type=activity_data["element_type"],
                element_text=activity_data.get("element_text")
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported activity type: {activity_type}"
            )
        
        return {"status": "success", "activity_id": activity.id if activity else None}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking web activity for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track web activity"
        )


# Enhanced WebSocket Endpoint

@router.websocket("/ws/enhanced/{user_id}")
async def enhanced_websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Enhanced WebSocket endpoint with email and web activity integration"""
    try:
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4004, reason="User not found")
            return
        
        # Handle enhanced WebSocket connection
        await enhanced_realtime_service.handle_websocket_connection(
            websocket, user_id, user.username, db
        )
    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")


# Combined Analytics Endpoint

@router.get("/analytics/combined")
async def get_combined_analytics(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get combined analytics from email and web activity"""
    try:
        analytics = {
            "user_id": current_user.id,
            "analysis_period": f"Last {days} days",
            "timestamp": datetime.now().isoformat(),
            "email_analytics": None,
            "web_activity_analytics": None,
            "productivity_insights": {},
            "recommendations": []
        }
        
        # Get email analytics if configured
        email_config = db.query(EmailConfig).filter(
            EmailConfig.user_id == current_user.id,
            EmailConfig.is_active == True
        ).first()
        
        if email_config:
            try:
                await email_service.configure_email_access(
                    email_address=email_config.email_address,
                    password="",
                    imap_server=email_config.imap_server,
                    imap_port=email_config.imap_port,
                    smtp_server=email_config.smtp_server,
                    smtp_port=email_config.smtp_port
                )
                analytics["email_analytics"] = await email_service.get_email_summary(days=days)
            except Exception as e:
                logger.error(f"Error getting email analytics: {str(e)}")
                analytics["email_analytics"] = {"error": "Failed to fetch email data"}
        
        # Get web activity analytics
        try:
            analytics["web_activity_analytics"] = await web_activity_tracker.get_user_activity_summary(
                user_id=current_user.id,
                days=days
            )
        except Exception as e:
            logger.error(f"Error getting web activity analytics: {str(e)}")
            analytics["web_activity_analytics"] = {"error": "Failed to fetch web activity data"}
        
        # Generate productivity insights
        if analytics["web_activity_analytics"] and "productivity_score" in analytics["web_activity_analytics"]:
            productivity_score = analytics["web_activity_analytics"]["productivity_score"]
            
            if productivity_score >= 80:
                analytics["productivity_insights"]["status"] = "excellent"
                analytics["productivity_insights"]["message"] = "You're being very productive!"
            elif productivity_score >= 60:
                analytics["productivity_insights"]["status"] = "good"
                analytics["productivity_insights"]["message"] = "Good productivity level"
            elif productivity_score >= 40:
                analytics["productivity_insights"]["status"] = "moderate"
                analytics["productivity_insights"]["message"] = "Consider focusing more on work-related activities"
            else:
                analytics["productivity_insights"]["status"] = "needs_improvement"
                analytics["productivity_insights"]["message"] = "Try to reduce distractions and focus on productive tasks"
        
        # Get recommendations
        try:
            recommendations = await web_activity_tracker.get_recommendations(
                user_id=current_user.id,
                based_on="recent_activity"
            )
            analytics["recommendations"] = recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting combined analytics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get combined analytics"
        ) 