#!/usr/bin/env python3
"""
Simple health check script to test if the app can start
"""
import os
import sys

def main():
    print("🔍 Health Check Starting...")
    print(f"Python version: {sys.version}")
    print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
    
    try:
        print("📦 Testing imports...")
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        print("🧪 Testing app creation...")
        print(f"App title: {app.title}")
        print("✅ App is healthy")
        
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)