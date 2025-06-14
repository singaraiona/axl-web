#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
from urllib.parse import urlparse

PORT = 8000
DIRECTORY = "site"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

def run_server():
    # Change to the directory containing the server script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create the server
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n🚀 Starting server at http://localhost:{PORT}")
        print("📂 Serving files from:", os.getcwd())
        print("\n📝 Available pages:")
        print("  • http://localhost:8000/")
        print("\n🛑 Press Ctrl+C to stop the server\n")
        
        # Open the default browser
        webbrowser.open(f'http://localhost:{PORT}')
        
        # Start the server
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    run_server() 