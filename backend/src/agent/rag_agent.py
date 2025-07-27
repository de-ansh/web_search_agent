"""
Main RAG Agent - Orchestrates retrieval and generation
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import logging

# Import RAG components
from ..core.llm.gemini_client import GeminiClient, LLMResponse
from ..infrastructure.vector_database.chroma_client import ChromaVectorStore
from ..core.memory.conversation_memory import ConversationMemory
from ..core.knowledge.document_processor import DocumentProcessor
from ..core.tools.web_search_tool import WebSearchTool

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    """Response from RAG agent"""
    content: str
    sources: List[Dict[str, Any]]
    conversation_id: str
    processing_time: float
    method_used: str
    confidence_score: float
    citations: List[Dict[str, Any]]

class RAGAgent:
    """
    Main RAG Agent that orchestrates retrieval and generation
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        vector_store_path: str = "./data/vector_store",
        enable_web_search: bool = True,
        max_context_docs: int = 5
    ):
        """
        Initialize RAG Agent
        
        Args:
            gemini_api_key: Gemini API key
            vector_store_path: Path to vector database
            enable_web_search: Enable real-time web search
            max_context_docs: Maximum documents to use as context
        """
        self.max_context_docs = max_context_docs
        self.enable_web_search = enable_web_search
        
        # Initialize components
        try:
            # LLM Client
            self.llm_client = GeminiClient(api_key=gemini_api_key)
            logger.info("✅ Gemini LLM client initialized")
            
            # Vector Store
            self.vector_store = ChromaVectorStore(persist_directory=vector_store_path)
            logger.info("✅ Vector store initialized")
            
            # Memory Manager
            self.memory = ConversationMemory()
            logger.info("✅ Conversation memory initialized")
            
            # Document Processor
            self.doc_processor = DocumentProcessor()
            logger.info("✅ Document processor initialized")
            
            # Web Search Tool (if enabled)
            if enable_web_search:
                self.web_search = WebSearchTool()
                logger.info("✅ Web search tool initialized")
            else:
                self.web_search = None
            
            logger.info("🤖 RAG Agent fully initialized!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Agent: {e}")
            raise
    
    async def query(
        self,
        user_query: str,
        conversation_id: Optional[str] = None,
        use_web_search: bool = False,
        search_threshold: float = 0.7
    ) -> RAGResponse:
        """
        Process user query using RAG pipeline
        
        Args:
            user_query: User's question/query
            conversation_id: Conversation identifier
            use_web_search: Whether to use web search for fresh info
            search_threshold: Minimum similarity threshold for retrieval
            
        Returns:
            RAGResponse with generated answer and sources
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Processing query: {user_query}")
            
            # Step 1: Get conversation context
            conversation_history = []
            if conversation_id:
                conversation_history = await self.memory.get_conversation_history(
                    conversation_id, limit=5
                )
            
            # Step 2: Retrieve relevant documents from knowledge base
            logger.info("📚 Retrieving from knowledge base...")
            kb_results = self.vector_store.search(
                query=user_query,
                n_results=self.max_context_docs
            )
            
            # Filter by threshold
            kb_results = [r for r in kb_results if r['score'] >= search_threshold]
            
            # Step 3: Web search if enabled and needed
            web_results = []
            if use_web_search and self.web_search:
                logger.info("🌐 Performing web search...")
                try:
                    web_results = await self.web_search.search_and_process(
                        query=user_query,
                        max_results=3
                    )
                    
                    # Add web results to knowledge base for future use
                    if web_results:
                        await self._add_web_results_to_kb(web_results)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Web search failed: {e}")
            
            # Step 4: Combine and rank all sources
            all_sources = self._combine_and_rank_sources(kb_results, web_results)
            
            # Step 5: Generate response using LLM
            logger.info("🤖 Generating response with LLM...")
            llm_response = await self.llm_client.generate_response(
                query=user_query,
                context=all_sources[:self.max_context_docs],
                conversation_history=conversation_history
            )
            
            # Step 6: Store conversation
            if conversation_id:
                await self.memory.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_query
                )
                await self.memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant", 
                    content=llm_response.content
                )
            
            # Step 7: Calculate confidence score
            confidence_score = self._calculate_confidence(
                sources=all_sources,
                llm_response=llm_response
            )
            
            processing_time = time.time() - start_time
            
            # Create response
            response = RAGResponse(
                content=llm_response.content,
                sources=all_sources,
                conversation_id=conversation_id or "single_query",
                processing_time=processing_time,
                method_used="rag_with_web" if web_results else "rag_kb_only",
                confidence_score=confidence_score,
                citations=llm_response.citations
            )
            
            logger.info(f"✅ Query processed successfully in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            
            # Return error response
            return RAGResponse(
                content=f"I apologize, but I encountered an error processing your query: {str(e)}",
                sources=[],
                conversation_id=conversation_id or "error",
                processing_time=time.time() - start_time,
                method_used="error_fallback",
                confidence_score=0.0,
                citations=[]
            )
    
    async def stream_query(
        self,
        user_query: str,
        conversation_id: Optional[str] = None,
        use_web_search: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream query response for real-time output
        
        Args:
            user_query: User's question
            conversation_id: Conversation ID
            use_web_search: Whether to use web search
            
        Yields:
            Streaming response chunks
        """
        try:
            # Yield status updates
            yield {"type": "status", "message": "Processing query..."}
            
            # Get context (same as regular query)
            conversation_history = []
            if conversation_id:
                conversation_history = await self.memory.get_conversation_history(
                    conversation_id, limit=5
                )
            
            yield {"type": "status", "message": "Retrieving relevant information..."}
            
            # Retrieve documents
            kb_results = self.vector_store.search(user_query, n_results=self.max_context_docs)
            
            # Web search if needed
            web_results = []
            if use_web_search and self.web_search:
                yield {"type": "status", "message": "Searching the web..."}
                web_results = await self.web_search.search_and_process(user_query, max_results=3)
            
            # Combine sources
            all_sources = self._combine_and_rank_sources(kb_results, web_results)
            
            yield {"type": "sources", "data": all_sources}
            yield {"type": "status", "message": "Generating response..."}
            
            # Stream LLM response
            async for chunk in self.llm_client.generate_streaming_response(
                query=user_query,
                context=all_sources[:self.max_context_docs],
                conversation_history=conversation_history
            ):
                yield {"type": "content", "data": chunk}
            
            yield {"type": "complete", "message": "Response generated successfully"}
            
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    async def add_knowledge(
        self,
        documents: List[Dict[str, Any]],
        source: str = "manual"
    ) -> bool:
        """
        Add documents to knowledge base
        
        Args:
            documents: List of documents to add
            source: Source identifier
            
        Returns:
            Success status
        """
        try:
            # Process documents
            processed_docs = await self.doc_processor.process_documents(
                documents, source=source
            )
            
            # Add to vector store
            doc_ids = self.vector_store.add_documents(processed_docs)
            
            logger.info(f"✅ Added {len(doc_ids)} documents to knowledge base")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add knowledge: {e}")
            return False
    
    def _combine_and_rank_sources(
        self,
        kb_results: List[Dict[str, Any]],
        web_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and rank sources from KB and web search"""
        
        # Add source type to results
        for result in kb_results:
            result['source_type'] = 'knowledge_base'
        
        for result in web_results:
            result['source_type'] = 'web_search'
            # Boost web results slightly for freshness
            result['score'] = min(result.get('score', 0.5) + 0.1, 1.0)
        
        # Combine and sort by score
        all_sources = kb_results + web_results
        all_sources.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return all_sources
    
    def _calculate_confidence(
        self,
        sources: List[Dict[str, Any]],
        llm_response: LLMResponse
    ) -> float:
        """Calculate confidence score for the response"""
        
        if not sources:
            return 0.3  # Low confidence without sources
        
        # Average source relevance
        avg_relevance = sum(s.get('score', 0) for s in sources) / len(sources)
        
        # Response length factor (longer responses might be more comprehensive)
        length_factor = min(len(llm_response.content) / 500, 1.0)
        
        # Citation factor (responses with citations are more reliable)
        citation_factor = min(len(llm_response.citations) / 3, 1.0)
        
        # Combine factors
        confidence = (avg_relevance * 0.5 + length_factor * 0.2 + citation_factor * 0.3)
        
        return min(confidence, 1.0)
    
    async def _add_web_results_to_kb(self, web_results: List[Dict[str, Any]]):
        """Add web search results to knowledge base for future use"""
        try:
            # Convert web results to document format
            documents = []
            for result in web_results:
                doc = {
                    'content': result.get('content', ''),
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'source': 'web_search',
                    'timestamp': time.time()
                }
                documents.append(doc)
            
            # Add to knowledge base
            if documents:
                await self.add_knowledge(documents, source="web_search")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to add web results to KB: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            llm_info = self.llm_client.get_model_info()
            
            return {
                "agent_status": "active",
                "vector_store": vector_stats,
                "llm_model": llm_info,
                "web_search_enabled": self.enable_web_search,
                "max_context_docs": self.max_context_docs,
                "memory_active": True
            }
        except Exception as e:
            return {"agent_status": "error", "error": str(e)}