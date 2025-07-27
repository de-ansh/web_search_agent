"""
ChromaDB Vector Database Client for RAG Agent
"""

import os
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    """ChromaDB vector store for RAG operations"""
    
    def __init__(
        self,
        collection_name: str = "rag_knowledge_base",
        persist_directory: str = "./data/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        chroma_host: Optional[str] = None,
        chroma_port: Optional[int] = None
    ):
        """
        Initialize ChromaDB client
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
            embedding_model: Sentence transformer model for embeddings
            chroma_host: ChromaDB server host (if using server mode)
            chroma_port: ChromaDB server port (if using server mode)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        self.chroma_host = chroma_host or os.getenv("CHROMA_HOST")
        self.chroma_port = chroma_port or int(os.getenv("CHROMA_PORT", "8000"))
        
        # Initialize ChromaDB client (embedded or server mode)
        if self.chroma_host:
            # Server mode - connect to remote ChromaDB server
            logger.info(f"🌐 Connecting to ChromaDB server at {self.chroma_host}:{self.chroma_port}")
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
        else:
            # Embedded mode - local ChromaDB instance
            logger.info(f"💾 Using embedded ChromaDB at {persist_directory}")
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"✅ Loaded embedding model: {embedding_model}")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"✅ Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "RAG knowledge base"}
            )
            logger.info(f"✅ Created new collection: {collection_name}")
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents with 'content', 'title', 'url', etc.
            batch_size: Batch size for processing
            
        Returns:
            List of document IDs
        """
        document_ids = []
        
        try:
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_ids = []
                batch_texts = []
                batch_metadatas = []
                
                for doc in batch:
                    # Generate unique ID
                    doc_id = doc.get('id', str(uuid.uuid4()))
                    batch_ids.append(doc_id)
                    
                    # Extract text content
                    content = doc.get('content', '')
                    title = doc.get('title', '')
                    text = f"{title}\n\n{content}" if title else content
                    batch_texts.append(text)
                    
                    # Prepare metadata
                    metadata = {
                        'title': title,
                        'url': doc.get('url', ''),
                        'source': doc.get('source', 'unknown'),
                        'timestamp': doc.get('timestamp', time.time()),
                        'content_length': len(content),
                        'chunk_index': doc.get('chunk_index', 0)
                    }
                    batch_metadatas.append(metadata)
                
                # Generate embeddings
                logger.info(f"🔄 Generating embeddings for batch {i//batch_size + 1}")
                embeddings = self.embedding_model.encode(
                    batch_texts,
                    convert_to_tensor=False,
                    show_progress_bar=True
                ).tolist()
                
                # Add to collection
                self.collection.add(
                    ids=batch_ids,
                    embeddings=embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                
                document_ids.extend(batch_ids)
                logger.info(f"✅ Added batch {i//batch_size + 1} ({len(batch)} documents)")
            
            logger.info(f"✅ Successfully added {len(document_ids)} documents to vector store")
            return document_ids
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Metadata filters
            
        Returns:
            List of similar documents with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'title': results['metadatas'][0][i].get('title', 'Unknown'),
                        'url': results['metadatas'][0][i].get('url', ''),
                        'source': results['metadatas'][0][i].get('source', 'unknown')
                    }
                    formatted_results.append(result)
            
            logger.info(f"✅ Found {len(formatted_results)} similar documents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        n_results: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword search
        
        Args:
            query: Semantic search query
            keywords: Keywords for filtering
            n_results: Number of results
            semantic_weight: Weight for semantic vs keyword search
            
        Returns:
            Combined search results
        """
        try:
            # Semantic search
            semantic_results = self.search(query, n_results * 2)
            
            # Keyword filtering (simple implementation)
            keyword_filtered = []
            for result in semantic_results:
                content_lower = result['content'].lower()
                keyword_score = sum(1 for kw in keywords if kw.lower() in content_lower)
                
                if keyword_score > 0:
                    # Combine scores
                    combined_score = (
                        semantic_weight * result['score'] +
                        (1 - semantic_weight) * (keyword_score / len(keywords))
                    )
                    result['score'] = combined_score
                    result['keyword_matches'] = keyword_score
                    keyword_filtered.append(result)
            
            # Sort by combined score and return top results
            keyword_filtered.sort(key=lambda x: x['score'], reverse=True)
            return keyword_filtered[:n_results]
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return self.search(query, n_results)  # Fallback to semantic search
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"✅ Deleted {len(document_ids)} documents")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete documents: {e}")
            return False
    
    def update_document(self, document_id: str, document: Dict[str, Any]) -> bool:
        """Update a single document"""
        try:
            # Delete old version
            self.collection.delete(ids=[document_id])
            
            # Add updated version
            document['id'] = document_id
            self.add_documents([document])
            
            logger.info(f"✅ Updated document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update document: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the entire collection (use with caution!)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG knowledge base"}
            )
            logger.info(f"✅ Reset collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reset collection: {e}")
            return False