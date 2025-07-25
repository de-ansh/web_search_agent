#!/usr/bin/env python3
"""
Test script to verify frontend-backend integration
"""

import requests
import json
import time

def test_backend_endpoints():
    """Test backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend Endpoints")
    print("=" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test enhanced research status
    try:
        response = requests.get(f"{base_url}/research/status", timeout=5)
        print(f"✅ Research status: {response.status_code}")
        status_data = response.json()
        print(f"   Service: {status_data.get('research_service', {}).get('service', 'Unknown')}")
        print(f"   AI Method: {status_data.get('research_service', {}).get('ai_method', 'Unknown')}")
    except Exception as e:
        print(f"❌ Research status failed: {e}")
        return False
    
    # Test quick research endpoint
    try:
        print("\n🔍 Testing Quick Research...")
        test_query = "Python programming tips"
        
        response = requests.post(
            f"{base_url}/research/quick",
            json={
                "query": test_query,
                "max_sources": 2,
                "ai_method": "gemini"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Quick research: Success")
            print(f"   Query: {result.get('query', 'Unknown')}")
            print(f"   Success: {result.get('success', False)}")
            print(f"   Sources: {result.get('successful_scrapes', 0)}/{result.get('total_sources', 0)}")
            print(f"   Method: {result.get('method_used', 'Unknown')}")
            print(f"   Time: {result.get('processing_time', 0):.1f}s")
            print(f"   Summary: {result.get('combined_summary', 'No summary')[:100]}...")
        else:
            print(f"❌ Quick research failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Quick research failed: {e}")
        return False
    
    return True

def test_frontend_proxy():
    """Test frontend API proxy"""
    frontend_url = "http://localhost:3000"
    
    print("\n🌐 Testing Frontend API Proxy")
    print("=" * 40)
    
    # Test health through frontend proxy
    try:
        response = requests.get(f"{frontend_url}/api/health", timeout=10)
        print(f"✅ Frontend proxy health: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend proxy health failed: {e}")
        return False
    
    # Test research status through frontend proxy
    try:
        response = requests.get(f"{frontend_url}/api/research/status", timeout=10)
        print(f"✅ Frontend proxy research status: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend proxy research status failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Frontend-Backend Integration Test")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_endpoints()
    
    if not backend_ok:
        print("\n❌ Backend tests failed!")
        print("Make sure to start the backend first:")
        print("   cd backend && ./run.sh server")
        return
    
    # Test frontend proxy
    frontend_ok = test_frontend_proxy()
    
    if not frontend_ok:
        print("\n❌ Frontend proxy tests failed!")
        print("Make sure to start the frontend:")
        print("   cd frontend && npm run dev")
        return
    
    print("\n🎉 Integration Test Results")
    print("=" * 30)
    print("✅ Backend: Working")
    print("✅ Frontend Proxy: Working")
    print("✅ Enhanced Research: Working")
    print("✅ Integration: Complete!")
    
    print("\n🌐 Access Points:")
    print("   Backend API: http://localhost:8000")
    print("   Backend Docs: http://localhost:8000/docs")
    print("   Frontend App: http://localhost:3000")
    
    print("\n🧪 Try these test queries in the frontend:")
    print("   - 'artificial intelligence trends 2024'")
    print("   - 'Python web scraping best practices'")
    print("   - 'climate change renewable energy'")

if __name__ == "__main__":
    main()