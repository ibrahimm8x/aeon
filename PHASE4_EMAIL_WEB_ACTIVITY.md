# AEON Phase 4: Email Access & Web Activity Tracking

## 🎯 Overview

This document outlines the implementation of **Email Access** and **Web Activity Tracking** features for AEON Digital AI Twin, enabling unprecedented personalization through real-time monitoring of user's digital activities.

## 📧 Email Integration

### Architecture

The email integration system allows AEON to:
- **Access user emails** via IMAP/SMTP protocols
- **Analyze email content** for importance, sentiment, and topics
- **Provide real-time notifications** for urgent emails
- **Generate email insights** and patterns

### Key Components

#### 1. Email Service (`app/services/email_service.py`)

```python
class EmailService:
    """Service for email access and processing"""
    
    async def configure_email_access(self, email_address, password, ...)
    async def fetch_recent_emails(self, folder="INBOX", limit=50, ...)
    async def send_email(self, to, subject, content, ...)
    async def get_email_summary(self, days=7)
```

**Features:**
- ✅ **IMAP/SMTP Integration**: Connect to any email provider
- ✅ **Email Analysis**: Importance scoring (1-5 scale)
- ✅ **Sentiment Analysis**: Positive/negative/neutral classification
- ✅ **Entity Extraction**: People, organizations, topics
- ✅ **Real-time Monitoring**: Check for new emails every 5 minutes

#### 2. Email Data Structure

```python
@dataclass
class EmailMessage:
    id: str
    subject: str
    sender: str
    recipients: List[str]
    content: str
    html_content: Optional[str]
    timestamp: datetime
    is_read: bool
    labels: List[str]
    importance: int = 1  # 1-5 scale
    sentiment: Optional[str] = None
    extracted_entities: Optional[Dict] = None
```

### Email Analysis Capabilities

#### Importance Scoring
- **Urgent Keywords**: "urgent", "asap", "important", "critical", "deadline"
- **Sender Importance**: Boss, manager, CEO, HR, finance contacts
- **Personal Keywords**: "meeting", "appointment", "schedule", "project"

#### Sentiment Analysis
- **Positive Words**: "good", "great", "excellent", "happy", "pleased", "thank"
- **Negative Words**: "bad", "terrible", "unhappy", "disappointed", "angry"

#### Entity Extraction
- **People**: Extract names and relationships
- **Organizations**: Company names and affiliations
- **Topics**: Categorize email content by subject matter
- **Dates**: Extract important dates and deadlines

## 🌐 Web Activity Tracking

### Architecture

The web activity tracking system enables AEON to:
- **Monitor browsing patterns** in real-time
- **Analyze productivity** based on website categories
- **Track user interests** and learning patterns
- **Provide personalized recommendations**

### Key Components

#### 1. Web Activity Tracker (`app/services/web_activity_service.py`)

```python
class WebActivityTracker:
    """Real-time web activity tracker"""
    
    async def track_page_view(self, user_id, url, title, ...)
    async def track_search(self, user_id, search_query, search_engine, ...)
    async def track_click(self, user_id, url, element_type, ...)
    async def get_user_activity_summary(self, user_id, days=7)
    async def get_recommendations(self, user_id, based_on="recent_activity")
```

**Features:**
- ✅ **Page View Tracking**: URL, title, duration, referrer
- ✅ **Search Query Monitoring**: Google, Bing, YouTube, etc.
- ✅ **Click Tracking**: Element types and interactions
- ✅ **Session Management**: Browsing sessions and patterns
- ✅ **Productivity Scoring**: Work vs. entertainment analysis

#### 2. Web Activity Data Structure

```python
@dataclass
class WebActivity:
    id: str
    user_id: int
    url: str
    domain: str
    title: str
    activity_type: str  # page_view, search, click, form_submit
    timestamp: datetime
    duration: Optional[int] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    meta_data: Optional[Dict] = None
    extracted_content: Optional[str] = None
    sentiment: Optional[str] = None
    topics: Optional[List[str]] = None
    importance: int = 1  # 1-5 scale
```

#### 3. Web Session Management

```python
@dataclass
class WebSession:
    id: str
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    total_pages: int = 0
    total_duration: int = 0
    domains_visited: Set[str] = None
    primary_topics: List[str] = None
    session_type: str = "general"  # work, personal, research, etc.
```

### Website Categorization

#### Domain Categories
- **Social Media**: Facebook, Twitter, Instagram, LinkedIn, Reddit
- **Work/Professional**: GitHub, Stack Overflow, Jira, Confluence, Slack
- **News/Information**: Hacker News, TechCrunch, BBC, CNN
- **Shopping**: Amazon, eBay, Etsy
- **Entertainment**: YouTube, Netflix, Spotify, Twitch
- **Learning**: Coursera, Udemy, Khan Academy, W3Schools

