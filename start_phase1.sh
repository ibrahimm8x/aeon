#!/bin/bash

echo "🚀 Starting AEON Phase 1..."
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Please copy env.example to .env and add your OpenAI API key:"
    echo "   cp env.example .env"
    echo "   # Then edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your-api-key-here" .env; then
    echo "⚠️  OpenAI API key not configured!"
    echo "📝 Please add your OpenAI API key to the .env file"
    exit 1
fi

# Start the application
echo "🌟 Starting AEON server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 