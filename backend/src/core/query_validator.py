"""
Enhanced query validation module using lightweight LLM classifier for robust edge case handling
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()

class QueryValidationResult(BaseModel):
    """Result of query validation"""
    is_valid: bool
    confidence: float
    reason: str
    category: Optional[str] = None
    validation_method: str = "llm"

class QueryClassificationCache:
    """Cache for query classification results to improve performance"""
    
    def __init__(self, cache_file: str = "data/query_classification_cache.json"):
        self.cache_file = cache_file
        self._ensure_cache_file()
        
    def _ensure_cache_file(self):
        """Ensure cache file exists"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as f:
                json.dump({}, f)
    
    def get_cached_result(self, query: str) -> Optional[QueryValidationResult]:
        """Get cached validation result"""
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                
            query_key = query.lower().strip()
            if query_key in cache:
                result_data = cache[query_key]
                # Check if result is still fresh (24 hours)
                if time.time() - result_data.get('timestamp', 0) < 86400:
                    return QueryValidationResult(**result_data)
                    
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        return None
    
    def cache_result(self, query: str, result: QueryValidationResult):
        """Cache validation result"""
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            cache = {}
            
        query_key = query.lower().strip()
        result_dict = result.dict()
        result_dict['timestamp'] = time.time()
        cache[query_key] = result_dict
        
        # Keep only last 1000 entries
        if len(cache) > 1000:
            # Remove oldest entries
            sorted_items = sorted(cache.items(), key=lambda x: x[1].get('timestamp', 0))
            cache = dict(sorted_items[-1000:])
            
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