#### Topic Classification
- **Technology**: programming, software, hardware, AI, machine learning
- **Business**: startup, entrepreneurship, marketing, finance
- **Health**: fitness, nutrition, medical, wellness
- **Education**: learning, course, tutorial, study, academic
- **Entertainment**: movie, music, game, streaming, podcast
- **News**: politics, world, local, breaking, current events

### Productivity Analysis

#### Productivity Scoring Algorithm
```python
# Calculate productivity score (0-100%)
work_activities = [activities from work/development/learning domains]
entertainment_activities = [activities from entertainment/social domains]

productivity_score = (len(work_activities) / total_activities) * 100
```

#### Session Type Classification
- **Work**: GitHub, Stack Overflow, Jira, Confluence
- **Entertainment**: YouTube, Netflix, social media
- **Learning**: Coursera, Udemy, educational sites
- **Research**: News sites, documentation, tutorials

## 🔌 Enhanced WebSocket Integration

### Real-time Communication

The enhanced WebSocket system provides:
- **Real-time email notifications**
- **Activity insights and recommendations**
- **Productivity reminders**
- **Contextual alerts**

#### Enhanced Connection Manager

```python
class EnhancedConnectionManager(ConnectionManager):
    """Enhanced connection manager with email and web activity tracking"""
    
    async def start_activity_monitoring(self, user_id: int)
    async def _check_new_emails(self, user_id: int)
    async def _check_web_activity_updates(self, user_id: int)
    async def _send_email_summary(self, user_id: int, emails: List[EmailMessage])
    async def _send_productivity_reminder(self, user_id: int, summary: Dict[str, Any])
```

### Real-time Features

#### Email Monitoring (Every 5 minutes)
- Check for new unread emails
- Analyze email importance and sentiment
- Send urgent email alerts
- Provide email summaries

#### Web Activity Monitoring (Every 30 seconds)
- Track recent browsing activity
- Calculate productivity scores
- Generate activity insights
- Send productivity reminders

#### Real-time Notifications
```json
{
  "type": "urgent_email_alert",
  "data": {
    "message": "You have 3 urgent emails",
    "emails": [
      {
        "subject": "Project Deadline",
        "sender": "boss@company.com",
        "importance": 5
      }
    ]
  }
}
```

## 🌐 Browser Extension

### Extension Architecture

#### Manifest (`browser_extension/manifest.json`)
```json
{
  "manifest_version": 3,
  "name": "AEON Web Activity Tracker",
  "permissions": [
    "activeTab",
    "storage",
    "tabs",
    "webNavigation",
    "webRequest"
  ],
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"]
    }
  ]
}
```

#### Content Script (`browser_extension/content.js`)

**Tracking Capabilities:**
- ✅ **Page Views**: URL, title, duration, referrer
- ✅ **Search Queries**: Google, Bing, YouTube, DuckDuckGo
- ✅ **Click Events**: Element types and text
- ✅ **Form Submissions**: Form data and actions
- ✅ **Page Visibility**: Tab focus/blur tracking
- ✅ **Scroll Depth**: Reading engagement metrics

**Real-time Communication:**
- WebSocket connection to AEON server
- HTTP fallback for activity data
- Real-time notifications and insights

### Extension Features

#### Activity Tracking
```javascript
class AEONActivityTracker {
    trackPageView(isFinal = false)
    trackClicks()
    trackFormSubmissions()
    trackSearchQueries()
    trackPageVisibility()
    trackScrollDepth()
}
```

#### Real-time Notifications
- **Productivity Reminders**: Low productivity score alerts
- **Activity Insights**: Daily browsing summaries
- **Recommendations**: Personalized content suggestions

## 🗄️ Database Schema

### New Tables

#### Email Configuration
```sql
CREATE TABLE email_configs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    imap_server VARCHAR(255) DEFAULT 'imap.gmail.com',
    imap_port INTEGER DEFAULT 993,
    smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com',
    smtp_port INTEGER DEFAULT 587,
    is_active BOOLEAN DEFAULT TRUE,
    last_sync DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users (id)
);
```

#### Web Activities
```sql
CREATE TABLE web_activities (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    domain VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    activity_type VARCHAR(50) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    duration INTEGER,
    referrer TEXT,
    user_agent TEXT,
    ip_address VARCHAR(45),
    meta_data JSON,
    extracted_content TEXT,
    sentiment VARCHAR(20),
    topics JSON,
    importance INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users (id)
);
```

