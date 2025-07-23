"""
Enhanced AI summarization service with Gemini API support
"""

import os
import re
import time
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import google.generativeai as genai
import openai
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class SummaryResult(BaseModel):
    """Result of content summarization"""
    summary: str
    method: str
    word_count: int
    original_length: int
    confidence: float
    processing_time: float

class GeminiSummarizer:
    """Enhanced AI-powered content summarization with Gemini API"""
    
    def __init__(self, preferred_method: str = "gemini"):
        """
        Initialize the enhanced content summarizer
        
        Args:
            preferred_method: Preferred summarization method ('gemini', 'openai', 'extractive')
        """
        self.preferred_method = preferred_method
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Gemini client
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Gemini client initialized successfully!")
            except Exception as e:
                logger.error(f"❌ Gemini client initialization failed: {e}")
                self.gemini_model = None
        else:
            logger.warning("⚠️  No Gemini API key found")
            self.gemini_model = None
        
        # Initialize OpenAI client as fallback
        if self.openai_api_key:
            try:
                self.openai_client = openai.Client(api_key=self.openai_api_key)
                logger.info("✅ OpenAI client initialized as fallback!")
            except Exception as e:
                logger.error(f"❌ OpenAI client initialization failed: {e}")
                self.openai_client = None
        else:
            logger.warning("⚠️  No OpenAI API key found")
            self.openai_client = None
    
    def summarize_content(
        self, 
        content: str, 
        max_length: int = 150,
        query_context: Optional[str] = None
    ) -> SummaryResult:
        """
        Summarize content using the best available method
        
        Args:
            content: Content to summarize
            max_length: Maximum length of summary in words
            query_context: Original query for context-aware summarization
            
        Returns:
            SummaryResult with summary and metadata
        """
        start_time = time.time()
        
        if not content or not content.strip():
            return SummaryResult(
                summary="No content to summarize",
                method="none",
                word_count=0,
                original_length=0,
                confidence=0.0,
                processing_time=0.0
            )
        
        # Clean and prepare content
        cleaned_content = self._clean_content(content)
        original_length = len(cleaned_content.split())
        
        # Skip summarization if content is already short
        if original_length <= max_length:
            return SummaryResult(
                summary=cleaned_content,
                method="passthrough",
                word_count=original_length,
                original_length=original_length,
                confidence=1.0,
                processing_time=time.time() - start_time
            )
        
        # Try different summarization methods based on preference and availability
        methods = self._get_available_methods()
        
        for method_name, method_func in methods:
            try:
                logger.info(f"🔄 Trying {method_name} summarization...")
                summary = method_func(cleaned_content, max_length, query_context)
                
                if summary and len(summary.strip()) > 20:  # Valid summary
                    processing_time = time.time() - start_time
                    confidence = self._get_method_confidence(method_name)
                    
                    logger.info(f"✅ {method_name} summarization successful! Generated {len(summary.split())} words in {processing_time:.2f}s")
                    
                    return SummaryResult(
                        summary=summary,
                        method=method_name,
                        word_count=len(summary.split()),
                        original_length=original_length,
                        confidence=confidence,
                        processing_time=processing_time
                    )
                else:
                    logger.warning(f"⚠️  {method_name} produced insufficient summary")
                    
            except Exception as e:
                logger.error(f"❌ Error with {method_name} summarization: {e}")
                continue
        
        # Fallback to simple truncation
        return self._simple_summarize(cleaned_content, max_length, start_time)
    
    def _get_available_methods(self) -> List[tuple]:
        """Get available summarization methods in order of preference"""
        methods = []
        
        if self.preferred_method == "gemini" and self.gemini_model:
            methods.append(("gemini", self._summarize_with_gemini))
            if self.openai_client:
                methods.append(("openai", self._summarize_with_openai))
            methods.append(("extractive", self._extractive_summarize))
            
        elif self.preferred_method == "openai" and self.openai_client:
            methods.append(("openai", self._summarize_with_openai))
            if self.gemini_model:
                methods.append(("gemini", self._summarize_with_gemini))
            methods.append(("extractive", self._extractive_summarize))
            
        else:
            # Default fallback order
            if self.gemini_model:
                methods.append(("gemini", self._summarize_with_gemini))
            if self.openai_client:
                methods.append(("openai", self._summarize_with_openai))
            methods.append(("extractive", self._extractive_summarize))
        
        return methods
    
    def _get_method_confidence(self, method_name: str) -> float:
        """Get confidence score for each method"""
        confidence_map = {
            "gemini": 0.95,
            "openai": 0.90,
            "extractive": 0.70,
            "simple": 0.50
        }
        return confidence_map.get(method_name, 0.50)
    
    def _summarize_with_gemini(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Summarize using Gemini API"""
        if not self.gemini_model:
            raise Exception("Gemini model not initialized")
        
        # Prepare context-aware prompt
        if query_context:
            prompt = f"""You are an expert research assistant. Create a comprehensive, human-readable summary that directly answers the user's question about "{query_context}".

CRITICAL REQUIREMENTS:
- Write ONLY unique, non-repetitive information
- Avoid duplicating any sentences or concepts
- Filter out navigation text, redirect messages, and web artifacts
- Focus ONLY on the core content relevant to the query: "{query_context}"
- Use natural, flowing prose without bullet points
- Organize information logically from most to least important
- Skip any content that seems like website navigation or boilerplate text
- Target approximately {max_length} words

Content to analyze:
{content[:4000]}

IMPORTANT: 
- Do NOT repeat any information
- Ignore navigation text like "Please if the page does not redirect automatically"
- Focus only on substantive content that answers the query about "{query_context}"
- Write unique, valuable information only

Please write a clear, coherent summary:"""
        else:
            prompt = f"""You are an expert research assistant. Create a comprehensive, human-readable summary of the following content.

CRITICAL REQUIREMENTS:
- Write ONLY unique, non-repetitive information
- Avoid duplicating any sentences or concepts
- Filter out navigation text, redirect messages, and web artifacts
- Focus ONLY on the core substantive content
- Use natural, flowing prose without bullet points
- Organize information logically from most to least important
- Skip any content that seems like website navigation or boilerplate text
- Target approximately {max_length} words

Content to analyze:
{content[:4000]}

IMPORTANT: 
- Do NOT repeat any information
- Ignore navigation text, redirect messages, and web artifacts
- Focus only on substantive content
- Write unique, valuable information only

Write a clear, coherent summary:"""
        
        try:
            # Generate content with Gemini
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_length * 2,  # Allow some buffer
                    temperature=0.2,  # Lower temperature for more focused output
                    top_p=0.8,
                    top_k=40
                )
            )
            
            if response.text:
                summary = response.text.strip()
                
                # Ensure summary isn't too long
                words = summary.split()
                if len(words) > max_length * 1.2:  # Allow 20% buffer
                    summary = " ".join(words[:max_length]) + "..."
                
                return summary
            else:
                raise Exception("Gemini returned empty response")
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise Exception(f"Gemini API failed: {str(e)}")
    
    def _summarize_with_openai(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Summarize using OpenAI API"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        # Prepare context-aware prompt
        if query_context:
            system_prompt = f"""You are an expert research assistant. Create a comprehensive, human-readable summary that directly answers the user's question about "{query_context}". 

CRITICAL REQUIREMENTS:
- Write ONLY unique, non-repetitive information
- Avoid duplicating any sentences or concepts
- Filter out navigation text, redirect messages, and web artifacts
- Focus ONLY on the core content relevant to the query
- Use natural, flowing prose without bullet points
- Organize information logically from most to least important
- Skip any content that seems like website navigation or boilerplate text"""
            
            user_prompt = f"""Based on the following content, provide a comprehensive summary about "{query_context}" in approximately {max_length} words.

Content to analyze:
{content[:3000]}

IMPORTANT: 
- Do NOT repeat any information
- Ignore navigation text like "Please if the page does not redirect automatically"
- Focus only on substantive content that answers the query
- Write unique, valuable information only

Please write a clear, coherent summary:"""
        else:
            system_prompt = """You are an expert research assistant. Create comprehensive, human-readable summaries that are easy to understand.

CRITICAL REQUIREMENTS:
- Write ONLY unique, non-repetitive information
- Avoid duplicating any sentences or concepts
- Filter out navigation text, redirect messages, and web artifacts
- Focus ONLY on the core substantive content
- Use natural, flowing prose without bullet points
- Organize information logically from most to least important
- Skip any content that seems like website navigation or boilerplate text"""
            
            user_prompt = f"""Please provide a comprehensive summary of the following content in approximately {max_length} words:

{content[:3000]}

IMPORTANT: 
- Do NOT repeat any information
- Ignore navigation text, redirect messages, and web artifacts
- Focus only on substantive content
- Write unique, valuable information only

Write a clear, coherent summary:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_length * 2,
                temperature=0.2,
                timeout=30
            )
            
            summary = response.choices[0].message.content
            return summary.strip() if summary else ""
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API failed: {str(e)}")
    
    def _extractive_summarize(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Enhanced extractive summarization with improved scoring"""
        sentences = self._split_into_sentences(content)
        
        if not sentences:
            return content[:max_length * 4] + "..." if len(content) > max_length * 4 else content
        
        if len(sentences) == 1:
            sentence = sentences[0]
            words = sentence.split()
            if len(words) <= max_length:
                return sentence
            return " ".join(words[:max_length]) + "..."
        
        # Score sentences based on various factors
        sentence_scores = {}
        
        # Calculate word frequencies for scoring
        all_words = []
        for sentence in sentences:
            words = [word.lower() for word in sentence.split() if len(word) > 3]
            all_words.extend(words)
        
        word_freq = {}
        for word in all_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get query keywords
        query_keywords = set()
        if query_context:
            query_keywords = set(word.lower() for word in re.findall(r'\b\w+\b', query_context) if len(word) > 2)
        
        for i, sentence in enumerate(sentences):
            score = 0
            words = sentence.split()
            sentence_words = [word.lower() for word in words if len(word) > 3]
            
            # Position score (earlier sentences are more important)
            position_score = 1.0 - (i / len(sentences))
            score += position_score * 0.3
            
            # Length score (prefer medium-length sentences)
            length = len(words)
            if 8 <= length <= 35:
                score += 0.3
            elif length > 35:
                score -= 0.2
            
            # Word frequency score
            if sentence_words:
                freq_score = sum(word_freq.get(word, 0) for word in sentence_words)
                score += (freq_score / len(sentence_words)) * 0.2
            
            # Query relevance score
            if query_keywords and sentence_words:
                sentence_word_set = set(sentence_words)
                overlap = len(query_keywords.intersection(sentence_word_set))
                if overlap > 0:
                    score += (overlap / len(query_keywords)) * 0.4
            
            # Content quality indicators
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in ['important', 'significant', 'key', 'main', 'primary']):
                score += 0.2
            
            # Avoid navigation/boilerplate
            if any(phrase in sentence_lower for phrase in ['click here', 'read more', 'subscribe', 'follow us', 'copyright']):
                score -= 0.4
            
            sentence_scores[sentence] = score
        
        # Select top sentences
        sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        
        selected_sentences = []
        total_words = 0
        
        for sentence, score in sorted_sentences:
            sentence_words = len(sentence.split())
            if total_words + sentence_words <= max_length:
                selected_sentences.append((sentence, sentences.index(sentence)))
                total_words += sentence_words
            
            if total_words >= max_length * 0.9:
                break
        
        if not selected_sentences:
            # Fallback: take first few sentences
            words_count = 0
            for i, sentence in enumerate(sentences):
                words_count += len(sentence.split())
                selected_sentences.append((sentence, i))
                if words_count >= max_length * 0.8:
                    break
        
        # Sort selected sentences by original order
        selected_sentences.sort(key=lambda x: x[1])
        
        result = " ".join([sentence for sentence, _ in selected_sentences])
        return result if result.strip() else content[:max_length * 4] + "..."
    
    def _simple_summarize(self, content: str, max_length: int, start_time: float) -> SummaryResult:
        """Fallback simple summarization"""
        words = content.split()
        summary = " ".join(words[:max_length])
        
        if len(words) > max_length:
            summary += "..."
        
        return SummaryResult(
            summary=summary,
            method="simple",
            word_count=len(summary.split()),
            original_length=len(words),
            confidence=0.5,
            processing_time=time.time() - start_time
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean and prepare content for summarization"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs
        content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '', content)
        
        # Remove excessive punctuation
        content = re.sub(r'[.]{2,}', '.', content)
        content = re.sub(r'[!]{2,}', '!', content)
        content = re.sub(r'[?]{2,}', '?', content)
        
        # Enhanced web artifacts removal
        web_artifacts = [
            "click here", "subscribe", "advertisement", "cookie policy",
            "please if the page does not redirect automatically",
            "loading", "please wait", "javascript must be enabled",
            "back to top", "skip to content", "privacy policy",
            "all rights reserved", "newsletter", "terms of service",
            "follow us on", "share this", "print this page"
        ]
        
        for artifact in web_artifacts:
            content = re.sub(re.escape(artifact), "", content, flags=re.IGNORECASE)
        
        # Remove sentences that are likely navigation or boilerplate
        sentences = re.split(r'[.!?]+', content)
        filtered_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Increased minimum length
                continue
            
            sentence_lower = sentence.lower()
            
            # Enhanced skip patterns
            skip_patterns = [
                r'please.*redirect',
                r'click.*here',
                r'javascript.*required',
                r'loading.*please.*wait',
                r'back.*to.*top',
                r'skip.*to.*content',
                r'copyright.*all.*rights',
                r'follow.*us.*on',
                r'share.*this.*page',
                r'subscribe.*to.*newsletter'
            ]
            
            should_skip = any(re.search(pattern, sentence_lower) for pattern in skip_patterns)
            
            if not should_skip:
                filtered_sentences.append(sentence)
        
        # Reconstruct content from filtered sentences
        content = '. '.join(filtered_sentences)
        
        # Remove duplicate sentences (enhanced)
        sentences = re.split(r'[.!?]+', content)
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            
            # Normalize sentence for comparison
            normalized = re.sub(r'\s+', ' ', sentence.lower())
            normalized = re.sub(r'[^\w\s]', '', normalized)
            
            # Check for substantial similarity (not just exact match)
            is_duplicate = False
            for seen in seen_sentences:
                if self._calculate_similarity(normalized, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_sentences.add(normalized)
                unique_sentences.append(sentence)
        
        # Reconstruct final content
        content = '. '.join(unique_sentences)
        if content and not content.endswith('.'):
            content += '.'
        
        return content.strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15:  # Filter out very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def batch_summarize(
        self, 
        contents: List[str], 
        max_length: int = 150,
        query_context: Optional[str] = None
    ) -> List[SummaryResult]:
        """
        Summarize multiple contents efficiently
        
        Args:
            contents: List of contents to summarize
            max_length: Maximum length per summary
            query_context: Original query for context
            
        Returns:
            List of SummaryResult objects
        """
        results = []
        
        for i, content in enumerate(contents):
            logger.info(f"Processing content {i+1}/{len(contents)}")
            result = self.summarize_content(content, max_length, query_context)
            results.append(result)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of available summarization methods"""
        return {
            "gemini_available": self.gemini_model is not None,
            "openai_available": self.openai_client is not None,
            "preferred_method": self.preferred_method,
            "fallback_methods": ["extractive", "simple"]
        }