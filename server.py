#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import signal
import socket
import sys
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

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_server():
    # Change to the directory containing the server script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if port is in use
    if is_port_in_use(PORT):
        print(f"\n❌ Port {PORT} is already in use!")
        print("Please either:")
        print(f"  1. Kill the process using port {PORT}:")
        print(f"     sudo lsof -i :{PORT}  # to find the process")
        print(f"     kill <PID>            # to kill it")
        print("  2. Or use a different port by changing PORT in server.py")
        sys.exit(1)
    
    # Create the server with socket reuse option
    socketserver.TCPServer.allow_reuse_address = True
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
            print("\n👋 Server stopping...")
            # Shutdown the server gracefully
            httpd.shutdown()
            httpd.server_close()
            print("✅ Server stopped")

if __name__ == "__main__":
    run_server() 