#### Web Sessions
```sql
CREATE TABLE web_sessions (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    total_pages INTEGER DEFAULT 0,
    total_duration INTEGER DEFAULT 0,
    domains_visited JSON,
    primary_topics JSON,
    session_type VARCHAR(50) DEFAULT 'general',
    FOREIGN KEY(user_id) REFERENCES users (id)
);
```

## 🔌 API Endpoints

### Email Endpoints

#### Configure Email Access
```http
POST /api/v1/aeon/enhanced/email/configure
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "app_password",
  "imap_server": "imap.gmail.com",
  "imap_port": 993,
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

#### Get Email Summary
```http
GET /api/v1/aeon/enhanced/email/summary?days=7
```

#### Get Recent Emails
```http
GET /api/v1/aeon/enhanced/email/recent?limit=20&folder=INBOX
```

### Web Activity Endpoints

#### Track Web Activity
```http
POST /api/v1/aeon/enhanced/web-activity/track
Content-Type: application/json

{
  "type": "page_view",
  "url": "https://example.com",
  "title": "Example Page",
  "duration": 120,
  "referrer": "https://google.com"
}
```

#### Get Activity Summary
```http
GET /api/v1/aeon/enhanced/web-activity/summary?days=7
```

#### Get Recommendations
```http
GET /api/v1/aeon/enhanced/web-activity/recommendations?based_on=recent_activity
```

### Combined Analytics

#### Get Combined Analytics
```http
GET /api/v1/aeon/enhanced/analytics/combined?days=7
```

**Response:**
```json
{
  "user_id": 1,
  "analysis_period": "Last 7 days",
  "timestamp": "2024-01-01T12:00:00Z",
  "email_analytics": {
    "total_emails": 45,
    "unread_count": 12,
    "important_emails": 8,
    "sentiment_distribution": {
      "positive": 15,
      "neutral": 25,
      "negative": 5
    }
  },
  "web_activity_analytics": {
    "total_activities": 156,
    "page_views": 89,
    "searches": 23,
    "clicks": 44,
    "productivity_score": 72.5,
    "top_topics": {
      "technology": 15,
      "business": 8,
      "learning": 12
    }
  },
  "productivity_insights": {
    "status": "good",
    "message": "Good productivity level"
  },
  "recommendations": [
    {
      "type": "learning",
      "title": "Advanced Programming Course",
      "description": "Based on your interest in technology",
      "url": "https://coursera.org/programming",
      "confidence": 0.8
    }
  ]
}
```

## 🔐 Security & Privacy

### Data Protection

#### Email Security
- **OAuth 2.0 Support**: For Gmail and other providers
- **App Passwords**: Use app-specific passwords instead of main passwords
- **Encrypted Storage**: Email credentials stored securely
- **Local Processing**: Email analysis done locally when possible

#### Web Activity Privacy
- **User Consent**: Explicit opt-in for tracking
- **Data Ownership**: All data belongs to the user
- **Local Storage**: Activity data stored locally initially
- **Anonymization**: Personal data can be anonymized

#### Privacy Controls
- **Granular Permissions**: Control what gets tracked
- **Data Retention**: Configurable data retention periods
- **Export/Delete**: Full control over personal data
- **Transparency**: Clear visibility into what's being tracked

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
# Install email and web activity dependencies
pip install imaplib smtplib chromadb

# Install browser extension dependencies (if needed)
npm install -g web-ext
```

### 2. Configure Email Access

```bash
# Set up email configuration
curl -X POST http://localhost:8000/api/v1/aeon/enhanced/email/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "email": "your-email@gmail.com",
    "password": "your-app-password",
    "imap_server": "imap.gmail.com",
    "smtp_server": "smtp.gmail.com"
  }'
```

### 3. Install Browser Extension

1. **Load Extension**: Open Chrome Extensions page
2. **Enable Developer Mode**: Toggle developer mode
3. **Load Unpacked**: Select the `browser_extension` folder
4. **Configure**: Set your user ID and session ID

### 4. Start Enhanced Services

```bash
# Start the enhanced AEON system
./start_phase2.sh

# Or start manually
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Usage Examples

### Email Integration

#### Monitor Important Emails
```python
# Get urgent email alerts
emails = await email_service.fetch_recent_emails(
    folder="INBOX",
    limit=10,
    days_back=1,
    include_read=False
)

urgent_emails = [e for e in emails if e.importance >= 4]
```

#### Email Sentiment Analysis
```python
# Analyze email sentiment
for email in emails:
    if email.sentiment == "negative":
        print(f"Negative email from {email.sender}: {email.subject}")
