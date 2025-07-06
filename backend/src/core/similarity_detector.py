"""
Similarity detection module for finding similar past queries
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv

from ..ai.embeddings import EmbeddingService

load_dotenv()

class SimilarityResult(BaseModel):
    """Result of similarity detection"""
    found_similar: bool
    similar_queries: List[Dict[str, Any]]
    best_match: Optional[Dict[str, Any]] = None
    best_similarity: float = 0.0

class SimilarityDetector:
    """Detects similar queries using embeddings and semantic similarity"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the similarity detector
        
        Args:
            similarity_threshold: Threshold for considering queries similar (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.embedding_service = EmbeddingService()
        self.cache_file = "data/similarity_cache.json"
        self._ensure_cache_file()
    
    def find_similar_query(self, query: str) -> SimilarityResult:
        """
        Find similar queries from the stored query history
        
        Args:
            query: The input query to find similar queries for
            
        Returns:
            SimilarityResult with information about similar queries found
        """
        # Load stored queries
        stored_queries = self._load_stored_queries()
        
        if not stored_queries:
            return SimilarityResult(
                found_similar=False,
                similar_queries=[]
            )
        
        # Find similar queries using embeddings
        similar_queries = self.embedding_service.find_similar_queries(
            query=query,
            stored_queries=stored_queries,
            threshold=self.similarity_threshold
        )
        
        if not similar_queries:
            return SimilarityResult(
                found_similar=False,
                similar_queries=[]
            )
        
        # Extract the best match
        best_match, best_similarity = similar_queries[0]
        
        # Convert to list of dictionaries
        similar_queries_list = []
        for stored_query, similarity in similar_queries:
            query_dict = stored_query.copy()
            query_dict["similarity_score"] = similarity
            similar_queries_list.append(query_dict)
        
        return SimilarityResult(
            found_similar=True,
            similar_queries=similar_queries_list,
            best_match=best_match,
            best_similarity=best_similarity
        )
    
    def store_query_with_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a query with its results for future similarity detection
        
        Args:
            query: The query string
            results: List of search results
            metadata: Additional metadata about the query
        """
        # Generate embedding for the query
        embedding = self.embedding_service.generate_embedding(query)
        
        # Create query record
        query_record = {
            "query": query,
            "embedding": embedding.tolist(),  # Convert to list for JSON serialization
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Load existing queries
        stored_queries = self._load_stored_queries()
        
        # Add new query
        stored_queries.append(query_record)
        
        # Save back to file
        self._save_stored_queries(stored_queries)
    
    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent query history
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of recent queries
        """
        stored_queries = self._load_stored_queries()
        
        # Sort by timestamp (newest first)
        stored_queries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return stored_queries[:limit]
    
    def clear_old_queries(self, days: int = 30) -> int:
        """
        Clear queries older than specified days
        
        Args:
            days: Number of days to keep queries for
            
        Returns:
            Number of queries removed
        """
        stored_queries = self._load_stored_queries()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(stored_queries)
        
        # Filter out old queries
        filtered_queries = []
        for query in stored_queries:
            try:
                query_date = datetime.fromisoformat(query.get("timestamp", ""))
                if query_date >= cutoff_date:
                    filtered_queries.append(query)
            except (ValueError, TypeError):
                # Keep queries with invalid timestamps
                filtered_queries.append(query)
        
        # Save filtered queries
        self._save_stored_queries(filtered_queries)
        
        removed_count = original_count - len(filtered_queries)
        return removed_count
    
    def _load_stored_queries(self) -> List[Dict[str, Any]]:
        """Load stored queries from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        return []
    
    def _save_stored_queries(self, queries: List[Dict[str, Any]]) -> None:
        """Save queries to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        with open(self.cache_file, 'w') as f:
            json.dump(queries, f, indent=2)
    
    def _ensure_cache_file(self) -> None:
        """Ensure the cache file and directory exist"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        if not os.path.exists(self.cache_file):
            self._save_stored_queries([])
    
    def get_similarity_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored queries and similarity detection
        
        Returns:
            Dictionary with statistics
        """
        stored_queries = self._load_stored_queries()
        
        if not stored_queries:
            return {
                "total_queries": 0,
                "oldest_query": None,
                "newest_query": None,
                "average_results_per_query": 0
            }
        
        # Calculate statistics
        timestamps = []
        total_results = 0
        
        for query in stored_queries:
            try:
                timestamp = datetime.fromisoformat(query.get("timestamp", ""))
                timestamps.append(timestamp)
            except (ValueError, TypeError):
                pass
            
            results = query.get("results", [])
            total_results += len(results)
        
        return {
            "total_queries": len(stored_queries),
            "oldest_query": min(timestamps).isoformat() if timestamps else None,
            "newest_query": max(timestamps).isoformat() if timestamps else None,
            "average_results_per_query": total_results / len(stored_queries) if stored_queries else 0
        } 