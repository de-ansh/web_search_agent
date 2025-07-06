"""
Embeddings module for generating and comparing query embeddings
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

class EmbeddingService:
    """Service for generating and comparing query embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a given text
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array containing the embedding
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Normalize the text
        normalized_text = self._normalize_text(text)
        
        # Generate embedding
        embedding = self.model.encode(normalized_text, convert_to_numpy=True)
        return embedding
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        if embedding1.shape != embedding2.shape:
            raise ValueError("Embeddings must have the same shape")
        
        # Reshape for sklearn cosine_similarity
        similarity = cosine_similarity(
            embedding1.reshape(1, -1), 
            embedding2.reshape(1, -1)
        )[0][0]
        
        return float(similarity)
    
    def find_similar_queries(
        self, 
        query: str, 
        stored_queries: List[Dict[str, Any]], 
        threshold: float = 0.8
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find similar queries from stored queries
        
        Args:
            query: Input query to find similar queries for
            stored_queries: List of stored queries with embeddings
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of tuples (query_dict, similarity_score) for similar queries
        """
        if not stored_queries:
            return []
        
        # Generate embedding for input query
        query_embedding = self.generate_embedding(query)
        
        similar_queries = []
        
        for stored_query in stored_queries:
            if "embedding" not in stored_query:
                continue
                
            # Convert stored embedding back to numpy array
            stored_embedding = np.array(stored_query["embedding"])
            
            # Calculate similarity
            similarity = self.calculate_similarity(query_embedding, stored_embedding)
            
            if similarity >= threshold:
                similar_queries.append((stored_query, similarity))
        
        # Sort by similarity (highest first)
        similar_queries.sort(key=lambda x: x[1], reverse=True)
        
        return similar_queries
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better embedding generation
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common stop words that don't add semantic meaning
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those"
        }
        
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words]
        
        return " ".join(filtered_words)
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        # Normalize all texts
        normalized_texts = [self._normalize_text(text) for text in texts]
        
        # Generate embeddings in batch
        embeddings = self.model.encode(normalized_texts, convert_to_numpy=True)
        
        return embeddings
    
    def save_embedding(self, embedding: np.ndarray, filepath: str) -> None:
        """
        Save embedding to file
        
        Args:
            embedding: Embedding to save
            filepath: Path to save the embedding
        """
        # Convert to list for JSON serialization
        embedding_list = embedding.tolist()
        
        with open(filepath, 'w') as f:
            json.dump(embedding_list, f)
    
    def load_embedding(self, filepath: str) -> np.ndarray:
        """
        Load embedding from file
        
        Args:
            filepath: Path to the embedding file
            
        Returns:
            Loaded embedding as numpy array
        """
        with open(filepath, 'r') as f:
            embedding_list = json.load(f)
        
        return np.array(embedding_list) 