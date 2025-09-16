#!/usr/bin/env python3
"""
Demo script for Tiger Options Delta Manager
"""

import webbrowser
import time
import subprocess
import sys
import os
from pathlib import Path

def check_server_running():
    """Check if the server is running"""
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the Tiger Options Trading Service"""
    print("🚀 Starting Tiger Options Trading Service...")
    
    # Check if server is already running
    if check_server_running():
        print("✅ Server is already running!")
        return True
    
    # Start server in background
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen([sys.executable, "test_server.py"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Unix/Linux/Mac
            subprocess.Popen([sys.executable, "test_server.py"])
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            if check_server_running():
                print("✅ Server started successfully!")
                return True
            time.sleep(1)
            print(f"   Waiting... ({i+1}/30)")
        
        print("❌ Server failed to start within 30 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def open_delta_manager():
    """Open the Delta Manager in browser"""
    url = "http://localhost:8000/static/delta-manager.html"
    print(f"🌐 Opening Delta Manager: {url}")
    
    try:
        webbrowser.open(url)
        print("✅ Delta Manager opened in browser!")
        return True
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"   Please manually open: {url}")
        return False

def show_demo_info():
    """Show demo information"""
    print("\n" + "="*60)
    print("🐅 Tiger Options Delta Manager Demo")
    print("="*60)
    print()
    print("📋 Demo Features:")
    print("  • Real-time account summary with Delta statistics")
    print("  • Option positions monitoring")
    print("  • Pending orders management")
    print("  • Trade history tracking")
    print("  • One-click position closing")
    print("  • Order cancellation")
    print("  • TradingView alert message generation")
    print()
    print("🎯 How to Use:")
    print("  1. Select an account from the dropdown")
    print("  2. View Delta statistics in the top cards")
    print("  3. Monitor positions, orders, and trades in tables")
    print("  4. Use refresh buttons to update data")
    print("  5. Click action buttons to manage positions/orders")
    print("  6. Generate TradingView alerts with the copy button")
    print()
    print("💡 Note: Currently running in MOCK mode with simulated data")
    print("   In production, connect to real Tiger Brokers API")
    print()

def main():
    """Main demo function"""
    show_demo_info()
    
    # Start server
    if not start_server():
        print("\n❌ Demo failed: Could not start server")
        return
    
    # Wait a moment for server to be fully ready
    time.sleep(2)
    
    # Open Delta Manager
    if not open_delta_manager():
        print("\n❌ Demo failed: Could not open browser")
        return
    
    print("\n" + "="*60)
    print("🎉 Demo Started Successfully!")
    print("="*60)
    print()
    print("📖 What you can do now:")
    print("  • The Delta Manager should be open in your browser")
    print("  • Select 'account_1' from the account dropdown")
    print("  • Explore the interface and try different features")
    print("  • Check the mock data in positions, orders, and trades")
    print("  • Try generating a TradingView alert message")
    print()
    print("🔧 API Endpoints Available:")
    print("  • http://localhost:8000/docs - API Documentation")
    print("  • http://localhost:8000/api/accounts - Account List")
    print("  • http://localhost:8000/api/health - Health Check")
    print()
    print("⚠️  To stop the demo:")
    print("   Press Ctrl+C in the server terminal window")
    print()
    print("📚 For more information, see: DELTA_MANAGER_README.md")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        sys.exit(1)
