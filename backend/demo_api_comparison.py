#!/usr/bin/env python3
"""
Demo script to compare summarization quality with and without API keys
"""

import asyncio
from src.ai.summarizer import ContentSummarizer
from src.core.web_scraper import WebScraper

async def demo_summarization_comparison():
    """Demo different summarization methods"""
    
    print("🔬 Web Search Agent - Summarization Quality Demo")
    print("=" * 60)
    
    # Sample content for testing
    sample_content = """
    Artificial intelligence has made remarkable progress in 2024, with significant breakthroughs 
    in large language models, computer vision, and robotics. Major tech companies have released 
    more powerful AI models that can understand and generate human-like text, create images, 
    and even write code. The integration of AI into everyday applications has accelerated, 
    with AI assistants becoming more capable and AI-powered tools being adopted across industries. 
    However, concerns about AI safety, bias, and the impact on employment continue to be debated. 
    Researchers are working on developing more interpretable AI systems and establishing ethical 
    guidelines for AI development and deployment. The year has also seen increased investment 
    in AI startups and growing competition between tech giants to dominate the AI landscape.
    """
    
    print("📄 Sample Content:")
    print("-" * 40)
    print(sample_content[:200] + "...")
    print()
    
    # Test different summarization methods
    summarizer = ContentSummarizer()
    
    print("🧪 Testing Different Summarization Methods:")
    print("-" * 50)
    
    # Test extractive summarization (always available)
    print("1. 📊 Extractive Summarization (No API required):")
    extractive_result = summarizer._extractive_summarize(sample_content, 50, "AI trends 2024")
    print(f"   Summary: {extractive_result}")
    print()
    
    # Test OpenAI summarization (requires API key)
    print("2. 🤖 OpenAI GPT-3.5 Summarization:")
    try:
        openai_result = summarizer._summarize_with_openai(sample_content, 50, "AI trends 2024")
        print(f"   Summary: {openai_result}")
    except Exception as e:
        print(f"   ❌ Not available: {e}")
        print("   💡 Set OPENAI_API_KEY to enable this feature")
    print()
    
    # Test HuggingFace summarization (requires model download)
    print("3. 🤗 HuggingFace BART Summarization:")
    try:
        hf_result = summarizer._summarize_with_huggingface(sample_content, 50, "AI trends 2024")
        print(f"   Summary: {hf_result}")
    except Exception as e:
        print(f"   ❌ Not available: {e}")
        print("   💡 Enable HuggingFace models in summarizer.py")
    print()
    
    # Test full summarization pipeline
    print("4. 🔄 Full Summarization Pipeline (Auto-selects best method):")
    full_result = summarizer.summarize_content(sample_content, 50, "AI trends 2024")
    print(f"   Method: {full_result.method}")
    print(f"   Confidence: {full_result.confidence}")
    print(f"   Summary: {full_result.summary}")
    print()

async def demo_web_search_with_api():
    """Demo web search with API-powered summarization"""
    
    print("🌐 Web Search + AI Summarization Demo")
    print("=" * 50)
    
    query = "machine learning advances 2024"
    print(f"🔍 Search Query: {query}")
    print()
    
    # Initialize components
    summarizer = ContentSummarizer()
    
    async with WebScraper() as scraper:
        print("🔄 Searching web...")
        search_results = await scraper.search_google(query, max_results=2)
        
        if not search_results:
            print("❌ No search results found")
            return
        
        print(f"✅ Found {len(search_results)} results")
        print()
        
        for i, result in enumerate(search_results, 1):
            print(f"📄 Result {i}: {result['title']}")
            print(f"🔗 URL: {result['url']}")
            
            # Scrape content
            page_content = await scraper.scrape_page_content(result['url'])
            content = page_content['content']
            
            if len(content) > 100:
                # Test summarization
                summary_result = summarizer.summarize_content(content, 80, query)
                print(f"📝 Summary ({summary_result.method}, {summary_result.confidence:.1f}): {summary_result.summary}")
            else:
                print(f"📝 Content too short: {content}")
            
            print("-" * 50)

def main():
    """Main demo function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        print("Running web search demo...")
        asyncio.run(demo_web_search_with_api())
    else:
        print("Running summarization comparison demo...")
        asyncio.run(demo_summarization_comparison())
        
        print("\n💡 To run web search demo: python demo_api_comparison.py web")
        print("💡 To set up API keys: python setup_api_keys.py")

if __name__ == "__main__":
    main() 