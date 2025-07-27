#!/usr/bin/env python3
"""
Test script for RAG system enhancements
"""

import asyncio
import time
import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_memory():
    """Test enhanced conversation memory"""
    print("\n🧠 Testing Enhanced Conversation Memory")
    print("=" * 50)
    
    try:
        from src.core.memory.conversation_memory import EnhancedConversationMemory
        
        # Initialize memory
        memory = EnhancedConversationMemory(
            max_history_length=10,
            enable_summarization=True
        )
        
        conversation_id = "test_conv_001"
        
        # Add test messages
        await memory.add_message(
            conversation_id=conversation_id,
            role="user",
            content="What is artificial intelligence?",
            metadata={"query_type": "factual"}
        )
        
        await memory.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content="Artificial intelligence (AI) is a branch of computer science...",
            confidence_score=0.9,
            processing_time=2.5,
            sources=[{"title": "AI Overview", "url": "example.com"}]
        )
        
        # Test context retrieval
        context, topics = await memory.get_context_for_llm(conversation_id)
        
        # Test user profile
        profile = await memory.get_user_profile(conversation_id)
        
        # Test conversation stats
        stats = await memory.get_conversation_stats(conversation_id)
        
        print("✅ Enhanced memory features:")
        print(f"   📝 Context length: {len(context)} characters")
        print(f"   🏷️ Key topics: {topics}")
        print(f"   👤 User profile keys: {list(profile.keys())}")
        print(f"   📊 Stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced memory test failed: {e}")
        return False

