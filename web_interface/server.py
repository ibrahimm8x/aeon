#!/usr/bin/env python3
"""
Simple HTTP server for AEON Web Interface
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # Serve login.html as default page
        if self.path == '/':
            self.path = '/login.html'
        super().do_GET()
    
    def log_message(self, format, *args):
        # Custom logging format
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    """Start the HTTP server"""
    PORT = 8080
    
    # Change to the web_interface directory
    os.chdir(SCRIPT_DIR)
    
    print(f"🚀 Starting AEON Web Interface Server...")
    print(f"📁 Serving files from: {SCRIPT_DIR}")
    print(f"🌐 Web Interface URL: http://localhost:{PORT}")
    print(f"🔗 API Server URL: http://localhost:8000")
    print(f"📱 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            print(f"🎯 Open your browser and go to: http://localhost:{PORT}")
            print("-" * 50)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Please stop any other server on this port.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 