```

### Web Activity Tracking

#### Productivity Monitoring
```python
# Get productivity insights
summary = await web_activity_tracker.get_user_activity_summary(
    user_id=user_id,
    days=7
)

if summary["productivity_score"] < 50:
    print("Low productivity detected. Consider focusing on work tasks.")
```

#### Interest Tracking
```python
# Track user interests
topics = summary["top_topics"]
for topic, count in topics.items():
    if count > 5:
        print(f"Strong interest in {topic}: {count} activities")
```

## 🔮 Future Enhancements

### Advanced Analytics
- **Learning Pattern Analysis**: Understand how user learns
- **Interest Evolution**: Track changing interests over time
- **Productivity Optimization**: Suggest optimal work patterns
- **Content Recommendations**: Curate personalized content feeds

### Integration Possibilities
- **Calendar Integration**: Connect with calendar for context
- **Task Management**: Link with todo apps for productivity
- **Social Media**: Analyze social media activity patterns
- **Health Data**: Integrate with health apps for holistic insights

### AI Enhancements
- **Predictive Analytics**: Predict user needs and behaviors
- **Smart Notifications**: Context-aware alerts and reminders
- **Personalized Coaching**: AI-driven productivity coaching
- **Behavioral Insights**: Deep learning for pattern recognition

## 🐛 Troubleshooting

### Common Issues

#### Email Connection Problems
```bash
# Test email connection
python -c "
from app.services.email_service import email_service
import asyncio

async def test():
    success = await email_service.configure_email_access(
        email='your-email@gmail.com',
        password='your-app-password'
    )
    print(f'Connection successful: {success}')

asyncio.run(test())
"
```

#### Web Activity Tracking Issues
```bash
# Check if browser extension is working
curl -X POST http://localhost:8000/api/v1/aeon/enhanced/web-activity/track \
  -H "Content-Type: application/json" \
  -d '{
    "type": "page_view",
    "url": "https://example.com",
    "title": "Test Page"
  }'
```

#### WebSocket Connection Issues
```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/api/v1/phase3/ws/1
```

### Debug Commands

#### Check Service Status
```bash
# Check if all services are running
docker ps | grep -E "(neo4j|chroma)"
ps aux | grep uvicorn
curl -s http://localhost:8000/health
```

#### View Logs
```bash
# Check application logs
tail -f logs/aeon.log

# Check database logs
docker logs aeon-neo4j
docker logs aeon-chroma
```

## 📈 Performance Considerations

### Optimization Strategies

#### Email Processing
- **Batch Processing**: Process emails in batches
- **Caching**: Cache email metadata
- **Incremental Sync**: Only fetch new emails
- **Background Processing**: Process emails asynchronously

#### Web Activity Tracking
- **Buffering**: Buffer activities before sending
- **Compression**: Compress activity data
- **Rate Limiting**: Limit tracking frequency
- **Local Storage**: Store activities locally first

#### Database Optimization
- **Indexing**: Index frequently queried fields
- **Partitioning**: Partition large tables by date
- **Archiving**: Archive old data
- **Connection Pooling**: Optimize database connections

## 🎯 Success Metrics

### Key Performance Indicators

#### Email Integration
- **Email Processing Time**: < 5 seconds per email
- **Accuracy**: > 90% importance classification
- **Coverage**: Support for major email providers
- **Uptime**: > 99.9% service availability

#### Web Activity Tracking
- **Tracking Accuracy**: > 95% activity capture
- **Real-time Latency**: < 1 second for notifications
- **Privacy Compliance**: 100% user consent
- **Performance Impact**: < 5% browser performance impact

#### User Engagement
- **Adoption Rate**: > 80% feature usage
- **User Satisfaction**: > 4.5/5 rating
- **Productivity Improvement**: > 20% productivity increase
- **Retention Rate**: > 90% monthly retention

---

## 📝 Conclusion

The Email Access and Web Activity Tracking features represent a significant advancement in AEON's personalization capabilities. By understanding user's email patterns and web browsing habits, AEON can provide:

- **Contextual Awareness**: Understand user's current context and needs
- **Proactive Assistance**: Anticipate user needs before they ask
- **Personalized Insights**: Provide relevant recommendations and insights
- **Productivity Enhancement**: Help users optimize their digital workflow

This implementation creates a truly personalized AI companion that learns and adapts to the user's digital life, making AEON an indispensable part of their daily routine.

---

*Last Updated: January 2024*  
*Version: 1.0.0*  
*Status: Implemented & Tested* 