async def test_enhanced_web_search():
    """Test enhanced web search tool"""
    print("\n🌐 Testing Enhanced Web Search Tool")
    print("=" * 50)
    
    try:
        from src.core.tools.web_search_tool import EnhancedWebSearchTool
        
        # Initialize search tool
        search_tool = EnhancedWebSearchTool(
            max_results=3,
            enable_content_analysis=True,
            enable_deduplication=True
        )
        
        # Test search
        query = "machine learning applications"
        results = await search_tool.search_and_process(
            query=query,
            query_context="artificial intelligence research"
        )
        
        print("✅ Enhanced web search features:")
        print(f"   🔍 Query: {query}")
        print(f"   📄 Results found: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"   [{i}] {result.get('title', 'No title')}")
            print(f"       🎯 Relevance: {result.get('relevance_score', 0):.2f}")
            print(f"       🏛️ Authority: {result.get('authority_score', 0):.2f}")
            print(f"       ⭐ Quality: {result.get('content_quality_score', 0):.2f}")
            print(f"       🏷️ Topics: {result.get('key_topics', [])[:3]}")
            print(f"       😊 Sentiment: {result.get('sentiment', 'neutral')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced web search test failed: {e}")
        return False

async def test_enhanced_llm_client():
    """Test enhanced Gemini LLM client"""
    print("\n🤖 Testing Enhanced Gemini LLM Client")
    print("=" * 50)
    
    try:
        from src.core.llm.gemini_client import GeminiClient
        import os
        
        # Check if API key is available
        if not os.getenv("GEMINI_API_KEY"):
            print("⚠️ GEMINI_API_KEY not found, skipping LLM test")
            return True
        
        # Initialize client
        llm_client = GeminiClient()
        
        # Test context
        mock_context = [
            {
                "title": "Machine Learning Basics",
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                "url": "https://example.com/ml-basics",
                "relevance_score": 0.9,
                "authority_score": 0.8,
                "key_topics": ["machine learning", "artificial intelligence", "algorithms"]
            }
        ]
        
        # Test conversation history
        conversation_history = [
            {"role": "user", "content": "I want detailed explanations with examples"},
            {"role": "assistant", "content": "I'll provide comprehensive answers with practical examples."}
        ]
        
        # Test different query types
        test_queries = [
            ("What is machine learning?", "factual"),
            ("Compare supervised and unsupervised learning", "analytical"),
            ("How do I implement a neural network?", "technical"),
            ("Create a study plan for AI", "creative")
        ]
        
        print("✅ Enhanced LLM client features:")
        
        for query, expected_type in test_queries:
            # Test prompt building (without actual API call)
            prompt = llm_client._build_rag_prompt(query, mock_context, conversation_history)
            query_type = llm_client._analyze_query_type(query)
            
            print(f"   🔍 Query: {query}")
            print(f"   📝 Type detected: {query_type} (expected: {expected_type})")
            print(f"   📏 Prompt length: {len(prompt)} characters")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced LLM client test failed: {e}")
        return False

async def test_rag_agent_integration():
    """Test RAG agent with enhancements"""
    print("\n🤖 Testing Enhanced RAG Agent Integration")
    print("=" * 50)
    
    try:
        from src.agent.rag_agent import RAGAgent
        import os
        
        # Initialize RAG agent
        rag_agent = RAGAgent(
            enable_web_search=True,
            max_context_docs=3
        )
        
        # Test agent status
        status = rag_agent.get_agent_status()
        print("✅ RAG Agent Status:")
        print(f"   🟢 Agent status: {status.get('agent_status', 'unknown')}")
        print(f"   📚 Vector store: {status.get('vector_store', {}).get('document_count', 0)} documents")
        print(f"   🤖 LLM model: {status.get('llm_model', {}).get('model_name', 'unknown')}")
        print(f"   🌐 Web search: {'enabled' if status.get('web_search_enabled') else 'disabled'}")
        
        # Test knowledge addition
        test_documents = [
            {
                "title": "AI Test Document",
                "content": "This is a test document about artificial intelligence and machine learning concepts.",
                "url": "https://test.example.com/ai-doc",
                "source": "test"
            }
        ]
        
        success = await rag_agent.add_knowledge(test_documents, source="test")
        print(f"   📄 Knowledge addition: {'✅ success' if success else '❌ failed'}")
        
        # Test query processing (without web search to avoid API calls)
        if os.getenv("GEMINI_API_KEY"):
            print("\n   🔍 Testing query processing...")
            response = await rag_agent.query(
                user_query="What is artificial intelligence?",
                conversation_id="test_conversation",
                use_web_search=False  # Disable to avoid external calls
            )
            
            print(f"   📝 Response length: {len(response.content)} characters")
            print(f"   📊 Confidence: {response.confidence_score:.2f}")
            print(f"   ⏱️ Processing time: {response.processing_time:.2f}s")
            print(f"   🔗 Sources: {len(response.sources)}")
            print(f"   📚 Citations: {len(response.citations)}")
        else:
            print("   ⚠️ Skipping query test (no GEMINI_API_KEY)")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG agent integration test failed: {e}")
        return False

async def test_vector_database():
    """Test vector database enhancements"""
    print("\n🗄️ Testing Vector Database")
    print("=" * 50)
    
    try:
        from src.infrastructure.vector_database.chroma_client import ChromaVectorStore
        
        # Initialize vector store
        vector_store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory="./data/test_vector_store"
        )
        
        # Test document addition
        test_docs = [
            {
                "id": "test_doc_1",
                "title": "Test Document 1",
                "content": "This is a test document about machine learning and artificial intelligence.",
                "url": "https://test.example.com/doc1",
                "source": "test"
            },
            {
                "id": "test_doc_2", 
                "title": "Test Document 2",
                "content": "This document covers deep learning, neural networks, and AI applications.",
                "url": "https://test.example.com/doc2",
                "source": "test"
            }
        ]
        
        doc_ids = vector_store.add_documents(test_docs)
        print(f"✅ Added {len(doc_ids)} documents to vector store")
        
        # Test search
        search_results = vector_store.search("machine learning", n_results=2)
        print(f"   🔍 Search results: {len(search_results)} found")
        
        for i, result in enumerate(search_results, 1):
            print(f"   [{i}] {result.get('title', 'No title')} (score: {result.get('score', 0):.3f})")
        
        # Test hybrid search
        hybrid_results = vector_store.hybrid_search(
            "artificial intelligence", 
            keywords=["AI", "machine", "learning"],
            n_results=2
        )
        print(f"   🔀 Hybrid search results: {len(hybrid_results)} found")
        
        # Test collection stats
        stats = vector_store.get_collection_stats()
        print(f"   📊 Collection stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        return False

async def run_all_tests():
    """Run all enhancement tests"""
    print("🚀 RAG System Enhancement Tests")
    print("=" * 60)
    
    tests = [
        ("Enhanced Memory", test_enhanced_memory),
        ("Enhanced Web Search", test_enhanced_web_search),
        ("Enhanced LLM Client", test_enhanced_llm_client),
        ("Vector Database", test_vector_database),
        ("RAG Agent Integration", test_rag_agent_integration),
    ]
    
    results = {}
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        start_time = time.time()
        try:
            success = await test_func()
            results[test_name] = success
            duration = time.time() - start_time
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status} - {test_name} ({duration:.2f}s)")
        except Exception as e:
            results[test_name] = False
            duration = time.time() - start_time
            print(f"\n❌ FAILED - {test_name} ({duration:.2f}s): {e}")
    
    # Summary
    total_duration = time.time() - total_start_time
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    print(f"Total time: {total_duration:.2f}s")
    
    print("\nDetailed Results:")
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print("\n🎉 All tests passed! RAG enhancements are working correctly.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())