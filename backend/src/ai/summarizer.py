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
    
    def __init__(self, preferred_method: str = "extractive"):
        """
        Initialize the content summarizer
        
        Args:
            preferred_method: Preferred summarization method ('openai', 'huggingface', 'extractive')
        """
        self.preferred_method = preferred_method
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")  # Free alternative
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            try:
                self.openai_client = openai.Client(api_key=self.openai_api_key)
                print("✅ OpenAI client initialized successfully!")
            except Exception as e:
                print(f"❌ OpenAI client initialization failed: {e}")
                self.openai_client = None
        else:
            print("⚠️  No OpenAI API key found, using free alternatives")
            self.openai_client = None
            
        # Initialize HuggingFace pipeline
        self.hf_summarizer = None
        self._init_huggingface_summarizer()
    
    def _init_huggingface_summarizer(self):
        """Initialize HuggingFace summarization pipeline"""
        try:
            print("🔄 Initializing HuggingFace summarizer...")
            # Try multiple models in order of preference
            models_to_try = [
                "facebook/bart-large-cnn",  # Best quality but larger
                "sshleifer/distilbart-cnn-12-6",  # Smaller version of BART
                "google/pegasus-xsum",  # Alternative model
                "t5-small"  # Smallest fallback
            ]
            
            for model_name in models_to_try:
                try:
                    print(f"  Trying model: {model_name}")
                    self.hf_summarizer = pipeline(
                        "summarization",
                        model=model_name,
                        tokenizer=model_name,
                        max_length=150,
                        min_length=20,
                        do_sample=False,
                        device_map="auto" if model_name != "t5-small" else None
                    )
                    print(f"✅ HuggingFace summarizer initialized with {model_name}!")
                    return
                except Exception as model_error:
                    print(f"  ❌ Failed to load {model_name}: {model_error}")
                    continue
            
            # If all models fail
            print("❌ All HuggingFace models failed to load")
            self.hf_summarizer = None
            
        except Exception as e:
            print(f"❌ HuggingFace summarizer initialization failed: {e}")
            print("✅ Will use extractive summarization as fallback")
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
        
        # Try different summarization methods in order of availability and preference
        methods = []
        
        # Add methods based on availability
        if self.preferred_method == "extractive":
            methods.append(("extractive", self._extractive_summarize))
            if self.hf_summarizer:
                methods.append(("huggingface", self._summarize_with_huggingface))
            if self.openai_client:
                methods.append(("openai", self._summarize_with_openai))
        elif self.preferred_method == "huggingface" and self.hf_summarizer:
            methods.append(("huggingface", self._summarize_with_huggingface))
            methods.append(("extractive", self._extractive_summarize))
            if self.openai_client:
                methods.append(("openai", self._summarize_with_openai))
        elif self.preferred_method == "openai" and self.openai_client:
            methods.append(("openai", self._summarize_with_openai))
            if self.hf_summarizer:
                methods.append(("huggingface", self._summarize_with_huggingface))
            methods.append(("extractive", self._extractive_summarize))
        else:
            # Fallback order when preferred method is not available
            methods.append(("extractive", self._extractive_summarize))
            if self.hf_summarizer:
                methods.append(("huggingface", self._summarize_with_huggingface))
            if self.openai_client:
                methods.append(("openai", self._summarize_with_openai))
        
        for method_name, method_func in methods:
            try:
                print(f"🔄 Trying {method_name} summarization...")
                summary = method_func(cleaned_content, max_length, query_context)
                if summary and len(summary.strip()) > 10:  # Valid summary
                    print(f"✅ {method_name} summarization successful! Generated {len(summary.split())} words")
                    confidence = 0.9 if method_name == "openai" else 0.8 if method_name == "huggingface" else 0.7
                    return SummaryResult(
                        summary=summary,
                        method=method_name,
                        word_count=len(summary.split()),
                        original_length=original_length,
                        confidence=confidence
                    )
                else:
                    print(f"⚠️  {method_name} produced insufficient summary: {len(summary.strip()) if summary else 0} characters")
            except Exception as e:
                print(f"❌ Error with {method_name} summarization: {e}")
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
        
        # Validate content length
        if len(content) < 20:
            raise Exception("Content too short for OpenAI summarization")
        
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
                max_tokens=max_length * 2,  # Rough estimate
                temperature=0.2,  # Lower temperature for more focused output
                timeout=60  # 60 second timeout
            )
        except Exception as e:
            print(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API failed: {str(e)}")
        
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
        """Enhanced extractive summarization with improved scoring"""
        sentences = self._split_into_sentences(content)
        
        if not sentences:
            return content[:max_length * 4] + "..." if len(content) > max_length * 4 else content
        
        if len(sentences) == 1:
            # Single sentence, truncate if too long
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
                score += 0.2
            elif length > 35:
                score -= 0.1  # Penalize very long sentences
            
            # Word frequency score (common words in document are important)
            freq_score = sum(word_freq.get(word, 0) for word in sentence_words)
            score += (freq_score / len(sentence_words)) * 0.2 if sentence_words else 0
            
            # Query relevance score
            if query_context:
                query_words = set(query_context.lower().split())
                sentence_word_set = set(sentence_words)
                overlap = len(query_words.intersection(sentence_word_set))
                if query_words:
                    score += (overlap / len(query_words)) * 0.3
            
            # Avoid sentences that are likely navigation/boilerplate
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in ['click here', 'read more', 'subscribe', 'follow us']):
                score -= 0.3
            
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
            
            if total_words >= max_length * 0.9:  # Stop when we're close to the limit
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
        
        # Web artifacts removal (more selective)
        web_artifacts = [
            "click here", "subscribe", "advertisement",
            "please if the page does not redirect automatically",
            "loading", "please wait", "javascript must be enabled",
            "back to top", "skip to content",
            "all rights reserved", "newsletter"
        ]
        
        for artifact in web_artifacts:
            content = re.sub(re.escape(artifact), "", content, flags=re.IGNORECASE)
        
        # Remove sentences that are likely navigation or boilerplate
        sentences = re.split(r'[.!?]+', content)
        filtered_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            sentence_lower = sentence.lower()
            
            # Skip sentences that are likely navigation or boilerplate (reduced patterns)
            skip_patterns = [
                r'please.*redirect',
                r'click.*here',
                r'javascript.*required',
                r'loading.*please.*wait',
                r'back.*to.*top',
                r'skip.*to.*content',
                r'copyright.*all.*rights'
            ]
            
            should_skip = any(re.search(pattern, sentence_lower) for pattern in skip_patterns)
            
            if not should_skip:
                filtered_sentences.append(sentence)
        
        # Reconstruct content from filtered sentences
        content = '. '.join(filtered_sentences)
        
        # Remove duplicate sentences
        sentences = re.split(r'[.!?]+', content)
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Normalize sentence for comparison
            normalized = re.sub(r'\s+', ' ', sentence.lower())
            normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
            
            if normalized not in seen_sentences:
                seen_sentences.add(normalized)
                unique_sentences.append(sentence)
        
        # Reconstruct final content
        content = '. '.join(unique_sentences)
        if content and not content.endswith('.'):
            content += '.'
        
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