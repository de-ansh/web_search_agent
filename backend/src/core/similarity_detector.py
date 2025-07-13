"""
Enhanced similarity detection module with LLM-based second-pass validation and KNN approach
"""

import os
import json
import time
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple, ClassVar
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from sklearn.neighbors import NearestNeighbors
import numpy as np
from difflib import SequenceMatcher

from ..ai.embeddings import EmbeddingService

load_dotenv()

class SimilarityResult(BaseModel):
    """Result of similarity detection with enhanced validation"""
    found_similar: bool
    similar_queries: List[Dict[str, Any]]
    best_match: Optional[Dict[str, Any]] = None
    best_similarity: float = 0.0
    validation_method: str = "embedding_only"
    llm_validated: bool = False
    cache_hit_reason: Optional[str] = None
    confidence_score: float = 0.0
    validation_stages: List[str] = []

class TTLPolicy(BaseModel):
    """Time-to-live policy for different query categories"""
    default_ttl: int = 86400  # 24 hours
    time_sensitive_ttl: int = 3600  # 1 hour
    stable_content_ttl: int = 604800  # 7 days
    
    # Time-sensitive categories
    time_sensitive_categories: ClassVar[List[str]] = [
        "stock_prices", "weather", "news", "sports_scores", "live_events",
        "trending_topics", "breaking_news", "current_events", "market_data",
        "traffic_conditions", "flight_status", "cryptocurrency"
    ]
    
    # Stable content categories
    stable_content_categories: ClassVar[List[str]] = [
        "tutorials", "documentation", "definitions", "concepts", "theory",
        "historical_facts", "scientific_principles", "programming_basics",
        "how_to_guides", "reference_materials", "specifications"
    ]

