"""
Email service for AEON to access and process user emails
"""

import asyncio
import email
import imaplib
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


@dataclass
class EmailMessage:
    """Email message data structure"""
    id: str
    subject: str
    sender: str
    recipients: List[str]
    content: str
    html_content: Optional[str]
    timestamp: datetime
    is_read: bool
    labels: List[str]
    thread_id: Optional[str] = None
    importance: int = 1  # 1-5 scale
    sentiment: Optional[str] = None
    extracted_entities: Optional[Dict] = None


class EmailService:
    """Service for email access and processing"""
    
    def __init__(self):
        self.imap_connection = None
        self.smtp_connection = None
        self.email_config = None
    
    async def configure_email_access(
        self,
        email_address: str,
        password: str,
        imap_server: str = "imap.gmail.com",
        imap_port: int = 993,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        use_oauth: bool = False,
        oauth_token: Optional[str] = None
    ):
        """Configure email access for a user"""
        self.email_config = {
            "email": email_address,
            "password": password,
            "imap_server": imap_server,
            "imap_port": imap_port,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "use_oauth": use_oauth,
            "oauth_token": oauth_token
        }
        
        # Test connection
        await self.test_connection()
    
    async def test_connection(self) -> bool:
        """Test email connection"""
        try:
            # Test IMAP connection
            imap = imaplib.IMAP4_SSL(self.email_config["imap_server"], self.email_config["imap_port"])
            imap.login(self.email_config["email"], self.email_config["password"])
            imap.logout()
            
            # Test SMTP connection
            smtp = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            smtp.starttls()
            smtp.login(self.email_config["email"], self.email_config["password"])
            smtp.quit()
            
            logger.info(f"Email connection successful for {self.email_config['email']}")
            return True
        except Exception as e:
            logger.error(f"Email connection failed: {str(e)}")
            return False
    
    async def fetch_recent_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        days_back: int = 7,
        include_read: bool = True
    ) -> List[EmailMessage]:
        """Fetch recent emails from specified folder"""
        try:
            imap = imaplib.IMAP4_SSL(self.email_config["imap_server"], self.email_config["imap_port"])
            imap.login(self.email_config["email"], self.email_config["password"])
            
            # Select folder
            imap.select(folder)
            
            # Search for recent emails
            date_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{date_since}")'
            if not include_read:
                search_criteria += ' UNSEEN'
            
            _, message_numbers = imap.search(None, search_criteria)
            
            emails = []
            for num in message_numbers[0].split()[-limit:]:
                try:
                    _, msg_data = imap.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Parse email
                    parsed_email = await self._parse_email_message(email_message, num.decode())
                    emails.append(parsed_email)
                    
                except Exception as e:
                    logger.error(f"Error parsing email {num}: {str(e)}")
                    continue
            
            imap.logout()
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            return []
    
    async def _parse_email_message(self, email_message: email.message.Message, message_id: str) -> EmailMessage:
        """Parse email message into structured format"""
        # Extract basic headers
        subject = email_message.get("subject", "")
        sender = email_message.get("from", "")
        recipients = email_message.get("to", "").split(",") if email_message.get("to") else []
        timestamp = email.utils.parsedate_to_datetime(email_message.get("date")) if email_message.get("date") else datetime.now()
        
        # Extract content
        content = ""
        html_content = None
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    content = part.get_payload(decode=True).decode()
                elif content_type == "text/html" and not html_content:
                    html_content = part.get_payload(decode=True).decode()
        else:
            content = email_message.get_payload(decode=True).decode()
        
        # Analyze email importance and sentiment
        importance = await self._analyze_email_importance(subject, content, sender)
        sentiment = await self._analyze_email_sentiment(content)
        entities = await self._extract_entities(subject, content)
        
        return EmailMessage(
            id=message_id,
            subject=subject,
            sender=sender,
            recipients=recipients,
            content=content,
            html_content=html_content,
            timestamp=timestamp,
            is_read=False,  # Will be updated based on IMAP flags
            labels=[],
            importance=importance,
            sentiment=sentiment,
            extracted_entities=entities
        )
    
    async def _analyze_email_importance(self, subject: str, content: str, sender: str) -> int:
        """Analyze email importance (1-5 scale)"""
        importance = 1
        
        # Check for urgent keywords
        urgent_keywords = ["urgent", "asap", "important", "critical", "deadline", "emergency"]
        if any(keyword in subject.lower() or keyword in content.lower() for keyword in urgent_keywords):
            importance += 2
        
        # Check sender importance (could be enhanced with contact database)
        important_senders = ["boss", "manager", "ceo", "hr", "finance"]
        if any(sender_keyword in sender.lower() for sender_keyword in important_senders):
            importance += 1
        
        # Check for personal keywords
        personal_keywords = ["meeting", "appointment", "schedule", "project", "task"]
        if any(keyword in subject.lower() or keyword in content.lower() for keyword in personal_keywords):
            importance += 1
        
        return min(importance, 5)
    
    async def _analyze_email_sentiment(self, content: str) -> Optional[str]:
        """Analyze email sentiment"""
        # Simple sentiment analysis (could be enhanced with ML models)
        positive_words = ["good", "great", "excellent", "happy", "pleased", "thank", "appreciate"]
        negative_words = ["bad", "terrible", "unhappy", "disappointed", "angry", "frustrated", "sorry"]
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def _extract_entities(self, subject: str, content: str) -> Dict[str, Any]:
        """Extract entities from email content"""
        entities = {
            "people": [],
            "organizations": [],
            "dates": [],
            "locations": [],
            "topics": []
        }
        
        # Simple entity extraction (could be enhanced with NER models)
        # This is a basic implementation - could use spaCy or other NLP libraries
        
        return entities
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        content: str,
        html_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email"""
        try:
            smtp = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            smtp.starttls()
            smtp.login(self.email_config["email"], self.email_config["password"])
            
            msg = MimeMultipart()
            msg["From"] = self.email_config["email"]
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject
            
            if cc:
                msg["Cc"] = ", ".join(cc)
            
            # Add text content
            text_part = MimeText(content, "plain")
            msg.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MimeText(html_content, "html")
                msg.attach(html_part)
            
            # Send email
            recipients = to + (cc or []) + (bcc or [])
            smtp.sendmail(self.email_config["email"], recipients, msg.as_string())
            smtp.quit()
            
            logger.info(f"Email sent successfully to {', '.join(to)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    async def mark_as_read(self, message_ids: List[str]) -> bool:
        """Mark emails as read"""
        try:
            imap = imaplib.IMAP4_SSL(self.email_config["imap_server"], self.email_config["imap_port"])
            imap.login(self.email_config["email"], self.email_config["password"])
            
            for message_id in message_ids:
                imap.store(message_id, '+FLAGS', '\\Seen')
            
            imap.logout()
            return True
            
        except Exception as e:
            logger.error(f"Error marking emails as read: {str(e)}")
            return False
    
    async def get_email_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get email summary for the specified period"""
        emails = await self.fetch_recent_emails(days_back=days)
        
        summary = {
            "total_emails": len(emails),
            "unread_count": len([e for e in emails if not e.is_read]),
            "important_emails": len([e for e in emails if e.importance >= 4]),
            "sentiment_distribution": {},
            "top_senders": {},
            "top_topics": {}
        }
        
        # Analyze sentiment distribution
        for email in emails:
            sentiment = email.sentiment or "neutral"
            summary["sentiment_distribution"][sentiment] = summary["sentiment_distribution"].get(sentiment, 0) + 1
        
        # Analyze top senders
        for email in emails:
            sender = email.sender
            summary["top_senders"][sender] = summary["top_senders"].get(sender, 0) + 1
        
        return summary


# Global email service instance
email_service = EmailService() 