"""
Gemini LLM Client for RAG Agent
"""

import os
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import google.generativeai as genai
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    model: str
    tokens_used: int
    processing_time: float
    citations: List[Dict[str, Any]]

class GeminiClient:
    """Gemini LLM client for RAG operations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (defaults to env var)
            model: Model to use (gemini-1.5-flash, gemini-1.5-pro)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"✅ Gemini client initialized with model: {self.model_name}")
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> LLMResponse:
        """
        Generate response using RAG context
        
        Args:
            query: User query
            context: Retrieved context documents
            conversation_history: Previous conversation
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Build prompt with context
            prompt = self._build_rag_prompt(query, context, conversation_history)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.8,
                    top_k=40
                )
            )
            
            # Extract citations from context
            citations = self._extract_citations(context)
            
            processing_time = time.time() - start_time
            
            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_used=self._estimate_tokens(response.text),
                processing_time=processing_time,
                citations=citations
            )
            
        except Exception as e:
            logger.error(f"❌ Gemini generation failed: {e}")
            raise Exception(f"LLM generation failed: {e}")
    
    async def generate_streaming_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response for real-time output
        
        Args:
            query: User query
            context: Retrieved context documents
            conversation_history: Previous conversation
            temperature: Generation temperature
            
        Yields:
            Chunks of generated text
        """
        try:
            prompt = self._build_rag_prompt(query, context, conversation_history)
            
            # Note: Gemini streaming might need different implementation
            # This is a placeholder for streaming functionality
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    top_p=0.8,
                    top_k=40
                ),
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"❌ Streaming generation failed: {e}")
            yield f"Error: {str(e)}"
    
    def _build_rag_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build enhanced RAG prompt with intelligent context integration"""
        
        # Analyze query type for better prompt engineering
        query_type = self._analyze_query_type(query)
        
        # Build enhanced context section with relevance scores
        context_text = ""
        if context:
            context_text = "## Retrieved Information Sources:\n\n"
            for i, doc in enumerate(context, 1):
                title = doc.get('title', 'Unknown Source')
                content = doc.get('content', '')
                url = doc.get('url', '')
                score = doc.get('relevance_score', doc.get('score', 0.0))
                authority = doc.get('authority_score', 0.5)
                key_topics = doc.get('key_topics', [])
                
                # Truncate content if too long
                if len(content) > 800:
                    content = content[:800] + "... [content truncated]"
                
                context_text += f"**[Source {i}] {title}** (Relevance: {score:.2f}, Authority: {authority:.2f})\n"
                if url:
                    context_text += f"🔗 URL: {url}\n"
                if key_topics:
                    context_text += f"🏷️ Key Topics: {', '.join(key_topics[:5])}\n"
                context_text += f"📄 Content: {content}\n\n"
        
        # Build conversation context with user preferences
        history_text = ""
        user_context = ""
        if conversation_history:
            # Extract user preferences and context
            user_preferences = self._extract_user_preferences(conversation_history)
            if user_preferences:
                user_context = f"## User Context:\n{user_preferences}\n\n"
            
            # Add recent conversation history
            history_text = "## Recent Conversation:\n\n"
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', 0)
                
                # Truncate long messages
                if len(content) > 200:
                    content = content[:200] + "..."
                
                history_text += f"**{role.title()}**: {content}\n"
            history_text += "\n"
        
        # Select prompt template based on query type
        if query_type == "factual":
            instruction_template = self._get_factual_instructions()
        elif query_type == "analytical":
            instruction_template = self._get_analytical_instructions()
        elif query_type == "creative":
            instruction_template = self._get_creative_instructions()
        elif query_type == "technical":
            instruction_template = self._get_technical_instructions()
        else:
            instruction_template = self._get_general_instructions()
        
        # Build the complete prompt
        prompt = f"""You are an advanced AI research assistant with access to curated information sources. Your goal is to provide accurate, insightful, and well-researched responses.

{user_context}{history_text}{context_text}## Current Query:
{query}

{instruction_template}

## Response:"""

        return prompt
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze query type for better prompt engineering"""
        query_lower = query.lower()
        
        # Factual queries
        factual_indicators = ['what is', 'who is', 'when did', 'where is', 'how many', 'define', 'explain']
        if any(indicator in query_lower for indicator in factual_indicators):
            return "factual"
        
        # Analytical queries
        analytical_indicators = ['analyze', 'compare', 'evaluate', 'assess', 'why', 'how does', 'what are the implications']
        if any(indicator in query_lower for indicator in analytical_indicators):
            return "analytical"
        
        # Technical queries
        technical_indicators = ['implement', 'code', 'algorithm', 'technical', 'programming', 'debug', 'error']
        if any(indicator in query_lower for indicator in technical_indicators):
            return "technical"
        
        # Creative queries
        creative_indicators = ['create', 'generate', 'write', 'design', 'brainstorm', 'suggest ideas']
        if any(indicator in query_lower for indicator in creative_indicators):
            return "creative"
        
        return "general"
    
    def _get_factual_instructions(self) -> str:
        """Instructions for factual queries"""
        return """## Instructions for Factual Response:
1. **Accuracy First**: Provide precise, factual information based on the retrieved sources
2. **Source Attribution**: Clearly cite which source each fact comes from using [Source X] notation
3. **Completeness**: Cover all relevant aspects of the question
4. **Verification**: If sources conflict, mention the discrepancy and explain which is more reliable
5. **Clarity**: Use clear, straightforward language
6. **Limitations**: If information is incomplete or uncertain, state this clearly

**Response Format**: Start with a direct answer, then provide supporting details with citations."""
    
    def _get_analytical_instructions(self) -> str:
        """Instructions for analytical queries"""
        return """## Instructions for Analytical Response:
1. **Multi-Perspective Analysis**: Consider different viewpoints from the sources
2. **Evidence-Based Reasoning**: Support all claims with evidence from retrieved sources
3. **Critical Thinking**: Evaluate the quality and reliability of different sources
4. **Structured Analysis**: Organize your response with clear sections (e.g., pros/cons, causes/effects)
5. **Synthesis**: Combine information from multiple sources to provide insights
6. **Balanced View**: Present multiple sides of complex issues

**Response Format**: Provide analysis with clear reasoning, supported by cited evidence."""
    
    def _get_technical_instructions(self) -> str:
        """Instructions for technical queries"""
        return """## Instructions for Technical Response:
1. **Precision**: Use accurate technical terminology and concepts
2. **Step-by-Step**: Break down complex processes into clear steps
3. **Code Examples**: Include relevant code snippets or examples when applicable
4. **Best Practices**: Mention industry standards and best practices
5. **Troubleshooting**: Address potential issues or common mistakes
6. **Resources**: Point to additional technical resources when helpful

**Response Format**: Provide technical details with practical examples and clear explanations."""
    
    def _get_creative_instructions(self) -> str:
        """Instructions for creative queries"""
        return """## Instructions for Creative Response:
1. **Innovation**: Use retrieved information as inspiration for creative solutions
2. **Practical Application**: Ensure creative ideas are grounded in real information
3. **Multiple Options**: Provide several creative alternatives when possible
4. **Feasibility**: Consider the practicality of creative suggestions
5. **Inspiration Sources**: Acknowledge what inspired each creative element
6. **Adaptability**: Explain how ideas can be modified or adapted

**Response Format**: Present creative ideas with explanations of their basis in the source material."""
    
    def _get_general_instructions(self) -> str:
        """General instructions for mixed or unclear query types"""
        return """## Instructions for Comprehensive Response:
1. **Contextual Understanding**: Interpret the query in context of the conversation
2. **Source Integration**: Seamlessly weave information from multiple sources
3. **Relevance**: Focus on the most relevant information for the user's needs
4. **Clarity**: Use clear, accessible language appropriate for the topic
5. **Completeness**: Address all aspects of the query thoroughly
6. **Citations**: Always cite sources using [Source X] notation
7. **Honesty**: Clearly state if information is insufficient or uncertain

**Response Format**: Provide a well-structured, comprehensive answer with proper citations."""
    
    def _extract_user_preferences(self, conversation_history: List[Dict[str, str]]) -> str:
        """Extract user preferences from conversation history"""
        preferences = []
        
        # Look for preference indicators in user messages
        for msg in conversation_history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                # Response length preferences
                if 'brief' in content or 'short' in content or 'summary' in content:
                    preferences.append("Prefers concise responses")
                elif 'detailed' in content or 'comprehensive' in content or 'thorough' in content:
                    preferences.append("Prefers detailed explanations")
                
                # Format preferences
                if 'example' in content or 'examples' in content:
                    preferences.append("Values concrete examples")
                if 'step by step' in content or 'steps' in content:
                    preferences.append("Prefers step-by-step explanations")
                
                # Topic interests (simple extraction)
                if 'technical' in content or 'programming' in content:
                    preferences.append("Interested in technical topics")
                if 'business' in content or 'marketing' in content:
                    preferences.append("Interested in business topics")
        
        if preferences:
            return "User preferences based on conversation: " + "; ".join(set(preferences))
        return ""
    
    def _extract_citations(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citation information from context"""
        citations = []
        
        for i, doc in enumerate(context, 1):
            citation = {
                "id": i,
                "title": doc.get('title', 'Unknown Source'),
                "url": doc.get('url', ''),
                "snippet": doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                "relevance_score": doc.get('score', 0.0)
            }
            citations.append(citation)
        
        return citations
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "provider": "Google Gemini",
            "max_context_length": 32000,  # Approximate for Gemini 1.5
            "supports_streaming": True,
            "supports_function_calling": True
        }