class EnhancedSimilarityDetector:
    """Enhanced similarity detector with multi-stage validation and stricter semantic analysis"""
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,  # Increased from 0.8
                 llm_validation_threshold: float = 0.75,  # Increased from 0.7
                 enable_llm_validation: bool = True,
                 knn_neighbors: int = 5,
                 strict_mode: bool = True):
        """
        Initialize the enhanced similarity detector
        
        Args:
            similarity_threshold: Threshold for considering queries similar (0-1)
            llm_validation_threshold: Threshold for LLM validation (0-1)
            enable_llm_validation: Whether to use LLM for second-pass validation
            knn_neighbors: Number of neighbors to consider in KNN approach
            strict_mode: Enable strict validation mode with multiple checks
        """
        self.similarity_threshold = similarity_threshold
        self.llm_validation_threshold = llm_validation_threshold
        self.enable_llm_validation = enable_llm_validation
        self.knn_neighbors = knn_neighbors
        self.strict_mode = strict_mode
        
        self.embedding_service = EmbeddingService()
        self.cache_file = "data/similarity_cache.json"
        self.ttl_policy = TTLPolicy()
        
        # Initialize OpenAI client for LLM validation
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = openai.Client(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        # KNN model for similarity search
        self.knn_model = None
        self.cached_embeddings = []
        self.cached_queries = []
        
        # Domain-specific keyword groups for strict validation
        self.domain_keywords = {
            "web_automation": ["playwright", "selenium", "puppeteer", "webdriver"],
            "programming_languages": ["python", "java", "javascript", "typescript", "go", "rust", "c++"],
            "web_frameworks": ["react", "vue", "angular", "django", "flask", "express"],
            "databases": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch"],
            "cloud_platforms": ["aws", "azure", "gcp", "google cloud", "amazon web services"],
            "testing_tools": ["jest", "pytest", "mocha", "cypress", "testcafe"],
            "version_control": ["git", "github", "gitlab", "bitbucket", "svn"],
            "operating_systems": ["windows", "linux", "macos", "ubuntu", "centos"]
        }
        
        self._ensure_cache_file()
        self._initialize_knn_model()
    
    def find_similar_query(self, query: str) -> SimilarityResult:
        """
        Find similar queries with enhanced multi-stage validation
        
        Args:
            query: The input query to find similar queries for
            
        Returns:
            SimilarityResult with enhanced validation information
        """
        validation_stages = []
        
        # Load stored queries and clean expired ones
        stored_queries = self._load_and_clean_stored_queries()
        
        if not stored_queries:
            return SimilarityResult(
                found_similar=False,
                similar_queries=[],
                validation_method="no_cache",
                validation_stages=["no_cache"]
            )
        
        # Stage 1: KNN similarity search
        validation_stages.append("knn_search")
        similar_queries = self._knn_similarity_search(query, stored_queries)
        
        if not similar_queries:
            return SimilarityResult(
                found_similar=False,
                similar_queries=[],
                validation_method="embedding_only",
                validation_stages=validation_stages
            )
        
        # Stage 2: Domain-specific validation (if strict mode)
        if self.strict_mode:
            validation_stages.append("domain_validation")
            similar_queries = self._domain_specific_validation(query, similar_queries)
            
            if not similar_queries:
                return SimilarityResult(
                    found_similar=False,
                    similar_queries=[],
                    validation_method="domain_filtered",
                    validation_stages=validation_stages
                )
        
        # Get the best match after domain filtering
        best_match, best_similarity = similar_queries[0]
        
        # Stage 3: Technology mismatch check
        validation_stages.append("technology_check")
        if self._check_technology_mismatch(query, best_match["query"]):
            return SimilarityResult(
                found_similar=False,
                similar_queries=[],
                validation_method="technology_mismatch",
                validation_stages=validation_stages
            )
        
        # Stage 4: Textual similarity check
        validation_stages.append("textual_similarity")
        textual_similarity = self._calculate_textual_similarity(query, best_match["query"])
        
        # If textual similarity is too low, reject
        if textual_similarity < 0.3:  # Very different text structure
            return SimilarityResult(
                found_similar=False,
                similar_queries=[],
                validation_method="textual_filtered",
                validation_stages=validation_stages
            )
        
        # Stage 5: LLM validation for high-confidence matches
        llm_validated = False
        llm_result = None
        
        if (self.enable_llm_validation and 
            self.openai_client and 
            best_similarity >= self.llm_validation_threshold):
            
            validation_stages.append("llm_validation")
            llm_result = self._llm_validate_similarity(query, best_match["query"])
            
            if llm_result["is_similar"] and llm_result.get("confidence", 0) >= 0.7:
                # LLM confirmed similarity with high confidence
                llm_validated = True
                confidence_score = self._calculate_confidence_score(
                    best_similarity, textual_similarity, llm_result.get("confidence", 0)
                )
                
                similar_queries_list = self._format_similar_queries(similar_queries)
                return SimilarityResult(
                    found_similar=True,
                    similar_queries=similar_queries_list,
                    best_match=best_match,
                    best_similarity=best_similarity,
                    validation_method="llm_validated",
                    llm_validated=True,
                    cache_hit_reason=llm_result["reason"],
                    confidence_score=confidence_score,
                    validation_stages=validation_stages
                )
            else:
                # LLM rejected similarity - try next best matches
                for stored_query, similarity in similar_queries[1:]:
                    if similarity >= self.llm_validation_threshold:
                        llm_result = self._llm_validate_similarity(query, stored_query["query"])
                        if llm_result["is_similar"] and llm_result.get("confidence", 0) >= 0.7:
                            llm_validated = True
                            confidence_score = self._calculate_confidence_score(
                                similarity, textual_similarity, llm_result.get("confidence", 0)
                            )
                            
                            similar_queries_list = self._format_similar_queries([(stored_query, similarity)])
                            return SimilarityResult(
                                found_similar=True,
                                similar_queries=similar_queries_list,
                                best_match=stored_query,
                                best_similarity=similarity,
                                validation_method="llm_validated",
                                llm_validated=True,
                                cache_hit_reason=llm_result["reason"],
                                confidence_score=confidence_score,
                                validation_stages=validation_stages
                            )
        
        # Stage 6: Final embedding-only validation with higher threshold
        validation_stages.append("final_embedding_check")
        
        # In strict mode, require higher similarity for embedding-only matches
        final_threshold = self.similarity_threshold + 0.05 if self.strict_mode else self.similarity_threshold
        
        if best_similarity >= final_threshold:
            confidence_score = self._calculate_confidence_score(
                best_similarity, textual_similarity, llm_result.get("confidence", 0) if llm_result else 0
            )
            
            similar_queries_list = self._format_similar_queries(similar_queries)
            return SimilarityResult(
                found_similar=True,
                similar_queries=similar_queries_list,
                best_match=best_match,
                best_similarity=best_similarity,
                validation_method="embedding_only",
                llm_validated=llm_validated,
                cache_hit_reason="High embedding similarity with domain validation",
                confidence_score=confidence_score,
                validation_stages=validation_stages
            )
        
        return SimilarityResult(
            found_similar=False,
            similar_queries=[],
            validation_method="strict_filtered",
            validation_stages=validation_stages
        )
    
    def _domain_specific_validation(self, query: str, similar_queries: List[Tuple[Dict[str, Any], float]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Apply domain-specific validation to filter out semantically different queries
        """
        query_lower = query.lower()
        query_domains = self._extract_domain_keywords(query_lower)
        
        filtered_queries = []
        
        for stored_query, similarity in similar_queries:
            stored_query_lower = stored_query["query"].lower()
            stored_domains = self._extract_domain_keywords(stored_query_lower)
            
            # Check if queries are from the same domain
            if self._are_domains_compatible(query_domains, stored_domains):
                filtered_queries.append((stored_query, similarity))
            else:
                print(f"Domain mismatch: '{query}' vs '{stored_query['query']}' - {query_domains} vs {stored_domains}")
        
        return filtered_queries
    
    def _extract_domain_keywords(self, query: str) -> List[str]:
        """Extract domain-specific keywords from a query"""
        found_domains = []
        
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    found_domains.append(domain)
                    break
        
        return found_domains
    
    def _are_domains_compatible(self, domains1: List[str], domains2: List[str]) -> bool:
        """Check if two sets of domains are compatible"""
        if not domains1 or not domains2:
            return True  # No specific domain detected
        
        # Check for exact matches
        if set(domains1) & set(domains2):
            return True
        
        # Check for incompatible domains
        incompatible_pairs = [
            ("web_automation", "programming_languages"),
            ("web_frameworks", "databases"),
            ("testing_tools", "cloud_platforms"),
            ("programming_languages", "web_frameworks"),
            ("databases", "cloud_platforms"),
            ("version_control", "testing_tools")
        ]
        
        for domain1 in domains1:
            for domain2 in domains2:
                for pair in incompatible_pairs:
                    if (domain1 in pair and domain2 in pair) and domain1 != domain2:
                        return False
        
        return True
    
    def _check_technology_mismatch(self, query1: str, query2: str) -> bool:
        """Check for specific technology mismatches within the same domain"""
        query1_lower = query1.lower()
        query2_lower = query2.lower()
        
        # Define technology groups that should not be considered similar
        technology_groups = [
            # Web automation tools
            ["playwright", "selenium", "puppeteer", "webdriver"],
            # Programming languages
            ["python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "php", "ruby"],
            # Web frameworks
            ["react", "vue", "angular", "django", "flask", "express", "spring", "laravel"],
            # Databases
            ["mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra", "oracle"],
            # Cloud platforms
            ["aws", "azure", "gcp", "google cloud", "amazon web services", "microsoft azure"],
            # Testing frameworks
            ["jest", "pytest", "mocha", "cypress", "testcafe", "junit", "rspec"],
            # Version control
            ["git", "github", "gitlab", "bitbucket", "svn", "mercurial"],
            # Operating systems
            ["windows", "linux", "macos", "ubuntu", "centos", "debian", "fedora"],
            # Mobile platforms
            ["ios", "android", "react native", "flutter", "xamarin"],
            # Product versions (iPhone models)
            ["iphone 14", "iphone 15", "iphone 13", "iphone 12"],
            # Container/orchestration
            ["docker", "kubernetes", "docker-compose", "openshift"]
        ]
        
        # Check if queries contain different technologies from the same group
        for group in technology_groups:
            found_in_query1 = [tech for tech in group if tech in query1_lower]
            found_in_query2 = [tech for tech in group if tech in query2_lower]
            
            if found_in_query1 and found_in_query2:
                # Both queries contain technologies from this group
                if not set(found_in_query1) & set(found_in_query2):
                    # But they don't share any common technologies
                    return True  # Technology mismatch detected
        
        return False  # No technology mismatch found
    
    def _calculate_textual_similarity(self, query1: str, query2: str) -> float:
        """Calculate textual similarity using sequence matching"""
        return SequenceMatcher(None, query1.lower(), query2.lower()).ratio()
    
    def _calculate_confidence_score(self, embedding_similarity: float, textual_similarity: float, llm_confidence: float) -> float:
        """Calculate overall confidence score based on multiple factors"""
        weights = {
            "embedding": 0.4,
            "textual": 0.3,
            "llm": 0.3
        }
        
        return (
            embedding_similarity * weights["embedding"] +
            textual_similarity * weights["textual"] +
            llm_confidence * weights["llm"]
        )
    
    def _knn_similarity_search(self, query: str, stored_queries: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Use KNN approach for similarity search"""
        if not self.knn_model or len(stored_queries) != len(self.cached_queries):
            self._initialize_knn_model()
        
        # Check if KNN model is available after initialization
        if not self.knn_model:
            return self._traditional_similarity_search(query, stored_queries)
        
        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Find K nearest neighbors
        try:
            distances, indices = self.knn_model.kneighbors(
                query_embedding.reshape(1, -1), 
                n_neighbors=min(self.knn_neighbors, len(stored_queries))
            )
            
            # Convert distances to similarities (cosine distance -> cosine similarity)
            similarities = 1 - distances[0]
            
            # Sort by similarity and return results
            similar_queries = []
            for idx, similarity in zip(indices[0], similarities):
                if similarity >= self.similarity_threshold:
                    similar_queries.append((stored_queries[idx], float(similarity)))
            
            # Sort by similarity (highest first)
            similar_queries.sort(key=lambda x: x[1], reverse=True)
            return similar_queries
            
        except Exception as e:
            print(f"KNN search error: {e}")
            # Fallback to traditional embedding search
            return self._traditional_similarity_search(query, stored_queries)
    
    def _traditional_similarity_search(self, query: str, stored_queries: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        """Traditional similarity search as fallback"""
        return self.embedding_service.find_similar_queries(
            query=query,
            stored_queries=stored_queries,
            threshold=self.similarity_threshold
        )
    
    def _llm_validate_similarity(self, query1: str, query2: str) -> Dict[str, Any]:
        """Use LLM to validate if two queries are semantically similar with stricter validation"""
        try:
            if not self.openai_client:
                return {"is_similar": False, "reason": "LLM not available", "confidence": 0.0}
                
            system_prompt = """You are a strict semantic similarity validator for a web search cache system.
            Your task is to determine if two queries are semantically similar enough that they would have nearly identical search results.
            
            BE VERY STRICT. Only consider queries similar if they:
            1. Have the SAME intent (seeking identical information)
            2. Are about the SAME specific topic/technology/entity
            3. Would return virtually identical search results
            4. Are at similar levels of detail/specificity
            
            Examples of SIMILAR queries (same intent, same topic):
            - "best restaurants in NYC" vs "top restaurants in New York City"
            - "how to learn Python programming" vs "Python programming tutorial for beginners"
            - "iPhone 15 features" vs "iPhone 15 specifications"
            - "install Docker on Ubuntu" vs "how to install Docker on Ubuntu"
            
            Examples of NOT SIMILAR queries (different topic/technology):
            - "best restaurants in NYC" vs "best hotels in NYC" (different intent)
            - "Python tutorial" vs "Java tutorial" (different programming language)
            - "Playwright automation" vs "Selenium automation" (different automation tools)
            - "iPhone 15 features" vs "iPhone 14 features" (different specific models)
            - "React hooks" vs "Vue composition API" (different frameworks)
            - "AWS Lambda" vs "Azure Functions" (different cloud platforms)
            
            CRITICAL: Different technologies, tools, or specific entities should NOT be considered similar
            even if they serve similar purposes.
            
            Respond with ONLY a JSON object:
            {
                "is_similar": boolean,
                "confidence": float (0.0 to 1.0),
                "reason": "brief explanation of decision focusing on key differences or similarities"
            }
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use more capable model for better accuracy
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query 1: {query1}\nQuery 2: {query2}"}
                ],
                temperature=0.0,  # Deterministic responses
                max_tokens=200,
                timeout=30  # Add timeout to prevent hanging
            )
            
            content = response.choices[0].message.content
            if content:
                try:
                    # Clean up the response to extract JSON
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    result = json.loads(content)
                    
                    # Validate the result structure
                    if not isinstance(result, dict):
                        raise ValueError("Invalid result format")
                    
                    # Ensure required fields exist
                    if "is_similar" not in result:
                        raise ValueError("Missing is_similar field")
                    
                    # Set defaults for missing fields
                    result.setdefault("confidence", 0.5)
                    result.setdefault("reason", "LLM validation completed")
                    
                    # Ensure confidence is between 0 and 1
                    result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
                    
                    return result
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"JSON parsing error: {e}, content: {content}")
                    # Try to extract JSON from response with regex
                    json_match = re.search(r'\{[^}]*"is_similar"[^}]*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group())
                            result.setdefault("confidence", 0.5)
                            result.setdefault("reason", "Extracted from partial response")
                            return result
                        except:
                            pass
            
            # Strict fallback - default to NOT similar when parsing fails
            return {"is_similar": False, "reason": "LLM response parsing failed", "confidence": 0.0}
            
        except Exception as e:
            print(f"LLM validation error: {e}")
            # Strict fallback - default to NOT similar on any error
            return {"is_similar": False, "reason": f"LLM validation failed: {str(e)}", "confidence": 0.0}
    
    def _initialize_knn_model(self):
        """Initialize KNN model with cached embeddings"""
        stored_queries = self._load_stored_queries()
        
        if not stored_queries:
            return
        
        # Extract embeddings
        embeddings = []
        queries = []
        
        for query in stored_queries:
            if "embedding" in query:
                embeddings.append(query["embedding"])
                queries.append(query)
        
        if embeddings:
            self.cached_embeddings = np.array(embeddings)
            self.cached_queries = queries
            
            # Initialize KNN model with cosine distance
            self.knn_model = NearestNeighbors(
                n_neighbors=min(self.knn_neighbors, len(embeddings)),
                metric='cosine',
                algorithm='brute'
            )
            self.knn_model.fit(self.cached_embeddings)
    
    def store_query_with_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a query with its results and TTL information
        
        Args:
            query: The query string
            results: List of search results
            metadata: Additional metadata about the query
        """
        # Generate embedding for the query
        embedding = self.embedding_service.generate_embedding(query)
        
        # Classify query for TTL policy
        query_category = self._classify_query_for_ttl(query)
        ttl = self._get_ttl_for_category(query_category)
        
        # Create query record with TTL
        query_record = {
            "query": query,
            "embedding": embedding.tolist(),
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            "ttl_seconds": ttl,
            "category": query_category,
            "metadata": metadata or {},
            "query_hash": hashlib.md5(query.encode()).hexdigest()
        }
        
        # Load existing queries
        stored_queries = self._load_stored_queries()
        
        # Remove any existing query with same hash (update)
        stored_queries = [q for q in stored_queries if q.get("query_hash") != query_record["query_hash"]]
        
        # Add new query
        stored_queries.append(query_record)
        
        # Save back to file
        self._save_stored_queries(stored_queries)
        
        # Update KNN model
        self._initialize_knn_model()
    
    def _classify_query_for_ttl(self, query: str) -> str:
        """Classify query to determine appropriate TTL policy"""
        query_lower = query.lower()
        
        # Check for time-sensitive indicators
        time_sensitive_indicators = [
            "current", "latest", "recent", "today", "now", "live", "real-time",
            "stock", "price", "weather", "news", "breaking", "trending",
            "score", "match", "game", "market", "traffic", "flight"
        ]
        
        for indicator in time_sensitive_indicators:
            if indicator in query_lower:
                return "time_sensitive"
        
        # Check for stable content indicators
        stable_indicators = [
            "tutorial", "how to", "definition", "meaning", "history",
            "concept", "theory", "basics", "fundamentals", "documentation",
            "reference", "guide", "manual", "specs", "specification"
        ]
        
        for indicator in stable_indicators:
            if indicator in query_lower:
                return "stable_content"
        
        return "default"
    
    def _get_ttl_for_category(self, category: str) -> int:
        """Get TTL seconds for a query category"""
        if category == "time_sensitive":
            return self.ttl_policy.time_sensitive_ttl
        elif category == "stable_content":
            return self.ttl_policy.stable_content_ttl
        else:
            return self.ttl_policy.default_ttl
    
    def _load_and_clean_stored_queries(self) -> List[Dict[str, Any]]:
        """Load stored queries and remove expired ones"""
        stored_queries = self._load_stored_queries()
        
        if not stored_queries:
            return []
        
        # Filter out expired queries
        current_time = datetime.now()
        valid_queries = []
        
        for query in stored_queries:
            expires_at = query.get("expires_at")
            if expires_at:
                try:
                    expiry_time = datetime.fromisoformat(expires_at)
                    if current_time <= expiry_time:
                        valid_queries.append(query)
                except ValueError:
                    # Invalid timestamp format - keep query for now
                    valid_queries.append(query)
            else:
                # No expiry time - keep query
                valid_queries.append(query)
        
        # Save cleaned queries back to file if any were removed
        if len(valid_queries) != len(stored_queries):
            self._save_stored_queries(valid_queries)
        
        return valid_queries
    
    def _format_similar_queries(self, similar_queries: List[Tuple[Dict[str, Any], float]]) -> List[Dict[str, Any]]:
        """Format similar queries for response"""
        formatted_queries = []
        for stored_query, similarity in similar_queries:
            query_dict = stored_query.copy()
            query_dict["similarity_score"] = similarity
            formatted_queries.append(query_dict)
        return formatted_queries
    
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
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache"""
        stored_queries = self._load_and_clean_stored_queries()
        
        if not stored_queries:
            return {
                "total_queries": 0,
                "expired_queries": 0,
                "categories": {},
                "avg_ttl": 0,
                "strict_mode": self.strict_mode
            }
        
        # Calculate statistics
        categories = {}
        total_ttl = 0
        
        for query in stored_queries:
            category = query.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            total_ttl += query.get("ttl_seconds", 0)
        
        return {
            "total_queries": len(stored_queries),
            "categories": categories,
            "avg_ttl": total_ttl / len(stored_queries) if stored_queries else 0,
            "knn_enabled": self.knn_model is not None,
            "llm_validation_enabled": self.enable_llm_validation,
            "strict_mode": self.strict_mode,
            "similarity_threshold": self.similarity_threshold,
            "llm_validation_threshold": self.llm_validation_threshold
        }
    
    def clear_expired_queries(self) -> int:
        """Clear expired queries from cache"""
        stored_queries = self._load_stored_queries()
        
        if not stored_queries:
            return 0
        
        current_time = datetime.now()
        valid_queries = []
        expired_count = 0
        
        for query in stored_queries:
            expires_at = query.get("expires_at")
            if expires_at:
                try:
                    expiry_time = datetime.fromisoformat(expires_at)
                    if current_time <= expiry_time:
                        valid_queries.append(query)
                    else:
                        expired_count += 1
                except ValueError:
                    # Invalid timestamp format - keep query for now
                    valid_queries.append(query)
            else:
                # No expiry time - keep query
                valid_queries.append(query)
        
        # Save cleaned queries back to file
        self._save_stored_queries(valid_queries)
        
        # Update KNN model if queries were removed
        if expired_count > 0:
            self._initialize_knn_model()
        
        return expired_count 