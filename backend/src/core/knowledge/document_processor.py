"""
Document Processing for RAG Knowledge Base
"""

import time
import hashlib
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process documents for RAG knowledge base"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info("✅ Document processor initialized")
    
    async def process_documents(
        self,
        documents: List[Dict[str, Any]],
        source: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """Process documents into chunks for vector storage"""
        processed_docs = []
        
        for doc in documents:
            try:
                # Extract content
                content = doc.get('content', '')
                title = doc.get('title', '')
                url = doc.get('url', '')
                
                # Clean content
                cleaned_content = self._clean_text(content)
                
                # Create chunks
                chunks = self._create_chunks(cleaned_content)
                
                # Create processed documents
                for i, chunk in enumerate(chunks):
                    processed_doc = {
                        'id': self._generate_doc_id(url, i),
                        'content': chunk,
                        'title': title,
                        'url': url,
                        'source': source,
                        'timestamp': time.time(),
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                    processed_docs.append(processed_doc)
                    
            except Exception as e:
                logger.error(f"❌ Failed to process document: {e}")
                continue
        
        logger.info(f"✅ Processed {len(documents)} documents into {len(processed_docs)} chunks")
        return processed_docs
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_doc_id(self, url: str, chunk_index: int) -> str:
        """Generate unique document ID"""
        content = f"{url}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()