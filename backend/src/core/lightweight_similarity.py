"""
Lightweight similarity detection for Render deployment (no sklearn)
"""

import os
import json
import time
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
from difflib import SequenceMatcher

class SimilarityResult(BaseModel):
    """Result of similarity detection"""
    found_similar: bool
    matched_query: Optional[str] = None
    similarity_score: float = 0.0
    cached_results: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "found_similar": self.found_similar,
            "matched_query": self.matched_query,
            "similarity_score": self.similarity_score,
            "cached_results_count": len(self.cached_results)
        }

class LightweightSimilarityDetector:
    """Lightweight similarity detector using simple text comparison"""
    
    def __init__(self, similarity_threshold: float = 0.8, cache_file: str = "data/similarity_cache.json"):
        self.similarity_threshold = similarity_threshold
        self.cache_file = cache_file
        self.stored_queries = self._load_stored_queries()
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    def find_similar_query(self, query: str) -> SimilarityResult:
        """Find similar queries using lightweight text comparison"""
        
        if not self.stored_queries:
            return SimilarityResult(found_similar=False)
        
        query_normalized = self._normalize_query(query)
        best_similarity = 0.0
        best_match = None
        
        for stored_query in self.stored_queries:
            stored_normalized = self._normalize_query(stored_query.get("query", ""))
            
            # Calculate similarity using multiple methods
            similarities = [
                self._sequence_similarity(query_normalized, stored_normalized),
                self._word_overlap_similarity(query_normalized, stored_normalized),
                self._fuzzy_similarity(query_normalized, stored_normalized)
            ]
            
            # Take the maximum similarity
            similarity = max(similarities)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = stored_query
        
        if best_similarity >= self.similarity_threshold and best_match:
            return SimilarityResult(
                found_similar=True,
                matched_query=best_match.get("query", ""),
                similarity_score=best_similarity,
                cached_results=best_match.get("results", [])
            )
        
        return SimilarityResult(found_similar=False)
    
    def store_query_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Store query results for future similarity matching"""
        
        # Clean old entries first
        self._clean_old_entries()
        
        # Check if query already exists
        query_normalized = self._normalize_query(query)
        for stored_query in self.stored_queries:
            if self._normalize_query(stored_query.get("query", "")) == query_normalized:
                # Update existing entry
                stored_query["results"] = results
                stored_query["timestamp"] = time.time()
                self._save_stored_queries()
                return
        
        # Add new entry
        new_entry = {
            "query": query,
            "results": results,
            "timestamp": time.time(),
            "query_hash": hashlib.md5(query_normalized.encode()).hexdigest()
        }
        
        self.stored_queries.append(new_entry)
        
        # Limit cache size
        if len(self.stored_queries) > 100:
            # Keep only the 80 most recent entries
            self.stored_queries = sorted(
                self.stored_queries, 
                key=lambda x: x.get("timestamp", 0),
                reverse=True
            )[:80]
        
        self._save_stored_queries()
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for comparison"""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common stop words and characters
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = normalized.split()
        words = [word for word in words if word not in stop_words]
        
        # Remove punctuation except important ones
        normalized = ' '.join(words)
        normalized = re.sub(r'[^\w\s\-\.]', '', normalized)
        
        return normalized
    
    def _sequence_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity using SequenceMatcher"""
        return SequenceMatcher(None, query1, query2).ratio()
    
    def _word_overlap_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity based on word overlap"""
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _fuzzy_similarity(self, query1: str, query2: str) -> float:
        """Calculate fuzzy similarity"""
        # Simple character-based similarity
        if not query1 or not query2:
            return 0.0
        
        longer = query1 if len(query1) > len(query2) else query2
        shorter = query2 if len(query1) > len(query2) else query1
        
        if len(longer) == 0:
            return 1.0
        
        # Count common characters
        common = 0
        for i, char in enumerate(shorter):
            if i < len(longer) and char == longer[i]:
                common += 1
        
        return common / len(longer)
    
    def _clean_old_entries(self) -> None:
        """Remove entries older than 24 hours"""
        current_time = time.time()
        cutoff_time = current_time - (24 * 60 * 60)  # 24 hours ago
        
        self.stored_queries = [
            query for query in self.stored_queries
            if query.get("timestamp", 0) > cutoff_time
        ]
    
    def _load_stored_queries(self) -> List[Dict[str, Any]]:
        """Load stored queries from cache file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different cache formats
                    if isinstance(data, list):
                        # Old format - convert queries
                        converted_queries = []
                        for item in data:
                            if isinstance(item, dict) and "query" in item:
                                converted_queries.append({
                                    "query": item["query"],
                                    "results": [],  # No cached results in old format
                                    "timestamp": time.time(),
                                    "query_hash": hashlib.md5(item["query"].lower().encode()).hexdigest()
                                })
                        return converted_queries
                    elif isinstance(data, dict):
                        # New format
                        return data.get("queries", [])
                    else:
                        return []
        except Exception as e:
            print(f"Warning: Could not load cache file: {e}")
        
        return []
    
    def _save_stored_queries(self) -> None:
        """Save stored queries to cache file"""
        try:
            cache_data = {
                "queries": self.stored_queries,
                "last_updated": time.time(),
                "version": "1.0"
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Could not save cache file: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached queries"""
        self.stored_queries = []
        self._save_stored_queries()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        return {
            "total_queries": len(self.stored_queries),
            "similarity_threshold": self.similarity_threshold,
            "cache_file": self.cache_file,
            "oldest_entry": min([q.get("timestamp", 0) for q in self.stored_queries]) if self.stored_queries else None,
            "newest_entry": max([q.get("timestamp", 0) for q in self.stored_queries]) if self.stored_queries else None
        } 