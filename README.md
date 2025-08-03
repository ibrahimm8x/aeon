# AEON - Digital AI Twin

AEON is a digital AI twin that learns and remembers everything about its owner, acting as their digital consciousness with persistent memory through a hybrid vector and graph database system.

## Project Overview

- **AI Twin**: Conversational interface that responds in-persona for its owner
- **Hybrid Memory**: Vector database (Chroma) + Graph database (Neo4j) for persistent, never-forgotten memory
- **Digital Realm**: Real-time hub for AEONs to communicate with each other
- **RAG System**: Retrieval-Augmented Generation using OpenAI

## Architecture

- **Backend**: FastAPI (Python)
- **Vector DB**: Chroma (local)
- **Graph DB**: Neo4j (local)
- **LLM**: OpenAI GPT-4
- **Frontend**: React/Next.js (Phase 1+)
- **Real-time**: WebSocket (Phase 3+)

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- OpenAI API Key

### Quick Start
1. Clone the repository
2. Copy `.env.example` to `.env` and add your OpenAI API key
3. Run `docker-compose up -d` to start databases
4. Run `pip install -r requirements.txt`
5. Run `uvicorn app.main:app --reload`

## Project Phases

- **Phase 0**: Environment Setup ✅
- **Phase 1**: Single-User AEON ✅
- **Phase 2**: Hybrid Memory & RAG
- **Phase 3**: Digital Realm Prototype
- **Phase 4**: Refinement & UX

## Phase 1 Features

### ✅ Completed Features
- **User Management**: Registration, login, authentication with JWT tokens
- **AEON Chat Interface**: Real-time conversation with AI using OpenAI GPT-4
- **Conversation Management**: Create, view, and manage chat conversations
- **Memory System**: Basic memory storage for user preferences and experiences
- **Database**: SQLite database with SQLAlchemy ORM (upgradable to PostgreSQL)
- **Security**: Password hashing, JWT authentication, role-based access

### 🔧 Technical Stack
- **Backend**: FastAPI with async/await support
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI Integration**: OpenAI GPT-4 for intelligent responses
- **API Documentation**: Auto-generated with OpenAPI/Swagger

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints
- `POST /api/v1/users/register` - User registration
- `POST /api/v1/users/login` - User authentication
- `POST /api/v1/aeon/chat` - Chat with AEON
- `GET /api/v1/aeon/conversations` - Get user conversations
- `GET /api/v1/aeon/status` - Get AEON statistics 