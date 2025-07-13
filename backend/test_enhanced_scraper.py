#!/usr/bin/env python3
"""
Test script for the enhanced web scraper with comprehensive improvements
"""

import asyncio
import time
import logging
from rich.console import Console
from rich.table import Table
from src.core.web_scraper import EnhancedWebScraper, FailureType

# Set up logging
logging.basicConfig(level=logging.INFO)
console = Console()

async def test_basic_functionality():
    """Test basic scraping functionality"""
    console.print("\n🔍 Testing Basic Scraping Functionality", style="bold blue")
    
    async with EnhancedWebScraper() as scraper:
        # Test search functionality
        console.print("Testing search functionality...")
        results = await scraper.search_google("python web scraping", max_results=3)
        
        console.print(f"Found {len(results)} search results")
        for i, result in enumerate(results[:2]):
            console.print(f"  {i+1}. {result['title'][:60]}...")
            console.print(f"     {result['url']}")
        
        # Test single page scraping
        if results:
            console.print(f"\nTesting page scraping on: {results[0]['url']}")
            start_time = time.time()
            page_content = await scraper.scrape_page_content(results[0]["url"])
            end_time = time.time()
            
            console.print(f"Scraped {len(page_content['content'])} characters in {end_time - start_time:.2f}s")
            console.print(f"Attempts: {page_content['metadata'].get('attempts', 1)}")
            console.print(f"Title: {page_content['metadata']['title'][:50]}...")

async def test_retry_mechanism():
    """Test retry mechanism with problematic URLs"""
    console.print("\n🔄 Testing Retry Mechanism", style="bold blue")
    
    async with EnhancedWebScraper(max_retries=3) as scraper:
        # Test with a slow/unreliable URL
        test_urls = [
            "https://httpstat.us/503",  # Returns 503 error
            "https://httpstat.us/timeout",  # Timeout
            "https://httpstat.us/200?sleep=2000",  # Slow response
        ]
        
        for url in test_urls:
            console.print(f"\nTesting retry with: {url}")
            try:
                start_time = time.time()
                result = await scraper.scrape_page_content_with_retry(url)
                end_time = time.time()
                
                console.print(f"✅ Success after {result['metadata'].get('attempts', 1)} attempts")
                console.print(f"   Duration: {end_time - start_time:.2f}s")
                console.print(f"   Content length: {len(result['content'])}")
                
            except Exception as e:
                console.print(f"❌ Failed after retries: {str(e)}")

async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    console.print("\n🚦 Testing Circuit Breaker", style="bold blue")
    
    async with EnhancedWebScraper(enable_circuit_breaker=True) as scraper:
        # Test with a consistently failing URL
        failing_url = "https://httpstat.us/500"
        
        console.print(f"Testing circuit breaker with: {failing_url}")
        
        for i in range(5):
            try:
                console.print(f"\nAttempt {i+1}:")
                start_time = time.time()
                result = await scraper.scrape_page_content_with_retry(failing_url)
                end_time = time.time()
                
                console.print(f"✅ Unexpected success in {end_time - start_time:.2f}s")
                
            except Exception as e:
                console.print(f"❌ Failed: {str(e)}")
                
                # Check circuit breaker state
                states = scraper.get_circuit_breaker_states()
                for domain, state in states.items():
                    if "httpstat.us" in domain:
                        console.print(f"   Circuit breaker state: {state}")
                        break

async def test_rate_limiting():
    """Test rate limiting functionality"""
    console.print("\n⚡ Testing Rate Limiting", style="bold blue")
    
    async with EnhancedWebScraper(enable_rate_limiting=True) as scraper:
        # Test multiple requests to same domain
        test_url = "https://httpstat.us/200"
        
        console.print(f"Testing rate limiting with multiple requests to: {test_url}")
        
        times = []
        for i in range(3):
            start_time = time.time()
            try:
                result = await scraper.scrape_page_content_with_retry(test_url)
                end_time = time.time()
                times.append(end_time - start_time)
                console.print(f"Request {i+1}: {end_time - start_time:.2f}s")
                
            except Exception as e:
                console.print(f"Request {i+1} failed: {str(e)}")
        
        # Check if rate limiting is working (later requests should be slower)
        if len(times) >= 2:
            if times[1] > times[0]:
                console.print("✅ Rate limiting appears to be working (increasing delays)")
            else:
                console.print("ℹ️  Rate limiting may not be triggered (fast responses)")

