#!/bin/bash

# AEON Phase 3: Digital Realm Prototype Startup Script
# Multi-User Interactions, Real-time Capabilities, and Social Intelligence

echo "🚀 Starting AEON Phase 3: Digital Realm Prototype..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing Phase 3 dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if database exists and run migrations
echo "🗄️  Setting up database..."
python -c "
from app.database.session import create_tables
from app.database.models import Base
from sqlalchemy import create_engine
from app.core.config import settings

# Create engine
engine = create_engine(settings.database_url)

# Create all tables including Phase 3 tables
Base.metadata.create_all(bind=engine)
print('✅ Database tables created successfully')
"

# Check if ChromaDB is running
echo "🔍 Checking ChromaDB connection..."
python -c "
import chromadb
try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    client.heartbeat()
    print('✅ ChromaDB is running')
except Exception as e:
    print('⚠️  ChromaDB not accessible. Phase 2 features may be limited.')
"

# Check if Neo4j is running
echo "🔍 Checking Neo4j connection..."
python -c "
from neo4j import GraphDatabase
import os
try:
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    driver.close()
    print('✅ Neo4j is running')
except Exception as e:
    print('⚠️  Neo4j not accessible. Phase 2 features may be limited.')
"

# Check OpenAI API key
echo "🔍 Checking OpenAI API key..."
python -c "
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print('❌ OPENAI_API_KEY not found in .env file')
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    client.models.list()
    print('✅ OpenAI API key is valid')
except Exception as e:
    print('❌ OpenAI API key is invalid or API is not accessible')
    exit(1)
"

# Create default chat rooms for Phase 3
echo "🏠 Creating default Phase 3 chat rooms..."
python -c "
from app.database.session import get_db
from app.database.models import ChatRoom, User
from sqlalchemy.orm import Session
import uuid

db = next(get_db())

# Check if default rooms exist
general_room = db.query(ChatRoom).filter(ChatRoom.name == 'General').first()
if not general_room:
    general_room = ChatRoom(
        id=str(uuid.uuid4()),
        name='General',
        description='General discussion room for all users',
        created_by=1,
        is_public=True,
        is_aeon_room=False
    )
    db.add(general_room)
    print('✅ Created General chat room')

aeon_room = db.query(ChatRoom).filter(ChatRoom.name == 'AEON Hub').first()
if not aeon_room:
    aeon_room = ChatRoom(
        id=str(uuid.uuid4()),
        name='AEON Hub',
        description='Room where AEONs can interact and share knowledge',
        created_by=1,
        is_public=True,
        is_aeon_room=True
    )
    db.add(aeon_room)
    print('✅ Created AEON Hub chat room')

knowledge_room = db.query(ChatRoom).filter(ChatRoom.name == 'Knowledge Exchange').first()
if not knowledge_room:
    knowledge_room = ChatRoom(
        id=str(uuid.uuid4()),
        name='Knowledge Exchange',
        description='Share and discuss knowledge with other users',
        created_by=1,
        is_public=True,
        is_aeon_room=False
    )
    db.add(knowledge_room)
    print('✅ Created Knowledge Exchange chat room')

db.commit()
print('✅ Default Phase 3 chat rooms ready')
"

# Start the FastAPI application
echo "🌐 Starting AEON Phase 3 server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo "🎯 Phase 3 Health: http://localhost:8000/api/v1/phase3/health/phase3"
echo "🔌 WebSocket endpoint: ws://localhost:8000/api/v1/phase3/ws/{user_id}"
echo ""
echo "🎉 AEON Phase 3 is ready! Features available:"
echo "   • Real-time messaging via WebSocket"
echo "   • Multi-user chat rooms"
echo "   • User relationships and social networking"
echo "   • Shared knowledge system"
echo "   • AEON-to-AEON interactions"
echo "   • Social intelligence and user discovery"
echo ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 