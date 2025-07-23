#!/usr/bin/env python3
"""
Example usage of the enhanced web scraping with Gemini AI
"""

import asyncio
import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"  # Adjust if your API runs on different port

def make_api_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make API request to the enhanced research service"""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return {"error": str(e)}

def example_enhanced_research():
    """Example of comprehensive research using enhanced endpoint"""
    print("🔍 Example 1: Enhanced Research")
    print("=" * 40)
    
    # Research request
    request_data = {
        "query": "artificial intelligence in healthcare 2024",
        "max_sources": 4,
        "summary_length": 150,
        "use_playwright": True,
        "ai_method": "gemini"
    }
    
    print(f"Query: {request_data['query']}")
    print("Making API request...")
    
    result = make_api_request("/research/enhanced", request_data)
    
    if "error" in result:
        print(f"❌ Request failed: {result['error']}")
        return
    
    # Display results
    print(f"✅ Success: {result['success']}")
    print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
    print(f"📊 Sources: {result['successful_scrapes']}/{result['total_sources']}")
    print(f"🤖 AI Method: {result['method_used']}")
    print()
    
    print("📝 Combined Summary:")
    print(f"   {result['combined_summary']}")
    print()
    
    print("📚 Individual Sources:")
    for i, summary in enumerate(result['individual_summaries'][:2], 1):
        print(f"   {i}. {summary['source_title'][:60]}...")
        print(f"      URL: {summary['source_url']}")
        print(f"      Method: {summary['method']} | Confidence: {summary['confidence']:.2f}")
        print(f"      Summary: {summary['summary'][:100]}...")
        print()

def example_quick_research():
    """Example of quick research for faster results"""
    print("🚀 Example 2: Quick Research")
    print("=" * 40)
    
    # Quick research request
    request_data = {
        "query": "Python web scraping best practices",
        "max_sources": 3,
        "ai_method": "gemini"
    }
    
    print(f"Query: {request_data['query']}")
    print("Making quick API request...")
    
    result = make_api_request("/research/quick", request_data)
    
    if "error" in result:
        print(f"❌ Request failed: {result['error']}")
        return
    
    # Display results
    print(f"✅ Success: {result['success']}")
    print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
    print(f"📝 Summary: {result['combined_summary'][:200]}...")
    print()

def example_service_status():
    """Example of checking service status"""
    print("📊 Example 3: Service Status")
    print("=" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/research/status", timeout=10)
        response.raise_for_status()
        status = response.json()
        
        print("Service Status:")
        research_status = status.get('research_service', {})
        for key, value in research_status.items():
            print(f"   {key}: {value}")
        
        print("\nEnhanced Features:")
        features = status.get('enhanced_features', {})
        for feature, enabled in features.items():
            status_icon = "✅" if enabled else "❌"
            print(f"   {status_icon} {feature}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Status request failed: {e}")

def example_comparison():
    """Example comparing different AI methods"""
    print("🤖 Example 4: AI Method Comparison")
    print("=" * 40)
    
    query = "renewable energy storage technologies"
    methods = ["gemini", "openai", "extractive"]
    
    for method in methods:
        print(f"\nTesting with {method.upper()}:")
        print("-" * 20)
        
        request_data = {
            "query": query,
            "max_sources": 2,
            "summary_length": 100,
            "use_playwright": False,  # Faster for comparison
            "ai_method": method
        }
        
        result = make_api_request("/research/quick", request_data)
        
        if "error" in result:
            print(f"❌ {method} failed: {result['error']}")
            continue
        
        print(f"⏱️  Time: {result['processing_time']:.2f}s")
        print(f"🤖 Method: {result['method_used']}")
        print(f"📝 Summary: {result['combined_summary'][:150]}...")

async def example_async_usage():
    """Example of using the service in an async application"""
    print("🔄 Example 5: Async Integration")
    print("=" * 40)
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        request_data = {
            "query": "machine learning model deployment",
            "max_sources": 3,
            "ai_method": "gemini"
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/research/quick",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                result = await response.json()
                
                print(f"✅ Async request completed")
                print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
                print(f"📝 Summary: {result['combined_summary'][:100]}...")
                
        except Exception as e:
            print(f"❌ Async request failed: {e}")

def main():
    """Run all examples"""
    print("🚀 Enhanced Web Scraping Examples")
    print("=" * 50)
    print()
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not running. Please start the server first:")
            print("   cd backend && python -m uvicorn src.api.main:app --reload")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API. Please start the server first:")
        print("   cd backend && python -m uvicorn src.api.main:app --reload")
        return
    
    print("✅ API is running. Starting examples...\n")
    
    # Run examples
    try:
        example_enhanced_research()
        print("\n" + "="*50 + "\n")
        
        example_quick_research()
        print("\n" + "="*50 + "\n")
        
        example_service_status()
        print("\n" + "="*50 + "\n")
        
        example_comparison()
        print("\n" + "="*50 + "\n")
        
        # Run async example
        asyncio.run(example_async_usage())
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Example failed: {e}")
    
    print("\n🎉 Examples completed!")
    print("\nNext steps:")
    print("1. Integrate these endpoints into your application")
    print("2. Customize parameters based on your needs")
    print("3. Set up proper error handling for production use")

if __name__ == "__main__":
    main()