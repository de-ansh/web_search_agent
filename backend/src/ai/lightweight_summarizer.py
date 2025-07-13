"""
Lightweight AI summarization service for Render deployment (no transformers)
"""

import os
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import openai
from dotenv import load_dotenv

load_dotenv()

class SummaryResult(BaseModel):
    """Result of content summarization"""
    summary: str
    method: str
    word_count: int
    original_length: int
    confidence: float

class LightweightSummarizer:
    """Lightweight AI-powered content summarization service"""
    
    def __init__(self, preferred_method: str = "extractive"):
        """
        Initialize the lightweight content summarizer
        
        Args:
            preferred_method: Preferred summarization method ('openai', 'extractive')
        """
        self.preferred_method = preferred_method
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            try:
                self.openai_client = openai.Client(api_key=self.openai_api_key)
                print("✅ OpenAI client initialized successfully!")
            except Exception as e:
                print(f"❌ OpenAI client initialization failed: {e}")
                self.openai_client = None
        else:
            print("⚠️  No OpenAI API key found, using extractive summarization")
            self.openai_client = None
    
    def summarize_content(
        self, 
        content: str, 
        max_length: int = 150,
        query_context: Optional[str] = None
    ) -> SummaryResult:
        """
        Summarize content using available methods
        
        Args:
            content: Text content to summarize
            max_length: Maximum length of summary in words
            query_context: Optional query context for better summarization
            
        Returns:
            SummaryResult with summary and metadata
        """
        if not content or len(content.strip()) < 50:
            return SummaryResult(
                summary="Content too short to summarize effectively.",
                method="error",
                word_count=0,
                original_length=len(content),
                confidence=0.0
            )
        
        # Clean content first
        cleaned_content = self._clean_content(content)
        
        # Try OpenAI first if available
        if self.openai_client and self.preferred_method == "openai":
            try:
                summary = self._summarize_with_openai(cleaned_content, max_length, query_context)
                return SummaryResult(
                    summary=summary,
                    method="openai",
                    word_count=len(summary.split()),
                    original_length=len(content),
                    confidence=0.9
                )
            except Exception as e:
                print(f"OpenAI summarization failed: {e}")
                # Fall back to extractive
        
        # Use extractive summarization as fallback
        try:
            summary = self._extractive_summarize(cleaned_content, max_length, query_context)
            return SummaryResult(
                summary=summary,
                method="extractive",
                word_count=len(summary.split()),
                original_length=len(content),
                confidence=0.7
            )
        except Exception as e:
            print(f"Extractive summarization failed: {e}")
            # Final fallback to simple truncation
            return self._simple_summarize(cleaned_content, max_length)
    
    def _summarize_with_openai(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Summarize content using OpenAI"""
        
        # Prepare the prompt
        if query_context:
            prompt = f"""Please summarize the following content in relation to the query: "{query_context}"
            
Focus on information that is most relevant to the query. Keep the summary under {max_length} words and make it informative and concise.

Content:
{content[:4000]}  # Limit content length for API

Summary:"""
        else:
            prompt = f"""Please provide a concise summary of the following content in under {max_length} words:

{content[:4000]}

Summary:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise, informative summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=min(max_length * 2, 300),  # Allow some buffer
                temperature=0.3,
                timeout=10
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Ensure summary isn't too long
            words = summary.split()
            if len(words) > max_length:
                summary = ' '.join(words[:max_length]) + "..."
            
            return summary
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise
    
    def _extractive_summarize(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """
        Extractive summarization using sentence scoring
        """
        sentences = self._split_into_sentences(content)
        
        if len(sentences) <= 2:
            return content
        
        # Score sentences based on various factors
        sentence_scores = {}
        
        # Get query keywords for context
        query_keywords = []
        if query_context:
            query_keywords = [word.lower() for word in re.findall(r'\b\w+\b', query_context)]
        
        for i, sentence in enumerate(sentences):
            score = 0
            words = sentence.lower().split()
            
            # Length bonus (prefer medium-length sentences)
            word_count = len(words)
            if 10 <= word_count <= 30:
                score += 2
            elif 5 <= word_count <= 40:
                score += 1
            
            # Position bonus (early sentences are often important)
            if i < len(sentences) * 0.3:
                score += 1
            
            # Query relevance bonus
            if query_keywords:
                for keyword in query_keywords:
                    if keyword in sentence.lower():
                        score += 2
            
            # Common important words bonus
            important_words = ['important', 'significant', 'key', 'main', 'primary', 'major', 'crucial']
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            # Avoid very short or very long sentences
            if word_count < 5 or word_count > 50:
                score -= 1
            
            sentence_scores[i] = score
        
        # Select top sentences
        target_word_count = max_length
        selected_sentences = []
        current_word_count = 0
        
        # Sort sentences by score (descending) but keep original order in output
        sorted_indices = sorted(sentence_scores.keys(), key=lambda x: sentence_scores[x], reverse=True)
        
        selected_indices = []
        for idx in sorted_indices:
            sentence_word_count = len(sentences[idx].split())
            if current_word_count + sentence_word_count <= target_word_count:
                selected_indices.append(idx)
                current_word_count += sentence_word_count
            
            if current_word_count >= target_word_count * 0.8:  # 80% of target
                break
        
        # Sort selected indices to maintain original order
        selected_indices.sort()
        
        # Build summary
        if selected_indices:
            summary_sentences = [sentences[i] for i in selected_indices]
            summary = ' '.join(summary_sentences)
        else:
            # Fallback: take first few sentences
            words_so_far = 0
            summary_sentences = []
            for sentence in sentences:
                words_in_sentence = len(sentence.split())
                if words_so_far + words_in_sentence <= max_length:
                    summary_sentences.append(sentence)
                    words_so_far += words_in_sentence
                else:
                    break
            summary = ' '.join(summary_sentences)
        
        return summary.strip()
    
    def _simple_summarize(self, content: str, max_length: int) -> SummaryResult:
        """Simple fallback summarization by truncation"""
        words = content.split()
        if len(words) <= max_length:
            summary = content
        else:
            summary = ' '.join(words[:max_length]) + "..."
        
        return SummaryResult(
            summary=summary,
            method="simple_truncation",
            word_count=len(summary.split()),
            original_length=len(content),
            confidence=0.3
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean and preprocess content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove very short lines
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        content = '\n'.join(cleaned_lines)
        
        # Remove common web artifacts
        artifacts = [
            r'cookie policy',
            r'privacy policy',
            r'terms of service',
            r'subscribe to newsletter',
            r'click here to',
            r'loading\.\.\.',
            r'please wait',
            r'error \d+',
            r'©.*all rights reserved'
        ]
        
        for artifact in artifacts:
            content = re.sub(artifact, '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def batch_summarize(
        self, 
        contents: List[str], 
        max_length: int = 150,
        query_context: Optional[str] = None
    ) -> List[SummaryResult]:
        """Batch summarize multiple contents"""
        results = []
        for content in contents:
            try:
                result = self.summarize_content(content, max_length, query_context)
                results.append(result)
            except Exception as e:
                print(f"Failed to summarize content: {e}")
                results.append(SummaryResult(
                    summary="Summarization failed",
                    method="error",
                    word_count=0,
                    original_length=len(content),
                    confidence=0.0
                ))
        return results 