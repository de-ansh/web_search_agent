"""
Enhanced Conversation Memory Management for RAG Agent
"""

import time
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Single conversation message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    sources: List[Dict[str, Any]] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0

@dataclass
class ConversationSummary:
    """Summary of conversation for context compression"""
    conversation_id: str
    summary: str
    key_topics: List[str]
    user_preferences: Dict[str, Any]
    last_updated: float
    message_count: int

class EnhancedConversationMemory:
    """Enhanced conversation memory with context management and persistence"""
    
    def __init__(
        self, 
        max_history_length: int = 50,
        context_window_size: int = 4000,
        persist_directory: str = "./data/conversations",
        enable_summarization: bool = True
    ):
        """
        Initialize enhanced conversation memory
        
        Args:
            max_history_length: Maximum messages to keep per conversation
            context_window_size: Maximum tokens for context window
            persist_directory: Directory to persist conversations
            enable_summarization: Enable automatic summarization
        """
        self.max_history_length = max_history_length
        self.context_window_size = context_window_size
        self.persist_directory = persist_directory
        self.enable_summarization = enable_summarization
        
        # In-memory storage
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.conversation_summaries: Dict[str, ConversationSummary] = {}
        self.user_profiles: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Create persist directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Load existing conversations
        self._load_conversations()
        
        logger.info("✅ Enhanced conversation memory initialized")
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        confidence_score: float = 0.0,
        processing_time: float = 0.0
    ) -> bool:
        """Add message to conversation history with enhanced metadata"""
        try:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=time.time(),
                metadata=metadata or {},
                sources=sources or [],
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
            self.conversations[conversation_id].append(message)
            
            # Update user profile if user message
            if role == "user":
                await self._update_user_profile(conversation_id, content, metadata)
            
            # Trim if too long and summarize if needed
            if len(self.conversations[conversation_id]) > self.max_history_length:
                if self.enable_summarization:
                    await self._summarize_old_messages(conversation_id)
                else:
                    self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history_length:]
            
            # Persist conversation
            await self._persist_conversation(conversation_id)
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add message: {e}")
            return False
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_summary: bool = True
    ) -> List[Dict[str, Any]]:
        """Get conversation history with optional summary"""
        try:
            if conversation_id not in self.conversations:
                return []
            
            messages = self.conversations[conversation_id]
            if limit:
                messages = messages[-limit:]
            
            history = []
            
            # Add conversation summary if available and requested
            if include_summary and conversation_id in self.conversation_summaries:
                summary = self.conversation_summaries[conversation_id]
                history.append({
                    "role": "system",
                    "content": f"Previous conversation summary: {summary.summary}",
                    "timestamp": summary.last_updated,
                    "metadata": {
                        "type": "summary",
                        "key_topics": summary.key_topics,
                        "message_count": summary.message_count
                    }
                })
            
            # Add recent messages
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata,
                    "sources": msg.sources,
                    "confidence_score": msg.confidence_score,
                    "processing_time": msg.processing_time
                })
            
            return history
        except Exception as e:
            logger.error(f"❌ Failed to get history: {e}")
            return []
    
    async def get_context_for_llm(
        self,
        conversation_id: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, List[str]]:
        """
        Get optimized context for LLM with token management
        
        Returns:
            Tuple of (context_string, key_topics)
        """
        try:
            max_tokens = max_tokens or self.context_window_size
            
            # Get conversation history
            history = await self.get_conversation_history(conversation_id, include_summary=True)
            
            # Build context string with token estimation
            context_parts = []
            estimated_tokens = 0
            key_topics = []
            
            # Add user profile if available
            if conversation_id in self.user_profiles:
                profile = self.user_profiles[conversation_id]
                if profile:
                    profile_text = f"User preferences: {json.dumps(profile, indent=2)}"
                    context_parts.append(profile_text)
                    estimated_tokens += len(profile_text.split()) * 1.3  # Rough token estimation
            
            # Add messages in reverse order (most recent first)
            for msg in reversed(history):
                msg_text = f"{msg['role']}: {msg['content']}"
                msg_tokens = len(msg_text.split()) * 1.3
                
                if estimated_tokens + msg_tokens > max_tokens:
                    break
                
                context_parts.insert(-1 if context_parts else 0, msg_text)
                estimated_tokens += msg_tokens
                
                # Extract key topics from metadata
                if msg.get('metadata', {}).get('key_topics'):
                    key_topics.extend(msg['metadata']['key_topics'])
            
            context_string = "\n\n".join(context_parts)
            unique_topics = list(set(key_topics))
            
            return context_string, unique_topics
            
        except Exception as e:
            logger.error(f"❌ Failed to get LLM context: {e}")
            return "", []
    
    async def get_user_profile(self, conversation_id: str) -> Dict[str, Any]:
        """Get user profile for personalization"""
        return self.user_profiles.get(conversation_id, {})
    
    async def update_user_preference(
        self,
        conversation_id: str,
        preference_key: str,
        preference_value: Any
    ) -> bool:
        """Update user preference"""
        try:
            self.user_profiles[conversation_id][preference_key] = preference_value
            await self._persist_user_profile(conversation_id)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update user preference: {e}")
            return False
    
    async def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            if conversation_id not in self.conversations:
                return {}
            
            messages = self.conversations[conversation_id]
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            avg_confidence = sum(m.confidence_score for m in assistant_messages) / len(assistant_messages) if assistant_messages else 0
            avg_processing_time = sum(m.processing_time for m in assistant_messages) / len(assistant_messages) if assistant_messages else 0
            
            return {
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "avg_confidence_score": avg_confidence,
                "avg_processing_time": avg_processing_time,
                "conversation_duration": messages[-1].timestamp - messages[0].timestamp if messages else 0,
                "last_activity": messages[-1].timestamp if messages else 0
            }
        except Exception as e:
            logger.error(f"❌ Failed to get conversation stats: {e}")
            return {}
    
    def _load_conversations(self):
        """Load conversations from disk"""
        try:
            conversations_file = os.path.join(self.persist_directory, "conversations.json")
            if os.path.exists(conversations_file):
                with open(conversations_file, 'r') as f:
                    data = json.load(f)
                    
                # Load conversations
                for conv_id, messages_data in data.get('conversations', {}).items():
                    self.conversations[conv_id] = [
                        ConversationMessage(**msg) for msg in messages_data
                    ]
                
                # Load summaries
                for conv_id, summary_data in data.get('summaries', {}).items():
                    self.conversation_summaries[conv_id] = ConversationSummary(**summary_data)
                
                # Load user profiles
                self.user_profiles.update(data.get('user_profiles', {}))
                
                logger.info(f"✅ Loaded {len(self.conversations)} conversations from disk")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load conversations: {e}")
    
    async def _persist_conversation(self, conversation_id: str):
        """Persist single conversation to disk"""
        try:
            # For now, persist all conversations together
            # In production, consider per-conversation files
            await self._persist_all_conversations()
        except Exception as e:
            logger.error(f"❌ Failed to persist conversation: {e}")
    
    async def _persist_all_conversations(self):
        """Persist all conversations to disk"""
        try:
            conversations_file = os.path.join(self.persist_directory, "conversations.json")
            
            data = {
                'conversations': {
                    conv_id: [asdict(msg) for msg in messages]
                    for conv_id, messages in self.conversations.items()
                },
                'summaries': {
                    conv_id: asdict(summary)
                    for conv_id, summary in self.conversation_summaries.items()
                },
                'user_profiles': dict(self.user_profiles)
            }
            
            with open(conversations_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to persist conversations: {e}")
    
    async def _persist_user_profile(self, conversation_id: str):
        """Persist user profile"""
        await self._persist_all_conversations()
    
    async def _update_user_profile(
        self,
        conversation_id: str,
        user_message: str,
        metadata: Optional[Dict[str, Any]]
    ):
        """Update user profile based on message"""
        try:
            profile = self.user_profiles[conversation_id]
            
            # Track message count
            profile['message_count'] = profile.get('message_count', 0) + 1
            
            # Track topics of interest (simple keyword extraction)
            topics = profile.get('topics_of_interest', [])
            
            # Simple topic extraction (in production, use NLP)
            keywords = [word.lower() for word in user_message.split() 
                       if len(word) > 4 and word.isalpha()]
            
            for keyword in keywords[:3]:  # Top 3 keywords
                if keyword not in topics:
                    topics.append(keyword)
            
            profile['topics_of_interest'] = topics[-20:]  # Keep last 20 topics
            profile['last_seen'] = time.time()
            
            # Track preferences from metadata
            if metadata:
                if 'preferred_response_length' in metadata:
                    profile['preferred_response_length'] = metadata['preferred_response_length']
                if 'preferred_sources' in metadata:
                    profile['preferred_sources'] = metadata['preferred_sources']
            
        except Exception as e:
            logger.error(f"❌ Failed to update user profile: {e}")
    
    async def _summarize_old_messages(self, conversation_id: str):
        """Summarize old messages to save space"""
        try:
            messages = self.conversations[conversation_id]
            
            if len(messages) <= self.max_history_length:
                return
            
            # Keep recent messages, summarize older ones
            recent_messages = messages[-self.max_history_length//2:]
            old_messages = messages[:-self.max_history_length//2]
            
            # Create simple summary (in production, use LLM)
            user_messages = [m.content for m in old_messages if m.role == "user"]
            assistant_messages = [m.content for m in old_messages if m.role == "assistant"]
            
            key_topics = []
            for msg in old_messages:
                if msg.metadata and msg.metadata.get('key_topics'):
                    key_topics.extend(msg.metadata['key_topics'])
            
            summary_text = f"Previous conversation covered {len(user_messages)} user questions about topics including: {', '.join(set(key_topics[:10]))}"
            
            # Store summary
            self.conversation_summaries[conversation_id] = ConversationSummary(
                conversation_id=conversation_id,
                summary=summary_text,
                key_topics=list(set(key_topics)),
                user_preferences=self.user_profiles.get(conversation_id, {}),
                last_updated=time.time(),
                message_count=len(old_messages)
            )
            
            # Keep only recent messages
            self.conversations[conversation_id] = recent_messages
            
            logger.info(f"✅ Summarized {len(old_messages)} old messages for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to summarize messages: {e}")

# Backward compatibility alias
ConversationMemory = EnhancedConversationMemory