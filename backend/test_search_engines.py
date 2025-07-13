#!/usr/bin/env python3
"""
Test script to verify search engines are working correctly
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.web_scraper import EnhancedWebScraper

async def test_search_engines():
    """Test individual search engines"""
    
    query = "Who made React Js?"
    print(f"Testing search engines for query: '{query}'")
    print("=" * 50)
    
    async with EnhancedWebScraper() as scraper:
        # Test each search engine individually
        search_engines = [
            ("Bing", scraper.search_bing),
            ("DuckDuckGo", scraper.search_duckduckgo),
            ("Yahoo", scraper.search_yahoo),
        ]
        
        for engine_name, search_func in search_engines:
            print(f"\nTesting {engine_name}:")
            print("-" * 20)
            
            try:
                results = await search_func(query, max_results=3)
                
                if results:
                    print(f"✅ {engine_name} returned {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. {result['title']}")
                        print(f"     URL: {result['url']}")
                        print()
                else:
                    print(f"❌ {engine_name} returned no results")
                    
            except Exception as e:
                print(f"❌ {engine_name} failed: {str(e)}")
        
        # Test the main search function
        print("\nTesting main search function:")
        print("-" * 30)
        
        try:
            results = await scraper.search_google(query, max_results=5)
            
            if results:
                print(f"✅ Main search returned {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['title']}")
                    print(f"     URL: {result['url']}")
                    print()
            else:
                print("❌ Main search returned no results")
                
        except Exception as e:
            print(f"❌ Main search failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_search_engines()) 