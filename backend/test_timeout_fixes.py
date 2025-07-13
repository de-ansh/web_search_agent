#!/usr/bin/env python3
"""
Test script to verify timeout fixes and enhanced scraper functionality
"""

import asyncio
import time
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_api_health():
    """Test API health check"""
    console.print("🏥 Testing API Health Check", style="bold green")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ API is healthy", style="green")
            return True
        else:
            console.print(f"❌ API health check failed: {response.status_code}", style="red")
            return False
    except Exception as e:
        console.print(f"❌ Cannot connect to API: {e}", style="red")
        return False

def test_enhanced_search(query: str, description: str):
    """Test enhanced search endpoint"""
    console.print(f"\n🔍 {description}", style="bold blue")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/search",
            json={"query": query},
            timeout=200  # 200 seconds to test enhanced processing
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Create results table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Status", "✅ Success")
            table.add_row("Duration", f"{duration:.2f}s")
            table.add_row("Valid Query", str(result.get('is_valid', 'N/A')))
            table.add_row("Found Similar", str(result.get('found_similar', 'N/A')))
            table.add_row("Results Count", str(len(result.get('results', []))))
            table.add_row("Has Summary", "Yes" if result.get('combined_summary') else "No")
            
            if result.get('combined_summary'):
                summary_length = len(result['combined_summary'])
                table.add_row("Summary Length", f"{summary_length} chars")
            
            console.print(table)
            
            # Show sample results
            results = result.get('results', [])
            if results:
                console.print(f"\n📊 Sample Results:")
                for i, res in enumerate(results[:2]):
                    console.print(f"  {i+1}. {res.get('title', 'N/A')[:60]}...")
                    console.print(f"     URL: {res.get('url', 'N/A')}")
                    console.print(f"     Scraped: {'✅' if res.get('scraped_successfully') else '❌'}")
                    console.print(f"     Content Length: {res.get('content_length', 0)}")
                    if res.get('search_mode'):
                        console.print(f"     Search Mode: {res.get('search_mode')}")
            
            return True
            
        else:
            console.print(f"❌ Search failed: {response.status_code}", style="red")
            console.print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        console.print(f"⏰ Enhanced search timed out after 200s", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        return False

def test_fast_search(query: str, description: str):
    """Test fast search endpoint"""
    console.print(f"\n🚀 {description}", style="bold yellow")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/search/fast",
            json={"query": query},
            timeout=70  # 70 seconds for fast search
        )
        end_time = time.time()
        
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Create results table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")
            
            table.add_row("Status", "✅ Success")
            table.add_row("Duration", f"{duration:.2f}s")
            table.add_row("Valid Query", str(result.get('is_valid', 'N/A')))
            table.add_row("Found Similar", str(result.get('found_similar', 'N/A')))
            table.add_row("Results Count", str(len(result.get('results', []))))
            table.add_row("Has Summary", "Yes" if result.get('combined_summary') else "No")
            
            console.print(table)
            
            # Check if results have fast search mode indicator
            results = result.get('results', [])
            if results and results[0].get('search_mode') == 'fast':
                console.print("✅ Fast search mode confirmed", style="green")
            
            return True
            
        else:
            console.print(f"❌ Fast search failed: {response.status_code}", style="red")
            console.print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        console.print(f"⏰ Fast search timed out after 70s", style="yellow")
        return False
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        return False

def test_timeout_scenarios():
    """Test various timeout scenarios"""
    console.print("\n⏰ Testing Timeout Scenarios", style="bold red")
    
    # Test with a query that might cause timeouts
    difficult_queries = [
        "enterprise software architecture patterns microservices",
        "quantum computing algorithms machine learning applications",
        "blockchain consensus mechanisms proof of stake",
    ]
    
    results = []
    for query in difficult_queries:
        console.print(f"\nTesting difficult query: {query[:40]}...")
        
        # Test enhanced search
        enhanced_success = test_enhanced_search(query, f"Enhanced Search: {query[:30]}...")
        
        # Test fast search
        fast_success = test_fast_search(query, f"Fast Search: {query[:30]}...")
        
        results.append({
            "query": query[:40] + "...",
            "enhanced": enhanced_success,
            "fast": fast_success
        })
    
    # Summary table
    console.print("\n📊 Timeout Test Summary", style="bold cyan")
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Query", style="cyan")
    summary_table.add_column("Enhanced Search", style="green")
    summary_table.add_column("Fast Search", style="yellow")
    
    for result in results:
        enhanced_status = "✅ Success" if result["enhanced"] else "❌ Failed"
        fast_status = "✅ Success" if result["fast"] else "❌ Failed"
        summary_table.add_row(result["query"], enhanced_status, fast_status)
    
    console.print(summary_table)

def main():
    """Run comprehensive timeout tests"""
    console.print("🛠️ Web Search Agent Timeout Fix Verification", style="bold green")
    console.print("=" * 60)
    
    # Check API health first
    if not test_api_health():
        console.print("\n❌ API is not available. Please start the backend server first.", style="red")
        console.print("Run: cd backend && python start_server.py")
        return
    
    # Test enhanced search with a simple query
    console.print("\n" + "=" * 60)
    success1 = test_enhanced_search(
        "artificial intelligence trends 2024",
        "Enhanced Search Test - AI Trends"
    )
    
    # Test fast search with the same query
    console.print("\n" + "=" * 60)
    success2 = test_fast_search(
        "artificial intelligence trends 2024", 
        "Fast Search Test - AI Trends"
    )
    
    # Test timeout scenarios
    console.print("\n" + "=" * 60)
    test_timeout_scenarios()
    
    # Final summary
    console.print("\n" + "=" * 60)
    console.print("🎯 Test Summary", style="bold green")
    
    if success1 and success2:
        console.print("✅ All basic tests passed! Timeout fixes appear to be working.", style="green")
        console.print("\n💡 Key improvements:")
        console.print("  • Frontend timeout increased to 3 minutes")
        console.print("  • Backend parallel processing timeout increased to 45 seconds")
        console.print("  • Fast search fallback endpoint added")
        console.print("  • Enhanced web scraper with retry mechanisms enabled")
        console.print("  • Progressive timeout escalation implemented")
    else:
        console.print("⚠️ Some tests failed. Check the logs above for details.", style="yellow")
    
    console.print(f"\n🔧 Frontend changes:")
    console.print(f"  • Progressive timeout handling with fallback")
    console.print(f"  • Better error messages")
    console.print(f"  • Enhanced search progress indicators")

if __name__ == "__main__":
    main() 