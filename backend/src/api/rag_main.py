"""
RAG Agent FastAPI Application
"""

import time
import uuid
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import logging

# Load environment variables first
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Import RAG components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agent.rag_agent import RAGAgent, RAGResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG AI Agent API",
    description="Retrieval Augmented Generation AI Agent with Gemini LLM",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG agent instance
rag_agent: Optional[RAGAgent] = None

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    use_web_search: bool = False
    search_threshold: float = 0.7

class ChatResponse(BaseModel):
    content: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    processing_time: float
    method_used: str
    confidence_score: float
    citations: List[Dict[str, Any]]

class KnowledgeRequest(BaseModel):
    documents: List[Dict[str, Any]]
    source: str = "manual"

class StatusResponse(BaseModel):
    status: str
    agent_info: Dict[str, Any]
    version: str

@app.on_event("startup")
async def startup_event():
    """Initialize RAG agent on startup"""
    global rag_agent
    
    try:
        logger.info("🚀 Initializing RAG Agent...")
        rag_agent = RAGAgent(
            enable_web_search=True,
            max_context_docs=5
        )
        logger.info("✅ RAG Agent initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Agent: {e}")
        # Continue without RAG agent for now
        rag_agent = None

@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint with agent status"""
    if rag_agent:
        agent_info = rag_agent.get_agent_status()
        status = "healthy"
    else:
        agent_info = {"error": "RAG agent not initialized"}
        status = "degraded"
    
    return StatusResponse(
        status=status,
        agent_info=agent_info,
        version="3.0.0"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if rag_agent else "degraded",
        "message": "RAG AI Agent API",
        "version": "3.0.0",
        "agent_ready": rag_agent is not None
    }

@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with RAG agent
    """
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not available")
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Process query with RAG agent
        response = await rag_agent.query(
            user_query=request.query,
            conversation_id=conversation_id,
            use_web_search=request.use_web_search,
            search_threshold=request.search_threshold
        )
        
        return ChatResponse(
            content=response.content,
            sources=response.sources,
            conversation_id=response.conversation_id,
            processing_time=response.processing_time,
            method_used=response.method_used,
            confidence_score=response.confidence_score,
            citations=response.citations
        )
        
    except Exception as e:
        logger.error(f"❌ Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/agent/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream chat response for real-time output
    """
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not available")
    
    async def generate_stream():
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            
            async for chunk in rag_agent.stream_query(
                user_query=request.query,
                conversation_id=conversation_id,
                use_web_search=request.use_web_search
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            error_chunk = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/knowledge/add")
async def add_knowledge(request: KnowledgeRequest):
    """
    Add documents to knowledge base
    """
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not available")
    
    try:
        success = await rag_agent.add_knowledge(
            documents=request.documents,
            source=request.source
        )
        
        if success:
            return {
                "message": f"Successfully added {len(request.documents)} documents",
                "source": request.source,
                "document_count": len(request.documents)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add documents")
            
    except Exception as e:
        logger.error(f"❌ Knowledge addition failed: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge addition failed: {str(e)}")

@app.get("/knowledge/stats")
async def get_knowledge_stats():
    """
    Get knowledge base statistics
    """
    if not rag_agent:
        raise HTTPException(status_code=503, detail="RAG agent not available")
    
    try:
        stats = rag_agent.vector_store.get_collection_stats()
        return {
            "knowledge_base": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.get("/agent/status")
async def get_agent_status():
    """
    Get detailed agent status
    """
    if not rag_agent:
        return {
            "agent_status": "not_initialized",
            "error": "RAG agent not available"
        }
    
    try:
        status = rag_agent.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"❌ Failed to get agent status: {e}")
        return {
            "agent_status": "error",
            "error": str(e)
        }

# Legacy endpoints for compatibility
@app.post("/research/enhanced")
async def legacy_enhanced_research(request: dict):
    """Legacy endpoint for compatibility with existing frontend"""
    if not rag_agent:
        # Return fallback response
        return {
            "query": request.get("query", ""),
            "success": False,
            "sources": [],
            "combined_summary": "RAG agent not available. Please check system status.",
            "individual_summaries": [],
            "processing_time": 0.0,
            "method_used": "error",
            "total_sources": 0,
            "successful_scrapes": 0,
            "error": "RAG agent not initialized"
        }
    
    try:
        # Convert legacy request to new format
        chat_request = ChatRequest(
            query=request.get("query", ""),
            use_web_search=request.get("use_playwright", False),
            search_threshold=0.7
        )
        
        # Process with RAG agent
        response = await rag_agent.query(
            user_query=chat_request.query,
            use_web_search=chat_request.use_web_search,
            search_threshold=chat_request.search_threshold
        )
        
        # Convert to legacy format
        return {
            "query": response.conversation_id,
            "success": True,
            "sources": [
                {
                    "title": source.get("title", ""),
                    "url": source.get("url", ""),
                    "success": True,
                    "method": source.get("source_type", "rag"),
                    "word_count": len(source.get("content", "").split()),
                    "processing_time": response.processing_time
                }
                for source in response.sources[:5]
            ],
            "combined_summary": response.content,
            "individual_summaries": [
                {
                    "source_title": source.get("title", ""),
                    "source_url": source.get("url", ""),
                    "summary": source.get("content", "")[:200] + "...",
                    "method": "rag_agent",
                    "confidence": response.confidence_score,
                    "word_count": len(source.get("content", "").split()),
                    "processing_time": response.processing_time / len(response.sources) if response.sources else 0,
                    "scraping_method": source.get("source_type", "rag"),
                    "scraping_success": True
                }
                for source in response.sources[:5]
            ],
            "processing_time": response.processing_time,
            "method_used": response.method_used,
            "total_sources": len(response.sources),
            "successful_scrapes": len(response.sources)
        }
        
    except Exception as e:
        logger.error(f"❌ Legacy research failed: {e}")
        return {
            "query": request.get("query", ""),
            "success": False,
            "sources": [],
            "combined_summary": f"Research failed: {str(e)}",
            "individual_summaries": [],
            "processing_time": 0.0,
            "method_used": "error",
            "total_sources": 0,
            "successful_scrapes": 0,
            "error": str(e)
        }

@app.post("/research/quick")
async def legacy_quick_research(request: dict):
    """Legacy quick research endpoint"""
    # Use the same logic as enhanced but with web search disabled
    request["use_playwright"] = False
    return await legacy_enhanced_research(request)

if __name__ == "__main__":
    import uvicorn
    
    print("🤖 Starting RAG AI Agent API")
    print("=" * 40)
    print("✅ Retrieval Augmented Generation")
    print("✅ Gemini LLM Integration")
    print("✅ Vector Database (ChromaDB)")
    print("✅ Conversation Memory")
    print("✅ Web Search Integration")
    print()
    print("🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")