"""
Web activity tracking service for AEON to monitor user's internet activity
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from urllib.parse import urlparse, parse_qs
import hashlib

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class WebActivity:
    """Web activity data structure"""
    id: str
    user_id: int
    url: str
    domain: str
    title: str
    activity_type: str  # page_view, search, click, form_submit, etc.
    timestamp: datetime
    duration: Optional[int] = None  # seconds spent on page
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    meta_data: Optional[Dict] = None
    extracted_content: Optional[str] = None
    sentiment: Optional[str] = None
    topics: Optional[List[str]] = None
    importance: int = 1  # 1-5 scale


@dataclass
class WebSession:
    """Web browsing session"""
    id: str
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    total_pages: int = 0
    total_duration: int = 0
    domains_visited: Set[str] = None
    primary_topics: List[str] = None
    session_type: str = "general"  # work, personal, research, etc.


class WebActivityTracker:
    """Real-time web activity tracker"""
    
    def __init__(self):
        self.active_sessions: Dict[int, WebSession] = {}
        self.activity_buffer: List[WebActivity] = []
        self.domain_categories = self._load_domain_categories()
        self.topic_keywords = self._load_topic_keywords()
    
    def _load_domain_categories(self) -> Dict[str, str]:
        """Load domain categories for classification"""
        return {
            # Social Media
            "facebook.com": "social_media",
            "twitter.com": "social_media",
            "instagram.com": "social_media",
            "linkedin.com": "social_media",
            "reddit.com": "social_media",
            "tiktok.com": "social_media",
            
            # Work/Professional
            "github.com": "development",
            "stackoverflow.com": "development",
            "gitlab.com": "development",
            "jira.com": "project_management",
            "confluence.com": "project_management",
            "slack.com": "communication",
            "teams.microsoft.com": "communication",
            "zoom.us": "communication",
            
            # News/Information
            "news.ycombinator.com": "news",
            "techcrunch.com": "news",
            "wired.com": "news",
            "theverge.com": "news",
            "bbc.com": "news",
            "cnn.com": "news",
            
            # Shopping
            "amazon.com": "shopping",
            "ebay.com": "shopping",
            "etsy.com": "shopping",
            
            # Entertainment
            "youtube.com": "entertainment",
            "netflix.com": "entertainment",
            "spotify.com": "entertainment",
            "twitch.tv": "entertainment",
            
            # Learning
            "coursera.org": "learning",
            "udemy.com": "learning",
            "khanacademy.org": "learning",
            "w3schools.com": "learning",
            "freecodecamp.org": "learning"
        }
    
    def _load_topic_keywords(self) -> Dict[str, List[str]]:
        """Load topic keywords for classification"""
        return {
            "technology": ["programming", "software", "hardware", "ai", "machine learning", "data science", "cybersecurity"],
            "business": ["startup", "entrepreneurship", "marketing", "finance", "investment", "strategy"],
            "health": ["fitness", "nutrition", "medical", "wellness", "exercise", "diet"],
            "education": ["learning", "course", "tutorial", "study", "academic", "research"],
            "entertainment": ["movie", "music", "game", "streaming", "podcast", "comedy"],
            "news": ["politics", "world", "local", "breaking", "update", "current events"],
            "shopping": ["buy", "purchase", "product", "review", "price", "deal"],
            "travel": ["vacation", "trip", "hotel", "flight", "destination", "tourism"]
        }
    
    async def track_page_view(
        self,
        user_id: int,
        url: str,
        title: str,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        duration: Optional[int] = None
    ) -> WebActivity:
        """Track a page view activity"""
        try:
            # Parse URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Generate activity ID
            activity_id = hashlib.md5(f"{user_id}_{url}_{time.time()}".encode()).hexdigest()
            
            # Analyze content and extract metadata
            content_analysis = await self._analyze_page_content(title, url, domain)
            
            # Create activity record
            activity = WebActivity(
                id=activity_id,
                user_id=user_id,
                url=url,
                domain=domain,
                title=title,
                activity_type="page_view",
                timestamp=datetime.now(),
                duration=duration,
                referrer=referrer,
                user_agent=user_agent,
                ip_address=ip_address,
                meta_data=content_analysis,
                extracted_content=content_analysis.get("extracted_content"),
                sentiment=content_analysis.get("sentiment"),
                topics=content_analysis.get("topics"),
                importance=content_analysis.get("importance", 1)
            )
            
            # Add to buffer
            self.activity_buffer.append(activity)
            
            # Update active session
            await self._update_session(user_id, activity)
            
            logger.info(f"Tracked page view: {domain} - {title}")
            return activity
            
        except Exception as e:
            logger.error(f"Error tracking page view: {str(e)}")
            return None
    
    async def track_search(
        self,
        user_id: int,
        search_query: str,
        search_engine: str,
        results_count: Optional[int] = None
    ) -> WebActivity:
        """Track a search activity"""
        try:
            # Generate activity ID
            activity_id = hashlib.md5(f"{user_id}_search_{time.time()}".encode()).hexdigest()
            
            # Analyze search query
            query_analysis = await self._analyze_search_query(search_query)
            
            # Create activity record
            activity = WebActivity(
                id=activity_id,
                user_id=user_id,
                url=f"search://{search_engine}",
                domain=search_engine,
                title=f"Search: {search_query}",
                activity_type="search",
                timestamp=datetime.now(),
                meta_data={
                    "search_query": search_query,
                    "search_engine": search_engine,
                    "results_count": results_count,
                    "query_topics": query_analysis.get("topics"),
                    "query_intent": query_analysis.get("intent")
                },
                topics=query_analysis.get("topics"),
                importance=query_analysis.get("importance", 2)
            )
            
            # Add to buffer
            self.activity_buffer.append(activity)
            
            logger.info(f"Tracked search: {search_query} on {search_engine}")
            return activity
            
        except Exception as e:
            logger.error(f"Error tracking search: {str(e)}")
            return None
    
    async def track_click(
        self,
        user_id: int,
        url: str,
        element_type: str,
        element_text: Optional[str] = None
    ) -> WebActivity:
        """Track a click activity"""
        try:
            # Generate activity ID
            activity_id = hashlib.md5(f"{user_id}_click_{time.time()}".encode()).hexdigest()
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Create activity record
            activity = WebActivity(
                id=activity_id,
                user_id=user_id,
                url=url,
                domain=domain,
                title=f"Click: {element_type}",
                activity_type="click",
                timestamp=datetime.now(),
                meta_data={
                    "element_type": element_type,
                    "element_text": element_text
                }
            )
            
            # Add to buffer
            self.activity_buffer.append(activity)
            
            return activity
            
        except Exception as e:
            logger.error(f"Error tracking click: {str(e)}")
            return None
    
    async def _analyze_page_content(self, title: str, url: str, domain: str) -> Dict[str, Any]:
        """Analyze page content for topics, sentiment, and importance"""
        analysis = {
            "domain_category": self.domain_categories.get(domain, "general"),
            "topics": [],
            "sentiment": "neutral",
            "importance": 1,
            "extracted_content": title
        }
        
        # Extract topics from title and domain
        text_to_analyze = f"{title} {domain}".lower()
        
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                analysis["topics"].append(topic)
        
        # Determine importance based on domain and content
        if analysis["domain_category"] in ["work", "development", "project_management"]:
            analysis["importance"] = 4
        elif analysis["domain_category"] in ["social_media", "entertainment"]:
            analysis["importance"] = 2
        elif "urgent" in title.lower() or "important" in title.lower():
            analysis["importance"] = 5
        
        # Simple sentiment analysis
        positive_words = ["good", "great", "excellent", "success", "win", "happy"]
        negative_words = ["bad", "terrible", "error", "fail", "problem", "issue"]
        
        if any(word in title.lower() for word in positive_words):
            analysis["sentiment"] = "positive"
        elif any(word in title.lower() for word in negative_words):
            analysis["sentiment"] = "negative"
        
        return analysis
    
    async def _analyze_search_query(self, query: str) -> Dict[str, Any]:
        """Analyze search query for intent and topics"""
        analysis = {
            "topics": [],
            "intent": "information",
            "importance": 2
        }
        
        query_lower = query.lower()
        
        # Determine search intent
        if any(word in query_lower for word in ["how to", "tutorial", "guide", "learn"]):
            analysis["intent"] = "learning"
            analysis["importance"] = 3
        elif any(word in query_lower for word in ["buy", "purchase", "shop", "price"]):
            analysis["intent"] = "shopping"
        elif any(word in query_lower for word in ["news", "latest", "update", "breaking"]):
            analysis["intent"] = "news"
            analysis["importance"] = 3
        
        # Extract topics
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis["topics"].append(topic)
        
        return analysis
    
    async def _update_session(self, user_id: int, activity: WebActivity):
        """Update or create user session"""
        if user_id not in self.active_sessions:
            # Create new session
            session_id = hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()
            self.active_sessions[user_id] = WebSession(
                id=session_id,
                user_id=user_id,
                start_time=activity.timestamp,
                domains_visited=set(),
                primary_topics=[]
            )
        
        session = self.active_sessions[user_id]
        session.total_pages += 1
        session.domains_visited.add(activity.domain)
        
        if activity.topics:
            session.primary_topics.extend(activity.topics)
        
        if activity.duration:
            session.total_duration += activity.duration
    
    async def end_session(self, user_id: int) -> Optional[WebSession]:
        """End user's active session"""
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            session.end_time = datetime.now()
            
            # Determine session type based on activities
            if session.domains_visited:
                work_domains = {"github.com", "stackoverflow.com", "jira.com", "confluence.com"}
                if any(domain in work_domains for domain in session.domains_visited):
                    session.session_type = "work"
                elif "youtube.com" in session.domains_visited or "netflix.com" in session.domains_visited:
                    session.session_type = "entertainment"
                elif "coursera.org" in session.domains_visited or "udemy.com" in session.domains_visited:
                    session.session_type = "learning"
            
            # Remove from active sessions
            del self.active_sessions[user_id]
            
            logger.info(f"Ended session for user {user_id}: {session.session_type}")
            return session
        
        return None
    
    async def get_user_activity_summary(
        self,
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get user's web activity summary"""
        # Filter activities for the user and time period
        cutoff_time = datetime.now() - timedelta(days=days)
        user_activities = [
            activity for activity in self.activity_buffer
            if activity.user_id == user_id and activity.timestamp >= cutoff_time
        ]
        
        summary = {
            "total_activities": len(user_activities),
            "page_views": len([a for a in user_activities if a.activity_type == "page_view"]),
            "searches": len([a for a in user_activities if a.activity_type == "search"]),
            "clicks": len([a for a in user_activities if a.activity_type == "click"]),
            "domains_visited": list(set(a.domain for a in user_activities)),
            "top_topics": {},
            "session_summary": {},
            "productivity_score": 0
        }
        
        # Analyze topics
        all_topics = []
        for activity in user_activities:
            if activity.topics:
                all_topics.extend(activity.topics)
        
        for topic in all_topics:
            summary["top_topics"][topic] = summary["top_topics"].get(topic, 0) + 1
        
        # Calculate productivity score
        work_activities = [a for a in user_activities if a.meta_data and a.meta_data.get("domain_category") in ["work", "development", "learning"]]
        entertainment_activities = [a for a in user_activities if a.meta_data and a.meta_data.get("domain_category") in ["entertainment", "social_media"]]
        
        if user_activities:
            summary["productivity_score"] = len(work_activities) / len(user_activities) * 100
        
        return summary
    
    async def get_recommendations(
        self,
        user_id: int,
        based_on: str = "recent_activity"
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on web activity"""
        recommendations = []
        
        if based_on == "recent_activity":
            # Get recent activity summary
            summary = await self.get_user_activity_summary(user_id, days=3)
            
            # Generate recommendations based on topics
            for topic, count in summary["top_topics"].items():
                if topic == "technology" and count > 2:
                    recommendations.append({
                        "type": "learning",
                        "title": "Advanced Programming Course",
                        "description": "Based on your interest in technology",
                        "url": "https://coursera.org/programming",
                        "confidence": 0.8
                    })
                elif topic == "business" and count > 2:
                    recommendations.append({
                        "type": "resource",
                        "title": "Business Strategy Resources",
                        "description": "Curated business content for you",
                        "url": "https://hbr.org",
                        "confidence": 0.7
                    })
        
        return recommendations


# Global web activity tracker instance
web_activity_tracker = WebActivityTracker() 