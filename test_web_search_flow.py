#!/usr/bin/env python3
"""
Test script to verify the complete web search flow
"""

import requests
import json
import time

def test_backend_health():
    """Test backend health"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data['status']}")
            print(f"✅ Agent Ready: {data['agent_ready']}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_web_search():
    """Test web search functionality"""
    try:
        print("\n🔍 Testing web search with query: 'What is artificial intelligence?'")
        
        payload = {
            "query": "What is artificial intelligence?",
            "use_web_search": True,
            "search_threshold": 0.5
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/agent/chat",
            json=payload,
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search completed in {end_time - start_time:.2f}s")
            print(f"✅ Method used: {data['method_used']}")
            print(f"✅ Sources found: {len(data['sources'])}")
            print(f"✅ Confidence score: {data['confidence_score']:.2f}")
            
            # Check if we have real web sources
            web_sources = [s for s in data['sources'] if s.get('source_type') == 'web_search']
            print(f"✅ Web sources: {len(web_sources)}")
            
            if web_sources:
                print("\n📄 Sample web source:")
                sample = web_sources[0]
                print(f"   Title: {sample['title'][:100]}...")
                print(f"   URL: {sample['url']}")
                print(f"   Content length: {len(sample.get('content', ''))}")
                print(f"   Score: {sample.get('score', 0):.2f}")
            
            # Check response content
            if data['content'] and len(data['content']) > 100:
                print(f"\n💬 Response preview: {data['content'][:200]}...")
                return True
            else:
                print("❌ Response content is too short or empty")
                return False
        else:
            print(f"❌ Search request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Web search test error: {e}")
        return False

def test_frontend_connection():
    """Test frontend connection"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Web Search Agent Flow")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_health()
    
    # Test frontend
    frontend_ok = test_frontend_connection()
    
    # Test web search if backend is working
    if backend_ok:
        search_ok = test_web_search()
    else:
        search_ok = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Backend: {'✅ OK' if backend_ok else '❌ FAIL'}")
    print(f"Frontend: {'✅ OK' if frontend_ok else '❌ FAIL'}")
    print(f"Web Search: {'✅ OK' if search_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok and search_ok:
        print("\n🎉 All tests passed! The web search flow is working correctly.")
        print("You can now use the frontend at http://localhost:3000")
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")