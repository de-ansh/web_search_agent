// API Configuration for Enhanced RAG Backend
export const API_CONFIG = {
  // Backend URL - adjust based on your setup
  BASE_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
  
  // New RAG endpoints
  ENDPOINTS: {
    // Enhanced RAG Chat (Primary)
    RAG_CHAT: '/agent/chat',
    RAG_STREAM: '/agent/stream',
    
    // Knowledge management
    KNOWLEDGE_ADD: '/knowledge/add',
    KNOWLEDGE_STATS: '/knowledge/stats',
    
    // System status
    HEALTH: '/health',
    AGENT_STATUS: '/agent/status',
    
    // Legacy compatibility (fallback)
    LEGACY_ENHANCED: '/research/enhanced',
    LEGACY_QUICK: '/research/quick',
  },
  
  // Request timeouts
  TIMEOUTS: {
    RAG_CHAT: 60000,      // 1 minute for RAG chat
    RAG_STREAM: 120000,   // 2 minutes for streaming
    HEALTH_CHECK: 5000,   // 5 seconds for health
    LEGACY: 300000,       // 5 minutes for legacy (kept for compatibility)
  },
  
  // Default request parameters
  DEFAULTS: {
    RAG_CHAT: {
      use_web_search: true,
      search_threshold: 0.7,
    },
    LEGACY: {
      max_sources: 5,
      summary_length: 150,
      use_playwright: true,
      ai_method: "gemini"
    }
  }
};

// RAG Chat Request Interface
export interface RAGChatRequest {
  query: string;
  conversation_id?: string;
  use_web_search?: boolean;
  search_threshold?: number;
}

// RAG Chat Response Interface
export interface RAGChatResponse {
  content: string;
  sources: Array<{
    title: string;
    url: string;
    content: string;
    score: number;
    source_type: string;
    relevance_score?: number;
    authority_score?: number;
    content_quality_score?: number;
    key_topics?: string[];
    sentiment?: string;
  }>;
  conversation_id: string;
  processing_time: number;
  method_used: string;
  confidence_score: number;
  citations: Array<{
    id: number;
    title: string;
    url: string;
    snippet: string;
  }>;
}

// Agent Status Response Interface
export interface AgentStatusResponse {
  agent_status: string;
  vector_store: {
    collection_name: string;
    document_count: number;
    embedding_model: string;
    embedding_dimension: number;
  };
  llm_model: {
    model_name: string;
    provider: string;
    max_context_length: number;
    supports_streaming: boolean;
    supports_function_calling: boolean;
  };
  web_search_enabled: boolean;
  max_context_docs: number;
  memory_active: boolean;
}

// Knowledge Base Stats Response Interface
export interface KnowledgeStatsResponse {
  knowledge_base: {
    collection_name: string;
    document_count: number;
    embedding_model: string;
    embedding_dimension: number;
  };
  timestamp: number;
}

// Health Check Response Interface
export interface HealthCheckResponse {
  status: string;
  agent_ready: boolean;
  version: string;
  message?: string;
}

// Legacy API Response Interfaces
export interface LegacyApiResponse {
  query?: string;
  success?: boolean;
  sources?: Array<{
    title: string;
    url: string;
    success: boolean;
    method: string;
    word_count: number;
    processing_time: number;
  }>;
  combined_summary?: string;
  individual_summaries?: Array<{
    source_title: string;
    source_url: string;
    summary: string;
    method: string;
    confidence: number;
    word_count: number;
    processing_time: number;
    scraping_method: string;
    scraping_success: boolean;
  }>;
  processing_time?: number;
  method_used?: string;
  total_sources?: number;
  successful_scrapes?: number;
  error?: string;
}

// Comprehensive Search Result Interface
export interface ComprehensiveSearchResult {
  success: boolean;
  data?: TransformedLegacyResponse;
  method: 'rag' | 'legacy_enhanced' | 'legacy_quick';
  error?: string;
}

// Transformed Legacy Response Interface (for frontend compatibility)
export interface TransformedLegacyResponse {
  is_valid: boolean;
  found_similar: boolean;
  results: Array<{
    title: string;
    url: string;
    summary: string;
    summary_method: string;
    confidence: number;
    content_length: number;
    scraped_successfully: boolean;
    success: boolean;
    method: string;
    word_count: number;
    processing_time: number;
  }>;
  message: string;
  combined_summary: string;
  rag_metadata?: {
    conversation_id: string;
    method_used: string;
    confidence_score: number;
    citations: Array<{
      id: number;
      title: string;
      url: string;
      snippet: string;
    }>;
    processing_time: number;
  };
}

// API Error Response Interface
export interface ApiErrorResponse {
  detail: string;
  status_code?: number;
  error_type?: string;
}