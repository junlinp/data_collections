#!/usr/bin/env python3
"""
Test script to verify Flask server is working correctly
Helps diagnose 403 and other connection issues
"""

import requests
import time
import subprocess
import sys
import os
from web_app import app
import threading

def test_flask_app():
    """Test the Flask application directly"""
    print("🧪 Testing Flask application...")
    
    # Test basic route
    with app.test_client() as client:
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Flask application is working correctly")
            return True
        else:
            print(f"❌ Flask application returned status code: {response.status_code}")
            return False

def test_server_connection(host='127.0.0.1', port=5000, timeout=5):
    """Test server connection"""
    print(f"🌐 Testing connection to http://{host}:{port}")
    
    try:
        response = requests.get(f"http://{host}:{port}", timeout=timeout)
        print(f"✅ Server responded with status code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to server at http://{host}:{port}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout to http://{host}:{port}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def start_test_server(host='127.0.0.1', port=5000):
    """Start a test server in a separate thread"""
    def run_server():
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print(f"🚀 Starting test server on http://{host}:{port}")
    time.sleep(3)
    
    return server_thread

def check_port_usage(port=5000):
    """Check if port is already in use"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  Port {port} is already in use")
            return True
        else:
            print(f"✅ Port {port} is available")
            return False
    except Exception as e:
        print(f"❌ Error checking port {port}: {e}")
        return True

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Web Crawler Server Test")
    print("=" * 60)
    
    # Test 1: Check if Flask app works
    if not test_flask_app():
        print("❌ Flask application test failed")
        return
    
    # Test 2: Check port availability
    port = 5000
    if check_port_usage(port):
        print(f"💡 Trying alternative port 5001...")
        port = 5001
        if check_port_usage(port):
            print("❌ Both ports 5000 and 5001 are in use")
            print("💡 Please stop other applications or use a different port")
            return
    
    # Test 3: Start test server
    server_thread = start_test_server(port=port)
    
    # Test 4: Test connection
    if test_server_connection(port=port):
        print("✅ Server is working correctly!")
        print(f"🌐 You can now access the application at: http://localhost:{port}")
        
        # Keep server running for manual testing
        print("⏳ Server will run for 30 seconds for manual testing...")
        print("   Open your browser and go to the URL above")
        print("   Press Ctrl+C to stop early")
        
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n⏹️  Stopping server...")
    else:
        print("❌ Server connection test failed")
    
    print("=" * 60)
    print("🧪 Test completed")

if __name__ == "__main__":
    main() 