#!/usr/bin/env python3
"""
Test script for improved similarity detection system
Tests the ability to differentiate between semantically different queries
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.similarity_detector import EnhancedSimilarityDetector
from src.ai.embeddings import EmbeddingService

def test_similarity_cases():
    """Test various similarity cases including edge cases"""
    
    print("🧪 Testing Enhanced Similarity Detection System")
    print("=" * 60)
    
    # Initialize the detector with strict mode
    detector = EnhancedSimilarityDetector(
        similarity_threshold=0.85,
        llm_validation_threshold=0.75,
        enable_llm_validation=True,
        strict_mode=True
    )
    
    # Test cases that should be considered SIMILAR
    similar_cases = [
        ("best restaurants in NYC", "top restaurants in New York City"),
        ("how to learn Python programming", "Python programming tutorial for beginners"),
        ("install Docker on Ubuntu", "how to install Docker on Ubuntu"),
        ("iPhone 15 features", "iPhone 15 specifications"),
        ("React hooks tutorial", "how to use React hooks"),
    ]
    
    # Test cases that should be considered NOT SIMILAR (edge cases)
    not_similar_cases = [
        ("best resources for Playwright", "best resources for Selenium"),
        ("Python tutorial", "Java tutorial"),
        ("React hooks", "Vue composition API"),
        ("AWS Lambda functions", "Azure Functions"),
        ("MySQL database setup", "PostgreSQL database setup"),
        ("iPhone 15 features", "iPhone 14 features"),
        ("best restaurants in NYC", "best hotels in NYC"),
        ("Docker installation", "Kubernetes setup"),
        ("Jest testing framework", "Cypress testing framework"),
        ("GitHub Actions", "GitLab CI"),
    ]
    
    print("\n🔍 Testing SIMILAR cases (should return high similarity):")
    print("-" * 50)
    
    for query1, query2 in similar_cases:
        # Create a mock stored query
        stored_query = {
            "query": query2,
            "embedding": EmbeddingService().generate_embedding(query2).tolist(),
            "results": [{"title": "Mock result", "url": "https://example.com", "summary": "Mock summary"}],
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        }
        
        # Store the query
        detector.store_query_with_results(query2, stored_query["results"])
        
        # Test similarity
        result = detector.find_similar_query(query1)
        
        print(f"Query 1: '{query1}'")
        print(f"Query 2: '{query2}'")
        print(f"Result: {'✅ SIMILAR' if result.found_similar else '❌ NOT SIMILAR'}")
        print(f"Similarity: {result.best_similarity:.3f}")
        print(f"Confidence: {result.confidence_score:.3f}")
        print(f"Method: {result.validation_method}")
        print(f"LLM Validated: {result.llm_validated}")
        print(f"Stages: {' → '.join(result.validation_stages)}")
        if result.cache_hit_reason:
            print(f"Reason: {result.cache_hit_reason}")
        print()
    
    print("\n🚫 Testing NOT SIMILAR cases (should return low similarity or rejection):")
    print("-" * 50)
    
    for query1, query2 in not_similar_cases:
        # Create a mock stored query
        stored_query = {
            "query": query2,
            "embedding": EmbeddingService().generate_embedding(query2).tolist(),
            "results": [{"title": "Mock result", "url": "https://example.com", "summary": "Mock summary"}],
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True}
        }
        
        # Store the query
        detector.store_query_with_results(query2, stored_query["results"])
        
        # Test similarity
        result = detector.find_similar_query(query1)
        
        print(f"Query 1: '{query1}'")
        print(f"Query 2: '{query2}'")
        print(f"Result: {'❌ NOT SIMILAR' if not result.found_similar else '⚠️ SIMILAR (unexpected)'}")
        print(f"Similarity: {result.best_similarity:.3f}")
        print(f"Confidence: {result.confidence_score:.3f}")
        print(f"Method: {result.validation_method}")
        print(f"LLM Validated: {result.llm_validated}")
        print(f"Stages: {' → '.join(result.validation_stages)}")
        if result.cache_hit_reason:
            print(f"Reason: {result.cache_hit_reason}")
        print()
    
    # Test domain-specific validation
    print("\n🎯 Testing Domain-Specific Validation:")
    print("-" * 50)
    
    # Test the specific case mentioned by the user
    playwright_query = "best resources for Playwright"
    selenium_query = "best resources for Selenium"
    
    # Store Selenium query
    detector.store_query_with_results(selenium_query, [
        {"title": "Selenium documentation", "url": "https://selenium.dev", "summary": "Selenium automation"}
    ])
    
    # Test if Playwright query matches
    result = detector.find_similar_query(playwright_query)
    
    print(f"🎭 Playwright vs Selenium Test:")
    print(f"Stored: '{selenium_query}'")
    print(f"Query: '{playwright_query}'")
    print(f"Result: {'❌ CORRECTLY REJECTED' if not result.found_similar else '⚠️ INCORRECTLY MATCHED'}")
    print(f"Similarity: {result.best_similarity:.3f}")
    print(f"Method: {result.validation_method}")
    print(f"Stages: {' → '.join(result.validation_stages)}")
    if result.cache_hit_reason:
        print(f"Reason: {result.cache_hit_reason}")
    print()
    
    # Test cache statistics
    print("\n📊 Cache Statistics:")
    print("-" * 50)
    stats = detector.get_cache_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Similarity Detection Test Completed!")

def test_domain_extraction():
    """Test domain keyword extraction"""
    print("\n🔍 Testing Domain Keyword Extraction:")
    print("-" * 50)
    
    detector = EnhancedSimilarityDetector()
    
    test_queries = [
        "best resources for Playwright",
        "Selenium automation tutorial",
        "Python programming guide",
        "React hooks documentation",
        "AWS Lambda functions",
        "MySQL database setup",
        "Jest testing framework",
        "GitHub Actions workflow",
    ]
    
    for query in test_queries:
        domains = detector._extract_domain_keywords(query.lower())
        print(f"Query: '{query}'")
        print(f"Domains: {domains}")
        print()

def test_textual_similarity():
    """Test textual similarity calculation"""
    print("\n📝 Testing Textual Similarity:")
    print("-" * 50)
    
    detector = EnhancedSimilarityDetector()
    
    test_pairs = [
        ("best restaurants in NYC", "top restaurants in New York City"),
        ("Playwright automation", "Selenium automation"),
        ("Python programming", "Java programming"),
        ("how to install Docker", "Docker installation guide"),
        ("completely different query", "totally unrelated text"),
    ]
    
    for query1, query2 in test_pairs:
        similarity = detector._calculate_textual_similarity(query1, query2)
        print(f"Query 1: '{query1}'")
        print(f"Query 2: '{query2}'")
        print(f"Textual Similarity: {similarity:.3f}")
        print()

if __name__ == "__main__":
    try:
        test_similarity_cases()
        test_domain_extraction()
        test_textual_similarity()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 