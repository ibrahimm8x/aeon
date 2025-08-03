#!/bin/bash

# AEON Phase 2 Startup Script
# Starts the application with enhanced hybrid memory system

echo "🚀 Starting AEON Phase 2 - Hybrid Memory & RAG System"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your OpenAI API key before proceeding"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OpenAI API key not found in .env file"
    echo "📝 Please add your OpenAI API key to .env file"
    exit 1
fi

# Install/upgrade dependencies
echo "Installing Phase 2 dependencies..."
pip install -r requirements.txt

echo ""
echo "🐳 Starting database services..."
echo "Starting Chroma (Vector DB) and Neo4j (Graph DB)..."

# Start databases using Docker Compose
docker-compose up -d

# Wait for databases to be ready
echo "⏳ Waiting for databases to initialize..."
sleep 10

# Check if databases are running
echo "🔍 Checking database connectivity..."

# Check Chroma
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
    echo "✅ Chroma (Vector DB) is ready"
else
    echo "❌ Chroma is not responding"
fi

# Check Neo4j
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j (Graph DB) is ready"
else
    echo "❌ Neo4j is not responding"
fi

echo ""
echo "🧠 Initializing AEON Phase 2..."
echo "Features enabled:"
echo "  ✅ Hybrid Memory System (Chroma + Neo4j)"
echo "  ✅ RAG (Retrieval-Augmented Generation)"
echo "  ✅ Intelligent Context Retrieval"
echo "  ✅ Memory Relationships & Concepts"
echo "  ✅ Enhanced Conversation Understanding"

echo ""
echo "🌐 Starting AEON API server..."
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo "Hybrid System Health: http://localhost:8000/api/v1/aeon/health/hybrid"

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "🎉 AEON Phase 2 startup complete!"
echo ""
echo "Available endpoints:"
echo "  Original (Phase 1): /api/v1/aeon/chat"
echo "  Enhanced (Phase 2): /api/v1/aeon/chat/enhanced"
echo "  Memory Search: /api/v1/aeon/memories/search?enhanced=true"
echo "  Graph Init: /api/v1/aeon/graph/initialize"
echo "  Context Retrieval: /api/v1/aeon/context/retrieve" 