async def test_monitoring_features():
    """Test monitoring and metrics features"""
    console.print("\n📊 Testing Monitoring Features", style="bold blue")
    
    async with EnhancedWebScraper() as scraper:
        # Test various URLs to generate metrics
        test_urls = [
            "https://httpstat.us/200",
            "https://httpstat.us/404",
            "https://httpstat.us/500",
            "https://httpstat.us/timeout",
        ]
        
        console.print("Generating metrics data...")
        for url in test_urls:
            try:
                await scraper.scrape_page_content_with_retry(url)
            except:
                pass  # Expected failures
        
        # Display metrics
        success_rates = scraper.get_success_rate()
        circuit_states = scraper.get_circuit_breaker_states()
        
        console.print("\n📈 Success Rates:")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Domain", style="cyan")
        table.add_column("Success Rate", style="green")
        
        for domain, rate in success_rates.items():
            table.add_row(domain, f"{rate:.1%}")
        
        console.print(table)
        
        console.print("\n🔧 Circuit Breaker States:")
        for domain, state in circuit_states.items():
            color = "green" if state == "closed" else "red" if state == "open" else "yellow"
            console.print(f"  {domain}: {state}", style=color)

async def test_error_classification():
    """Test error classification system"""
    console.print("\n🔍 Testing Error Classification", style="bold blue")
    
    scraper = EnhancedWebScraper()
    
    # Test different error types
    test_cases = [
        ("Timeout error", Exception("Connection timeout after 30 seconds")),
        ("403 Forbidden", Exception("HTTP 403 Forbidden - Access denied")),
        ("Rate limited", Exception("HTTP 429 Too Many Requests")),
        ("Network error", Exception("Network connection failed - DNS resolution error")),
        ("CAPTCHA detected", Exception("CAPTCHA verification required")),
        ("JavaScript error", Exception("JavaScript execution failed")),
        ("Parsing error", Exception("HTML parsing failed - invalid markup")),
        ("Unknown error", Exception("Something went wrong")),
    ]
    
    console.print("Testing error classification:")
    for description, error in test_cases:
        error_type = scraper._classify_error(error)
        console.print(f"  {description}: {error_type.value}")

async def test_backward_compatibility():
    """Test backward compatibility with original WebScraper interface"""
    console.print("\n🔧 Testing Backward Compatibility", style="bold blue")
    
    # Import using original class name
    from src.core.web_scraper import WebScraper
    
    # Should work exactly like before
    async with WebScraper() as scraper:
        console.print("Testing original WebScraper interface...")
        
        # Test search
        results = await scraper.search_google("test query", max_results=2)
        console.print(f"Search results: {len(results)}")
        
        # Test scraping
        if results:
            content = await scraper.scrape_page_content(results[0]["url"])
            console.print(f"Scraped content length: {len(content['content'])}")
            console.print("✅ Backward compatibility maintained")

async def test_performance_comparison():
    """Test performance comparison between configurations"""
    console.print("\n🏁 Performance Comparison", style="bold blue")
    
    test_urls = [
        "https://httpstat.us/200?sleep=1000",
        "https://httpstat.us/200?sleep=500",
        "https://httpstat.us/200?sleep=2000",
    ]
    
    # Test with basic configuration
    console.print("Testing with basic configuration...")
    basic_times = []
    async with EnhancedWebScraper(max_retries=1, enable_circuit_breaker=False, enable_rate_limiting=False) as scraper:
        for url in test_urls:
            start_time = time.time()
            try:
                await scraper.scrape_page_content_with_retry(url)
                end_time = time.time()
                basic_times.append(end_time - start_time)
            except:
                basic_times.append(float('inf'))
    
    # Test with enhanced configuration
    console.print("Testing with enhanced configuration...")
    enhanced_times = []
    async with EnhancedWebScraper(max_retries=3, enable_circuit_breaker=True, enable_rate_limiting=True) as scraper:
        for url in test_urls:
            start_time = time.time()
            try:
                await scraper.scrape_page_content_with_retry(url)
                end_time = time.time()
                enhanced_times.append(end_time - start_time)
            except:
                enhanced_times.append(float('inf'))
    
    # Display comparison
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan")
    table.add_column("Basic Config", style="yellow")
    table.add_column("Enhanced Config", style="green")
    
    for i, (basic, enhanced) in enumerate(zip(basic_times, enhanced_times)):
        basic_str = f"{basic:.2f}s" if basic != float('inf') else "Failed"
        enhanced_str = f"{enhanced:.2f}s" if enhanced != float('inf') else "Failed"
        table.add_row(f"URL {i+1}", basic_str, enhanced_str)
    
    console.print(table)

async def main():
    """Run all tests"""
    console.print("🚀 Enhanced Web Scraper Test Suite", style="bold green")
    console.print("=" * 50)
    
    try:
        await test_basic_functionality()
        await test_retry_mechanism()
        await test_circuit_breaker()
        await test_rate_limiting()
        await test_monitoring_features()
        await test_error_classification()
        await test_backward_compatibility()
        await test_performance_comparison()
        
        console.print("\n✅ All tests completed!", style="bold green")
        
    except Exception as e:
        console.print(f"\n❌ Test suite failed: {str(e)}", style="bold red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 