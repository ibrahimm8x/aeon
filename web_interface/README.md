# AEON Web Interface

A modern, responsive web dashboard for testing and visualizing AEON Digital AI Twin features.

## 🚀 Features

### 📊 Dashboard Overview
- **Real-time Status Monitoring**: Database, AI services, email, and web activity status
- **Live Chat Interface**: Test AEON's conversation capabilities
- **Activity Feed**: Real-time activity monitoring and logging
- **Test Results Panel**: Visual display of API test results

### 🧪 Testing Capabilities
- **Health Check**: Test server and database connectivity
- **Chat Testing**: Test AEON's conversation and response generation
- **Memory Testing**: Test memory retrieval and storage
- **RAG Testing**: Test Retrieval-Augmented Generation capabilities
- **Email Configuration**: Set up and test email integration

### 🎨 Modern UI/UX
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Live status indicators and activity feeds
- **Interactive Elements**: Hover effects, animations, and smooth transitions
- **Dark/Light Theme**: Clean, modern interface design

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7+
- AEON API server running on `http://localhost:8000`
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Quick Start

1. **Start the AEON API Server** (if not already running):
   ```bash
   ./start_phase2.sh
   ```

2. **Start the Web Interface**:
   ```bash
   ./start_web_interface.sh
   ```

3. **Open in Browser**:
   Navigate to `http://localhost:8080`

### Manual Start
```bash
cd web_interface
python3 server.py
```

## 📱 Usage Guide

### Dashboard Overview
The dashboard is divided into several sections:

1. **Status Cards** (Top Row):
   - Database connection status
   - AI services availability
   - Email configuration status
   - Web activity tracking status

2. **Chat Interface** (Left Side):
   - Real-time chat with AEON
   - Message history
   - Send/receive functionality

3. **Control Panel** (Right Side):
   - Quick action buttons for testing
   - Email configuration form
   - Activity feed

4. **Test Results** (Bottom):
   - Detailed test results and responses
   - JSON response visualization
   - Error handling and display

### Testing Features

#### Health Check
- Tests server connectivity
- Verifies database connections
- Checks AI service availability

#### Chat Testing
- Sends test messages to AEON
- Displays AI responses
- Tests conversation flow

#### Memory Testing
- Tests memory retrieval
- Displays stored memories
- Tests memory enhancement features

#### RAG Testing
- Tests context retrieval
- Displays relevant information
- Tests knowledge base queries

#### Email Configuration
- Configure email access
- Test email connectivity
- Set up IMAP/SMTP settings

### Real-time Features

#### WebSocket Connection
- Real-time activity updates
- Live status monitoring
- Instant notifications

#### Activity Feed
- Logs all user actions
- Shows system events
- Displays error messages

## 🔧 Configuration

### API Endpoints
The web interface connects to the following AEON API endpoints:

- `GET /api/v1/health` - Health check
- `POST /api/v1/aeon/chat` - Basic chat
- `POST /api/v1/aeon/chat/enhanced` - Enhanced chat
- `GET /api/v1/aeon/memories/enhanced` - Memory retrieval
- `POST /api/v1/aeon/context/retrieve` - RAG testing
- `POST /api/v1/aeon/enhanced/email/configure` - Email setup
- `WS /api/v1/phase3/ws/{user_id}` - WebSocket connection

### Customization
You can customize the interface by modifying:

- **API Base URL**: Change `API_BASE` in `index.html`
- **Port**: Modify `PORT` in `server.py`
- **Styling**: Edit CSS in `index.html`
- **Features**: Add new test functions in JavaScript

## 🐛 Troubleshooting

### Common Issues

#### "Server not responding"
- Ensure AEON API server is running on port 8000
- Check if databases (Neo4j, ChromaDB) are running
- Verify firewall settings

#### "CORS errors"
- The web interface includes CORS headers
- Ensure you're accessing via `http://localhost:8080`
- Check browser console for specific errors

#### "WebSocket connection failed"
- Verify WebSocket endpoint is available
- Check if user authentication is required
- Ensure WebSocket support in browser

#### "Email configuration failed"
- Verify email credentials
- Check IMAP/SMTP settings
- Ensure app passwords are used for Gmail

### Debug Mode
Enable debug logging by opening browser developer tools:
1. Press `F12` or `Ctrl+Shift+I`
2. Go to Console tab
3. Check for error messages and network requests

## 📊 Performance

### Browser Compatibility
- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

### Network Requirements
- **API Server**: `http://localhost:8000`
- **Web Interface**: `http://localhost:8080`
- **WebSocket**: `ws://localhost:8000`

## 🔒 Security

### Local Development
- Only accessible from localhost
- No external network access
- CORS headers for local development

### Production Considerations
- Add authentication
- Use HTTPS
- Implement rate limiting
- Add input validation

## 📈 Future Enhancements

### Planned Features
- **User Authentication**: Login/logout functionality
- **Advanced Analytics**: Detailed performance metrics
- **Configuration Management**: Save/load settings
- **Multi-user Support**: Multiple user sessions
- **Mobile App**: Native mobile application

### Customization Options
- **Theme Selection**: Multiple color schemes
- **Layout Customization**: Adjustable dashboard layout
- **Plugin System**: Extensible functionality
- **API Documentation**: Built-in API explorer

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies
3. Start the development server
4. Make changes and test

### Code Style
- Use consistent indentation
- Follow JavaScript ES6+ standards
- Maintain responsive design
- Add comments for complex logic

## 📄 License

This web interface is part of the AEON Digital AI Twin project.

---

**Note**: This web interface is designed for testing and development purposes. For production use, additional security measures should be implemented. 