class EnhancedQueryValidator:
    """Enhanced query validator using lightweight LLM classifier"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the enhanced query validator"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.openai_client = openai.Client(api_key=self.api_key)
        else:
            self.openai_client = None
        
        self.classification_cache = QueryClassificationCache()
        
        # Enhanced category definitions
        self.valid_categories = {
            "information_search": "General information seeking queries",
            "how_to_guide": "How-to guides and tutorials",
            "definition_lookup": "Word definitions and explanations",
            "comparison_analysis": "Comparing two or more things",
            "product_research": "Product reviews and research",
            "news_current_events": "Current news and events",
            "educational_content": "Educational and learning content",
            "technical_documentation": "Technical documentation and specs",
            "location_services": "Location-based searches",
            "troubleshooting": "Problem-solving and troubleshooting"
        }
        
        self.invalid_categories = {
            "personal_action": "Personal tasks and actions",
            "device_control": "Device control commands",
            "personal_reminder": "Personal reminders and notes",
            "social_interaction": "Social media or messaging actions",
            "file_management": "File and app management",
            "scheduling": "Calendar and scheduling actions",
            "entertainment_control": "Media and entertainment control",
            "system_command": "System commands and operations"
        }
    
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Enhanced query validation using LLM classifier
        
        Args:
            query: The user's query string
            
        Returns:
            QueryValidationResult with validation details
        """
        if not query or not query.strip():
            return QueryValidationResult(
                is_valid=False,
                confidence=1.0,
                reason="Empty or whitespace-only query",
                validation_method="basic"
            )
        
        # Check cache first
        cached_result = self.classification_cache.get_cached_result(query)
        if cached_result:
            cached_result.validation_method = "cached"
            return cached_result
        
        # Basic heuristic check for obviously invalid queries
        heuristic_result = self._heuristic_check(query)
        if heuristic_result.confidence > 0.9:
            self.classification_cache.cache_result(query, heuristic_result)
            return heuristic_result
        
        # Use LLM for detailed classification
        if self.openai_client:
            llm_result = self._llm_validate_query(query)
            self.classification_cache.cache_result(query, llm_result)
            return llm_result
        else:
            # Enhanced fallback when no OpenAI API key
            enhanced_result = self._enhanced_heuristic_validation(query)
            self.classification_cache.cache_result(query, enhanced_result)
            return enhanced_result
    
    def _heuristic_check(self, query: str) -> QueryValidationResult:
        """Enhanced heuristic check for obviously invalid queries"""
        query_lower = query.lower().strip()
        
        # Strong invalid indicators
        strong_invalid_patterns = [
            r'\b(call|text|message|send)\s+\w+',
            r'\b(turn\s+on|turn\s+off|start|stop|pause|play)\s+\w+',
            r'\b(add\s+to|remove\s+from|delete)\s+\w+',
            r'\b(remind\s+me|remember\s+to|don\'t\s+forget)',
            r'\b(open|close|launch|quit)\s+\w+',
            r'\b(walk|feed|take)\s+my\s+\w+',
            r'\b(buy|purchase|order)\s+\w+',
            r'\b(schedule|book|cancel)\s+\w+',
            r'\bmy\s+(password|pin|address|phone)'
        ]
        
        for pattern in strong_invalid_patterns:
            if re.search(pattern, query_lower):
                return QueryValidationResult(
                    is_valid=False,
                    confidence=0.95,
                    reason=f"Contains personal action pattern: {pattern}",
                    category="personal_action",
                    validation_method="heuristic"
                )
        
        # Strong valid indicators
        strong_valid_patterns = [
            r'\b(what\s+is|what\s+are|what\s+does|what\s+means)',
            r'\b(how\s+to|how\s+do|how\s+can|how\s+does)',
            r'\b(why\s+is|why\s+do|why\s+does|why\s+would)',
            r'\b(when\s+is|when\s+do|when\s+does|when\s+was)',
            r'\b(where\s+is|where\s+can|where\s+to)',
            r'\b(best\s+\w+|top\s+\w+|review\s+of|comparison\s+of)',
            r'\b(tutorial|guide|instructions|documentation)',
            r'\b(definition\s+of|meaning\s+of|explain\s+\w+)',
            r'\b(difference\s+between|compare\s+\w+)',
            r'\b(latest\s+news|current\s+events|recent\s+\w+)'
        ]
        
        for pattern in strong_valid_patterns:
            if re.search(pattern, query_lower):
                return QueryValidationResult(
                    is_valid=True,
                    confidence=0.9,
                    reason=f"Contains information-seeking pattern: {pattern}",
                    category="information_search",
                    validation_method="heuristic"
                )
        
        # Ambiguous case - moderate confidence
        return QueryValidationResult(
            is_valid=True,
            confidence=0.6,
            reason="No clear indicators - defaulting to valid",
            category="information_search",
            validation_method="heuristic"
        )
    
    def _llm_validate_query(self, query: str) -> QueryValidationResult:
        """Use LLM for sophisticated query validation"""
        try:
            if not self.openai_client:
                return self._enhanced_heuristic_validation(query)
                
            system_prompt = f"""You are a sophisticated query classifier for a web search agent. 
            Your task is to determine if a user query is suitable for web search or if it's a personal task/action request.
            
            VALID QUERIES are those that can be answered through web search:
            {json.dumps(self.valid_categories, indent=2)}
            
            INVALID QUERIES are personal tasks, actions, or commands that cannot be answered by web search:
            {json.dumps(self.invalid_categories, indent=2)}
            
            Consider edge cases carefully:
            - "play music" (invalid - device control) vs "play music history" (valid - information search)
            - "call mom" (invalid - personal action) vs "call center best practices" (valid - information search)
            - "best restaurants" (valid - information search) vs "book restaurant" (invalid - personal action)
            
            Respond with ONLY a JSON object containing:
            {{
                "is_valid": boolean,
                "confidence": float (0.0 to 1.0),
                "reason": "brief explanation of decision",
                "category": "category from above lists"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: {query}"}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            content = response.choices[0].message.content
            if content:
                # Parse JSON response
                try:
                    result_data = json.loads(content.strip())
                    return QueryValidationResult(
                        **result_data,
                        validation_method="llm"
                    )
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result_data = json.loads(json_match.group())
                        return QueryValidationResult(
                            **result_data,
                            validation_method="llm"
                        )
            
            # Fallback if LLM response is malformed
            return self._enhanced_heuristic_validation(query)
                
        except Exception as e:
            print(f"Error in LLM validation: {e}")
            return self._enhanced_heuristic_validation(query)
    
    def _enhanced_heuristic_validation(self, query: str) -> QueryValidationResult:
        """Enhanced heuristic validation as fallback"""
        query_lower = query.lower().strip()
        
        # Context-aware pattern matching
        context_patterns = {
            "valid": [
                (r'\b(what|how|why|when|where|who|which)\s+', 0.8, "information_search"),
                (r'\b(best|top|good|better|worst|review|rating)\s+', 0.7, "product_research"),
                (r'\b(tutorial|guide|learn|study|understand)\s+', 0.8, "educational_content"),
                (r'\b(definition|meaning|explain|describe)\s+', 0.9, "definition_lookup"),
                (r'\b(compare|comparison|vs|versus|difference)\s+', 0.8, "comparison_analysis"),
                (r'\b(latest|recent|current|news|update)\s+', 0.7, "news_current_events"),
                (r'\b(problem|issue|error|fix|solve|troubleshoot)\s+', 0.7, "troubleshooting")
            ],
            "invalid": [
                (r'\b(call|text|message|send|email)\s+\w+', 0.9, "social_interaction"),
                (r'\b(turn\s+on|turn\s+off|start|stop|pause|play)\s+\w+', 0.9, "device_control"),
                (r'\b(add\s+to|remove\s+from|delete|create|make)\s+\w+', 0.8, "file_management"),
                (r'\b(remind|remember|note|write\s+down)', 0.9, "personal_reminder"),
                (r'\b(book|schedule|cancel|reserve)\s+\w+', 0.8, "scheduling"),
                (r'\b(walk|feed|take|bring)\s+my\s+\w+', 0.95, "personal_action"),
                (r'\b(buy|purchase|order|shop)\s+\w+', 0.8, "personal_action")
            ]
        }
        
        # Check invalid patterns first (higher priority)
        for pattern, confidence, category in context_patterns["invalid"]:
            if re.search(pattern, query_lower):
                return QueryValidationResult(
                    is_valid=False,
                    confidence=confidence,
                    reason=f"Contains pattern indicating {category}",
                    category=category,
                    validation_method="enhanced_heuristic"
                )
        
        # Check valid patterns
        for pattern, confidence, category in context_patterns["valid"]:
            if re.search(pattern, query_lower):
                return QueryValidationResult(
                    is_valid=True,
                    confidence=confidence,
                    reason=f"Contains pattern indicating {category}",
                    category=category,
                    validation_method="enhanced_heuristic"
                )
        
        # Word count and structure analysis
        words = query_lower.split()
        
        # Short queries with action verbs are likely invalid
        if len(words) <= 3:
            action_verbs = {'call', 'text', 'send', 'buy', 'get', 'take', 'make', 'do', 'go', 'come'}
            if any(word in action_verbs for word in words):
                return QueryValidationResult(
                    is_valid=False,
                    confidence=0.7,
                    reason="Short query with action verbs suggests personal task",
                    category="personal_action",
                    validation_method="enhanced_heuristic"
                )
        
        # Question structure analysis
        question_indicators = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 'does', 'is', 'are', 'can', 'will', 'should'}
        has_question_structure = any(word in question_indicators for word in words[:3])
        
        if has_question_structure:
            return QueryValidationResult(
                is_valid=True,
                confidence=0.8,
                reason="Question structure indicates information seeking",
                category="information_search",
                validation_method="enhanced_heuristic"
            )
        
        # Default to valid but with lower confidence
        return QueryValidationResult(
            is_valid=True,
            confidence=0.6,
            reason="No clear indicators - defaulting to valid",
            category="information_search",
            validation_method="enhanced_heuristic"
        )

# Backward compatibility
QueryValidator = EnhancedQueryValidator 