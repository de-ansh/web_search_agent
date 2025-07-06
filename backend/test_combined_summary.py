#!/usr/bin/env python3
"""
Test script to demonstrate the Web Search Agent API with both individual and combined summary modes
"""

import requests
import json
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def test_api_endpoint(url, data, description):
    """Test an API endpoint and display results"""
    console.print(f"\n🔍 {description}", style="bold blue")
    console.print(f"Endpoint: {url}")
    console.print(f"Request: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Display basic info
            console.print(f"✅ Status: {response.status_code}", style="green")
            console.print(f"Query Valid: {result.get('is_valid', 'N/A')}")
            console.print(f"Found Similar: {result.get('found_similar', 'N/A')}")
            console.print(f"Results Count: {len(result.get('results', []))}")
            
            # Display results in a table
            if result.get('results'):
                table = Table(title="Search Results")
                table.add_column("Title", style="cyan", width=40)
                table.add_column("URL", style="blue", width=50)
                
                # Add columns based on summary type
                if 'combined_summary' in result and result['combined_summary']:
                    table.add_column("Content Length", style="yellow", width=15)
                    table.add_column("Scraped", style="green", width=10)
                else:
                    table.add_column("Summary", style="magenta", width=60)
                    table.add_column("Method", style="yellow", width=15)
                    table.add_column("Confidence", style="green", width=10)
                
                for item in result['results']:
                    if 'combined_summary' in result and result['combined_summary']:
                        # Combined summary mode
                        table.add_row(
                            item.get('title', 'N/A')[:40] + "..." if len(item.get('title', '')) > 40 else item.get('title', 'N/A'),
                            item.get('url', 'N/A')[:50] + "..." if len(item.get('url', '')) > 50 else item.get('url', 'N/A'),
                            str(item.get('content_length', 'N/A')),
                            "✅" if item.get('scraped_successfully', False) else "❌"
                        )
                    else:
                        # Individual summary mode
                        table.add_row(
                            item.get('title', 'N/A')[:40] + "..." if len(item.get('title', '')) > 40 else item.get('title', 'N/A'),
                            item.get('url', 'N/A')[:50] + "..." if len(item.get('url', '')) > 50 else item.get('url', 'N/A'),
                            item.get('summary', 'N/A')[:60] + "..." if len(item.get('summary', '')) > 60 else item.get('summary', 'N/A'),
                            item.get('summary_method', 'N/A'),
                            str(item.get('confidence', 'N/A'))
                        )
                
                console.print(table)
            
            # Display combined summary if available
            if result.get('combined_summary'):
                console.print("\n📝 Combined Summary:", style="bold magenta")
                console.print(Panel(result['combined_summary'], title="Combined Summary", border_style="magenta"))
            
            console.print(f"Message: {result.get('message', 'N/A')}")
            
        else:
            console.print(f"❌ Status: {response.status_code}", style="red")
            console.print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        console.print(f"❌ Request failed: {e}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")

def main():
    """Run comprehensive API tests"""
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    console.print("🏥 Testing Health Endpoint", style="bold green")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ Server is healthy!", style="green")
        else:
            console.print("❌ Server health check failed", style="red")
            return
    except Exception as e:
        console.print(f"❌ Cannot connect to server: {e}", style="red")
        console.print("Please make sure the server is running with: python start_server.py")
        return
    
    # Test queries
    test_queries = [
        {
            "query": "machine learning algorithms 2024",
            "description": "Individual Summary Mode - Machine Learning Query"
        },
        {
            "query": "renewable energy storage solutions",
            "description": "Combined Summary Mode - Energy Storage Query"
        },
        {
            "query": "walk my dog",
            "description": "Invalid Query Test - Personal Task"
        }
    ]
    
    console.print("\n" + "="*80, style="bold")
    console.print("🚀 Web Search Agent API Comprehensive Test", style="bold cyan")
    console.print("="*80, style="bold")
    
    for i, query_data in enumerate(test_queries):
        console.print(f"\n{'='*20} Test {i+1} {'='*20}", style="bold yellow")
        
        if i == 0:
            # Test individual summary mode
            test_api_endpoint(
                f"{base_url}/search",
                {
                    "query": query_data["query"],
                    "summary_type": "individual"
                },
                query_data["description"]
            )
        elif i == 1:
            # Test combined summary mode
            test_api_endpoint(
                f"{base_url}/search/combined",
                {"query": query_data["query"]},
                query_data["description"]
            )
        else:
            # Test invalid query
            test_api_endpoint(
                f"{base_url}/search",
                {"query": query_data["query"]},
                query_data["description"]
            )
        
        if i < len(test_queries) - 1:
            console.print("\n⏳ Waiting 3 seconds before next test...", style="dim")
            time.sleep(3)
    
    console.print("\n" + "="*80, style="bold")
    console.print("🎉 All tests completed!", style="bold green")
    console.print("="*80, style="bold")
    
    # Display API documentation info
    console.print("\n📚 API Documentation:", style="bold blue")
    console.print(f"• Interactive docs: {base_url}/docs")
    console.print(f"• OpenAPI spec: {base_url}/openapi.json")
    console.print(f"• Health check: {base_url}/health")
    
    console.print("\n🔧 Available Endpoints:", style="bold blue")
    console.print("• POST /search - Main search with individual/combined summary")
    console.print("• POST /search/combined - Dedicated combined summary endpoint")
    console.print("• GET /stats - Query statistics")
    console.print("• GET /history - Query history")

if __name__ == "__main__":
    main() 