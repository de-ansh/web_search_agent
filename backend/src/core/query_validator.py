"""
Query validation module that uses AI to classify queries as valid or invalid.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

load_dotenv()

class QueryValidationResult(BaseModel):
    """Result of query validation"""
    is_valid: bool
    confidence: float
    reason: str
    category: Optional[str] = None

class QueryValidator:
    """Validates user queries using AI to determine if they are searchable"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the query validator"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        
        # Define valid query categories
        self.valid_categories = [
            "information_search",
            "product_search", 
            "location_search",
            "how_to",
            "definition",
            "news",
            "reviews",
            "comparison",
            "tutorial",
            "guide"
        ]
        
        # Define invalid query patterns
        self.invalid_patterns = [
            "personal_task",  # walk my pet, do laundry
            "action_request",  # add to grocery, call someone
            "personal_reminder",  # remember to buy milk
            "command",  # turn on lights, play music
            "personal_note"  # my password is, I need to
        ]
    
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        Validate if a query is suitable for web search
        
        Args:
            query: The user's query string
            
        Returns:
            QueryValidationResult with validation details
        """
        if not query or not query.strip():
            return QueryValidationResult(
                is_valid=False,
                confidence=1.0,
                reason="Empty or whitespace-only query"
            )
        
        # Quick heuristic check first
        if self._quick_invalid_check(query):
            return QueryValidationResult(
                is_valid=False,
                confidence=0.9,
                reason="Query appears to be a personal task or action request"
            )
        
        # Use AI for detailed classification if API key is available
        if self.api_key:
            return self._ai_validate_query(query)
        else:
            # Fallback to rule-based validation
            return self._rule_based_validate_query(query)
    
    def _quick_invalid_check(self, query: str) -> bool:
        """Quick check for obviously invalid queries"""
        query_lower = query.lower()
        
        # Check for personal task indicators
        personal_indicators = [
            "walk my", "feed my", "call", "text", "message",
            "add to", "buy", "purchase", "order",
            "remember to", "remind me", "don't forget",
            "turn on", "turn off", "play", "stop",
            "my password", "my phone", "my email"
        ]
        
        return any(indicator in query_lower for indicator in personal_indicators)
    
    def _ai_validate_query(self, query: str) -> QueryValidationResult:
        """Use AI to validate the query"""
        try:
            system_prompt = """You are a query classifier for a web search agent. 
            Determine if a user query is suitable for web search or if it's a personal task/action request.
            
            Valid queries are those that seek information, knowledge, or resources that can be found on the web.
            Invalid queries are personal tasks, action requests, or reminders that cannot be answered by web search.
            
            Respond with a JSON object containing:
            - is_valid: boolean
            - confidence: float (0.0 to 1.0)
            - reason: string explaining the decision
            - category: string (one of: information_search, product_search, location_search, how_to, definition, news, reviews, comparison, tutorial, guide, personal_task, action_request, personal_reminder, command, personal_note)
            
            Examples:
            - "best restaurants in NYC" -> valid, information_search
            - "walk my dog" -> invalid, personal_task
            - "Python tutorial" -> valid, tutorial
            - "add milk to grocery list" -> invalid, action_request
            """
            
            response = openai.Client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: {query}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse the response
            content = response.choices[0].message.content
            # Extract JSON from the response
            import json
            import re
            # Find JSON in the response
            if content:  # Check that content is not None
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                    return QueryValidationResult(**result_data)
                else:
                    # Fallback parsing
                    return self._parse_ai_response(content)
            
            # Fallback if content is None
            return self._rule_based_validate_query(query)
                
        except Exception as e:
            # Fallback to rule-based validation
            return self._rule_based_validate_query(query)
    
    def _parse_ai_response(self, content: str) -> QueryValidationResult:
        """Parse AI response when JSON parsing fails"""
        content_lower = content.lower()
        
        is_valid = "valid" in content_lower and "invalid" not in content_lower
        confidence = 0.8 if is_valid else 0.7
        
        # Extract category
        category = None
        for cat in self.valid_categories + self.invalid_patterns:
            if cat in content_lower:
                category = cat
                break
        
        return QueryValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            reason=content,
            category=category
        )
    
    def _rule_based_validate_query(self, query: str) -> QueryValidationResult:
        """Rule-based validation as fallback"""
        query_lower = query.lower()
        
        # Check for search indicators
        search_indicators = [
            "what is", "how to", "best", "top", "guide", "tutorial",
            "review", "compare", "vs", "difference", "definition",
            "where to", "when", "why", "who", "which"
        ]
        
        # Check for information-seeking patterns
        has_search_indicators = any(indicator in query_lower for indicator in search_indicators)
        
        # Check for personal action patterns
        action_indicators = [
            "walk", "feed", "call", "text", "message", "add to",
            "buy", "purchase", "order", "remember", "remind",
            "turn on", "turn off", "play", "stop"
        ]
        
        has_action_indicators = any(indicator in query_lower for indicator in action_indicators)
        
        if has_search_indicators and not has_action_indicators:
            return QueryValidationResult(
                is_valid=True,
                confidence=0.8,
                reason="Query contains information-seeking patterns",
                category="information_search"
            )
        elif has_action_indicators:
            return QueryValidationResult(
                is_valid=False,
                confidence=0.9,
                reason="Query appears to be a personal action request",
                category="action_request"
            )
        else:
            # Default to valid for ambiguous queries
            return QueryValidationResult(
                is_valid=True,
                confidence=0.6,
                reason="Query appears to be information-seeking",
                category="information_search"
            ) 