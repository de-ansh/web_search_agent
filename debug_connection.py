#!/usr/bin/env python3
"""
Debug connection between frontend and backend
"""

import requests
import time

def test_backend_direct():
    """Test direct backend connection"""
    print("🧪 Testing Direct Backend Connection")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Direct backend health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Direct backend failed: {e}")
        return False

def test_frontend_proxy():
    """Test frontend proxy"""
    print("\n🧪 Testing Frontend Proxy")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:3000/api/health", timeout=10)
        print(f"✅ Frontend proxy health: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Frontend proxy failed: {e}")
        return False

def test_research_endpoints():
    """Test research endpoints"""
    print("\n🧪 Testing Research Endpoints")
    print("=" * 35)
    
    # Test direct backend
    try:
        response = requests.get("http://localhost:8000/research/status", timeout=5)
        print(f"✅ Direct research status: {response.status_code}")
    except Exception as e:
        print(f"❌ Direct research status failed: {e}")
    
    # Test through frontend proxy
    try:
        response = requests.get("http://localhost:3000/api/research/status", timeout=10)
        print(f"✅ Proxy research status: {response.status_code}")
    except Exception as e:
        print(f"❌ Proxy research status failed: {e}")

def main():
    print("🔍 Connection Diagnostic Tool")
    print("=" * 50)
    
    backend_ok = test_backend_direct()
    if not backend_ok:
        print("\n❌ Backend is not running!")
        print("Start it with: cd backend && uv run python quick_start.py")
        return
    
    frontend_ok = test_frontend_proxy()
    if not frontend_ok:
        print("\n❌ Frontend proxy is not working!")
        print("Make sure frontend is running: cd frontend && npm run dev")
        return
    
    test_research_endpoints()
    
    print("\n🎉 All connections working!")
    print("If frontend still shows 'Disconnected', try:")
    print("1. Refresh the browser page")
    print("2. Check browser console for errors")
    print("3. Clear browser cache")

if __name__ == "__main__":
    main()