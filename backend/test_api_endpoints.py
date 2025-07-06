#!/usr/bin/env python3
"""
Test script for Web Search Agent API endpoints
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_individual_search(query):
    """Test individual summary search"""
    print(f"\n🔍 Testing Individual Search: '{query}'")
    try:
        payload = {
            "query": query,
            "summary_type": "individual"
        }
        
        response = requests.post(f"{BASE_URL}/search", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Valid: {data['is_valid']}")
            print(f"Found Similar: {data['found_similar']}")
            print(f"Results Count: {len(data['results'])}")
            print(f"Message: {data['message']}")
            
            # Show first result as example
            if data['results']:
                first_result = data['results'][0]
                print(f"\nFirst Result:")
                print(f"  Title: {first_result.get('title', 'N/A')}")
                print(f"  URL: {first_result.get('url', 'N/A')[:50]}...")
                print(f"  Summary: {first_result.get('summary', 'N/A')[:100]}...")
                print(f"  Method: {first_result.get('summary_method', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Individual search failed: {e}")

def test_combined_search(query):
    """Test combined summary search"""
    print(f"\n🔗 Testing Combined Search: '{query}'")
    try:
        payload = {
            "query": query,
            "summary_type": "combined"
        }
        
        response = requests.post(f"{BASE_URL}/search", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Valid: {data['is_valid']}")
            print(f"Found Similar: {data['found_similar']}")
            print(f"Results Count: {len(data['results'])}")
            print(f"Message: {data['message']}")
            
            # Show combined summary
            if data.get('combined_summary'):
                print(f"\n📝 Combined Summary:")
                print(data['combined_summary'])
            
            # Show result metadata
            print(f"\n📊 Results Overview:")
            for i, result in enumerate(data['results'], 1):
                print(f"  {i}. {result.get('title', 'N/A')}")
                print(f"     Content Length: {result.get('content_length', 0)} chars")
                print(f"     Scraped Successfully: {result.get('scraped_successfully', False)}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Combined search failed: {e}")

def test_combined_endpoint(query):
    """Test dedicated combined endpoint"""
    print(f"\n🎯 Testing Dedicated Combined Endpoint: '{query}'")
    try:
        payload = {"query": query}
        
        response = requests.post(f"{BASE_URL}/search/combined", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Combined Summary Available: {bool(data.get('combined_summary'))}")
            
            if data.get('combined_summary'):
                print(f"\n📝 Combined Summary:")
                print(data['combined_summary'])
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Combined endpoint test failed: {e}")

def test_stats():
    """Test stats endpoint"""
    print(f"\n📊 Testing Stats Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Stats: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Stats test failed: {e}")

def test_history():
    """Test history endpoint"""
    print(f"\n📝 Testing History Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/history?limit=3")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"History entries: {len(data.get('data', []))}")
            if data.get('data'):
                for i, entry in enumerate(data['data'][:2], 1):
                    print(f"  {i}. Query: {entry.get('query', 'N/A')}")
                    print(f"     Timestamp: {entry.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ History test failed: {e}")

def main():
    """Run all API tests"""
    print("🚀 Web Search Agent API Test Suite")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ API server is not running. Please start it with:")
        print("   cd backend && uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Test query
    test_query = "artificial intelligence trends 2024"
    
    # Test individual search
    test_individual_search(test_query)
    
    # Wait a bit
    time.sleep(2)
    
    # Test combined search
    test_combined_search(test_query)
    
    # Test dedicated combined endpoint
    test_combined_endpoint("renewable energy developments")
    
    # Test other endpoints
    test_stats()
    test_history()
    
    print("\n✅ API testing completed!")
    print("\n💡 Usage Examples:")
    print("Individual summaries:")
    print('  curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d \'{"query": "your query", "summary_type": "individual"}\'')
    print("\nCombined summary:")
    print('  curl -X POST "http://localhost:8000/search/combined" -H "Content-Type: application/json" -d \'{"query": "your query"}\'')

if __name__ == "__main__":
    main() 