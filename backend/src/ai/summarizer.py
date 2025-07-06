"""
AI-powered content summarization service
"""

import os
import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import openai
from transformers.pipelines import pipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv

load_dotenv()

class SummaryResult(BaseModel):
    """Result of content summarization"""
    summary: str
    method: str
    word_count: int
    original_length: int
    confidence: float

class ContentSummarizer:
    """AI-powered content summarization service"""
    
    def __init__(self, preferred_method: str = "openai"):
        """
        Initialize the content summarizer
        
        Args:
            preferred_method: Preferred summarization method ('openai', 'huggingface', 'extractive')
        """
        self.preferred_method = preferred_method
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            self.openai_client = openai.Client(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            
        # Initialize HuggingFace pipeline
        self.hf_summarizer = None
        self._init_huggingface_summarizer()
    
    def _init_huggingface_summarizer(self):
        """Initialize HuggingFace summarization pipeline"""
        try:
            # Use a smaller, faster summarization model
            model_name = "sshleifer/distilbart-cnn-12-6"  # Smaller version of BART
            print(f"Initializing HuggingFace summarizer with {model_name}...")
            self.hf_summarizer = pipeline(
                "summarization",
                model=model_name,
                tokenizer=model_name,
                max_length=150,
                min_length=30,
                do_sample=False
            )
            print("✅ HuggingFace summarizer initialized successfully!")
        except Exception as e:
            print(f"Warning: Could not initialize HuggingFace summarizer: {e}")
            print("Falling back to extractive summarization")
            self.hf_summarizer = None
    
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
        if not content or not content.strip():
            return SummaryResult(
                summary="No content to summarize",
                method="none",
                word_count=0,
                original_length=0,
                confidence=0.0
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
                confidence=1.0
            )
        
        # Try different summarization methods in order of preference
        methods = [
            ("openai", self._summarize_with_openai),
            ("huggingface", self._summarize_with_huggingface),
            ("extractive", self._extractive_summarize)
        ]
        
        # Prioritize preferred method
        if self.preferred_method != "openai":
            methods = [(method, func) for method, func in methods if method != "openai"] + \
                     [("openai", self._summarize_with_openai)]
        
        for method_name, method_func in methods:
            try:
                summary = method_func(cleaned_content, max_length, query_context)
                if summary and len(summary.strip()) > 10:  # Valid summary
                    return SummaryResult(
                        summary=summary,
                        method=method_name,
                        word_count=len(summary.split()),
                        original_length=original_length,
                        confidence=0.9 if method_name == "openai" else 0.8
                    )
            except Exception as e:
                print(f"Error with {method_name} summarization: {e}")
                continue
        
        # Fallback to simple truncation
        return self._simple_summarize(cleaned_content, max_length)
    
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

Write in clear, flowing prose that:
- Directly addresses the user's query
- Organizes information logically
- Uses natural language transitions
- Avoids bullet points or fragmented sentences
- Focuses on the most relevant and important information
- Maintains a professional but accessible tone"""
            
            user_prompt = f"""Based on the following content, provide a comprehensive summary about "{query_context}" in approximately {max_length} words.

Content to analyze:
{content[:3000]}

Please write a clear, coherent summary that would help someone understand the key information about this topic:"""
        else:
            system_prompt = """You are an expert research assistant. Create comprehensive, human-readable summaries that are easy to understand.

Write in clear, flowing prose that:
- Organizes information logically
- Uses natural language transitions
- Avoids bullet points or fragmented sentences
- Focuses on the most important information
- Maintains a professional but accessible tone"""
            
            user_prompt = f"""Please provide a comprehensive summary of the following content in approximately {max_length} words:

{content[:3000]}

Write a clear, coherent summary:"""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_length * 2,  # Rough estimate
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        return summary.strip() if summary else ""
    
    def _summarize_with_huggingface(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Summarize using HuggingFace model"""
        if not self.hf_summarizer:
            raise Exception("HuggingFace summarizer not initialized")
        
        # Truncate content to fit model limits
        max_input_length = 1024
        if len(content) > max_input_length:
            content = content[:max_input_length]
        
        # Generate summary
        summary_result = self.hf_summarizer(
            content,
            max_length=min(max_length, 150),
            min_length=min(30, max_length // 3),
            do_sample=False
        )
        
        return summary_result[0]['summary_text']
    
    def _extractive_summarize(
        self, 
        content: str, 
        max_length: int, 
        query_context: Optional[str] = None
    ) -> str:
        """Simple extractive summarization"""
        sentences = self._split_into_sentences(content)
        
        if not sentences:
            return ""
        
        # Score sentences based on various factors
        sentence_scores = {}
        
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position score (earlier sentences are more important)
            position_score = 1.0 - (i / len(sentences))
            score += position_score * 0.3
            
            # Length score (prefer medium-length sentences)
            length = len(sentence.split())
            if 10 <= length <= 30:
                score += 0.2
            
            # Query relevance score
            if query_context:
                query_words = set(query_context.lower().split())
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words.intersection(sentence_words))
                score += (overlap / len(query_words)) * 0.5
            
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
            
            if total_words >= max_length * 0.8:  # Stop when we're close to the limit
                break
        
        # Sort selected sentences by original order
        selected_sentences.sort(key=lambda x: x[1])
        
        return " ".join([sentence for sentence, _ in selected_sentences])
    
    def _simple_summarize(self, content: str, max_length: int) -> SummaryResult:
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
            confidence=0.5
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
        
        # Remove common web artifacts
        web_artifacts = [
            "click here", "read more", "continue reading", "subscribe", "advertisement",
            "cookies", "privacy policy", "terms of service", "share this", "follow us"
        ]
        
        for artifact in web_artifacts:
            content = re.sub(artifact, "", content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Filter out very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def batch_summarize(
        self, 
        contents: List[str], 
        max_length: int = 150,
        query_context: Optional[str] = None
    ) -> List[SummaryResult]:
        """
        Summarize multiple contents
        
        Args:
            contents: List of contents to summarize
            max_length: Maximum length per summary
            query_context: Original query for context
            
        Returns:
            List of SummaryResult objects
        """
        results = []
        
        for content in contents:
            result = self.summarize_content(content, max_length, query_context)
            results.append(result)
        
        return results 