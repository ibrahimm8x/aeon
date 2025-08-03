#!/bin/bash

# AEON Web Interface Startup Script

echo "🚀 Starting AEON Web Interface..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if the web interface directory exists
if [ ! -d "web_interface" ]; then
    echo "❌ web_interface directory not found"
    exit 1
fi

# Check if the main HTML file exists
if [ ! -f "web_interface/index.html" ]; then
    echo "❌ web_interface/index.html not found"
    exit 1
fi

# Check if the server script exists
if [ ! -f "web_interface/server.py" ]; then
    echo "❌ web_interface/server.py not found"
    exit 1
fi

# Make the server script executable
chmod +x web_interface/server.py

echo "✅ Starting web interface server..."
echo "🌐 Web Interface will be available at: http://localhost:8080"
echo "🔗 Make sure the AEON API server is running on: http://localhost:8000"
echo "📱 Press Ctrl+C to stop the web interface server"
echo "-" * 50

# Start the web interface server
cd web_interface
python3 server.py 