#!/usr/bin/env python3
"""
Quick test script to demonstrate the Web Search Agent API features
"""

import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_endpoint(url, data, description):
    """Test an API endpoint"""
    console.print(f"\n🔍 {description}", style="bold blue")
    console.print(f"Endpoint: {url}")
    console.print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ Status: {response.status_code}", style="green")
            console.print(f"Query Valid: {result.get('is_valid')}")
            console.print(f"Found Similar: {result.get('found_similar')}")
            console.print(f"Results Count: {len(result.get('results', []))}")
            console.print(f"Message: {result.get('message')}")
            
            # Show combined summary if available
            if result.get('combined_summary'):
                console.print("\n📝 Combined Summary:", style="bold magenta")
                console.print(Panel(result['combined_summary'], border_style="magenta"))
            
            # Show first few results
            if result.get('results'):
                console.print("\n📊 First 2 Results:", style="bold cyan")
                for i, item in enumerate(result['results'][:2]):
                    console.print(f"{i+1}. {item.get('title', 'N/A')}")
                    if 'summary' in item:
                        console.print(f"   Summary: {item['summary'][:100]}...")
                        console.print(f"   Method: {item.get('summary_method', 'N/A')}")
                        console.print(f"   Confidence: {item.get('confidence', 'N/A')}")
                    else:
                        console.print(f"   Content Length: {item.get('content_length', 'N/A')}")
                        console.print(f"   Scraped: {'✅' if item.get('scraped_successfully') else '❌'}")
                    console.print()
            
        else:
            console.print(f"❌ Status: {response.status_code}", style="red")
            console.print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        console.print("⏰ Request timed out (>10s)", style="yellow")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

def main():
    """Run quick tests"""
    base_url = "http://localhost:8000"
    
    console.print("🚀 Web Search Agent API Quick Test", style="bold cyan")
    console.print("="*50, style="bold")
    
    # Test 1: Health check
    console.print("\n1. Health Check", style="bold green")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ Server is healthy!", style="green")
        else:
            console.print("❌ Server not healthy", style="red")
            return
    except Exception as e:
        console.print(f"❌ Cannot connect to server: {e}", style="red")
        return
    
    # Test 2: Invalid query (fast)
    test_endpoint(
        f"{base_url}/search",
        {"query": "walk my dog"},
        "2. Invalid Query Test (should be fast)"
    )
    
    # Test 3: Valid query with individual summary (may timeout)
    test_endpoint(
        f"{base_url}/search",
        {"query": "AI trends", "summary_type": "individual"},
        "3. Individual Summary Mode (may timeout due to web scraping)"
    )
    
    # Test 4: Valid query with combined summary (may timeout)
    test_endpoint(
        f"{base_url}/search/combined",
        {"query": "web development"},
        "4. Combined Summary Mode (may timeout due to web scraping)"
    )
    
    console.print("\n" + "="*50, style="bold")
    console.print("🎉 Tests completed!", style="bold green")
    console.print("\n📚 API Documentation available at:", style="bold blue")
    console.print(f"   {base_url}/docs")

if __name__ == "__main__":
    main() 