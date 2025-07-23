#!/usr/bin/env python3
"""
Test runner for enhanced research service - works with uv and package structure
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

def setup_imports():
    """Setup proper import paths"""
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    
    # Add paths to sys.path
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# Setup imports before importing our modules
setup_imports()

from src.services.enhanced_research_service import EnhancedResearchService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_enhanced_research():
    """Test the enhanced research service"""
    
    print("🚀 Testing Enhanced Research Service with Gemini AI")
    print("=" * 60)
    
    # Check for API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    print(f"Gemini API Key: {'✅ Found' if gemini_key else '❌ Not found'}")
    print(f"OpenAI API Key: {'✅ Found' if openai_key else '❌ Not found'}")
    print()
    
    # Initialize service
    if gemini_key:
        service = EnhancedResearchService(
            use_playwright=True,
            preferred_ai_method="gemini",
            max_sources=3,
            summary_length=120
        )
        print("🤖 Using Gemini AI for summarization")
    elif openai_key:
        service = EnhancedResearchService(
            use_playwright=True,
            preferred_ai_method="openai",
            max_sources=3,
            summary_length=120
        )
        print("🤖 Using OpenAI for summarization")
    else:
        service = EnhancedResearchService(
            use_playwright=True,
            preferred_ai_method="extractive",
            max_sources=3,
            summary_length=120
        )
        print("🤖 Using extractive summarization (no API keys)")
    
    print()
    
    # Test queries
    test_queries = [
        "latest developments in artificial intelligence 2024",
        "climate change renewable energy solutions",
        "cryptocurrency market trends"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"📋 Test {i}/{len(test_queries)}: {query}")
        print("-" * 50)
        
        try:
            # Perform research
            result = await service.research_query(query)
            
            # Display results
            print(f"✅ Success: {result.success}")
            print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
            print(f"📊 Sources: {result.successful_scrapes}/{result.total_sources}")
            print(f"🤖 AI Method: {result.method_used}")
            print()
            
            print("📝 Combined Summary:")
            print(f"   {result.combined_summary[:200]}...")
            print()
            
            print("📚 Individual Sources:")
            for j, summary in enumerate(result.individual_summaries[:2], 1):  # Show first 2
                print(f"   {j}. {summary['source_title'][:50]}...")
                print(f"      Method: {summary['method']} | Confidence: {summary['confidence']:.2f}")
                print(f"      Summary: {summary['summary'][:150]}...")
                print()
            
            if result.sources:
                print("🔗 Source URLs:")
                for source in result.sources[:3]:  # Show first 3
                    status = "✅" if source['success'] else "❌"
                    print(f"   {status} {source['url']}")
                print()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            print()
        
        print("=" * 60)
        print()
        
        # Add delay between tests
        if i < len(test_queries):
            print("⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # Test service status
    print("📊 Service Status:")
    status = service.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()
    
    print("🎉 Enhanced research testing completed!")

async def test_quick_research():
    """Test quick research functionality"""
    print("\n🚀 Testing Quick Research Feature")
    print("=" * 40)
    
    service = EnhancedResearchService(
        use_playwright=False,  # Use requests only for speed
        preferred_ai_method="gemini" if os.getenv("GEMINI_API_KEY") else "extractive",
        max_sources=5,
        summary_length=100
    )
    
    query = "Python programming best practices"
    print(f"🔍 Quick research: {query}")
    
    try:
        result = await service.quick_research(query, max_sources=2)
        
        print(f"✅ Success: {result.success}")
        print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
        print(f"📝 Summary: {result.combined_summary[:200]}...")
        print()
    except Exception as e:
        print(f"❌ Quick research failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🧪 Enhanced Research Service Test Runner")
    print("=" * 45)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the backend directory")
        print("   cd backend && python test_runner.py")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        # Run tests
        asyncio.run(test_enhanced_research())
        asyncio.run(test_quick_research())
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 Test runner complete!")

if __name__ == "__main__":
    main()