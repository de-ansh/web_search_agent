// Comprehensive TypeScript types for RAG Frontend

// ===== CORE API TYPES =====

export interface RAGChatRequest {
  query: string;
  conversation_id?: string;
  use_web_search?: boolean;
  search_threshold?: number;
}

export interface RAGSource {
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
}

export interface RAGCitation {
  id: number;
  title: string;
  url: string;
  snippet: string;
}

export interface RAGChatResponse {
  content: string;
  sources: RAGSource[];
  conversation_id: string;
  processing_time: number;
  method_used: string;
  confidence_score: number;
  citations: RAGCitation[];
}

// ===== SYSTEM STATUS TYPES =====

export interface HealthCheckResponse {
  status: string;
  agent_ready: boolean;
  version: string;
  message?: string;
}

export interface VectorStoreInfo {
  collection_name: string;
  document_count: number;
  embedding_model: string;
  embedding_dimension: number;
}

export interface LLMModelInfo {
  model_name: string;
  provider: string;
  max_context_length: number;
  supports_streaming: boolean;
  supports_function_calling: boolean;
}

export interface AgentStatusResponse {
  agent_status: string;
  vector_store: VectorStoreInfo;
  llm_model: LLMModelInfo;
  web_search_enabled: boolean;
  max_context_docs: number;
  memory_active: boolean;
}

export interface KnowledgeStatsResponse {
  knowledge_base: VectorStoreInfo;
  timestamp: number;
}

// ===== LEGACY API TYPES =====

export interface LegacySource {
  title: string;
  url: string;
  success: boolean;
  method: string;
  word_count: number;
  processing_time: number;
}

export interface LegacyIndividualSummary {
  source_title: string;
  source_url: string;
  summary: string;
  method: string;
  confidence: number;
  word_count: number;
  processing_time: number;
  scraping_method: string;
  scraping_success: boolean;
}

export interface LegacyApiResponse {
  query?: string;
  success?: boolean;
  sources?: LegacySource[];
  combined_summary?: string;
  individual_summaries?: LegacyIndividualSummary[];
  processing_time?: number;
  method_used?: string;
  total_sources?: number;
  successful_scrapes?: number;
  error?: string;
}

// ===== FRONTEND COMPATIBILITY TYPES =====

export interface SearchResult {
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
}

export interface RAGMetadata {
  conversation_id: string;
  method_used: string;
  confidence_score: number;
  citations: RAGCitation[];
  processing_time: number;
}

export interface TransformedLegacyResponse {
  is_valid: boolean;
  found_similar: boolean;
  results: SearchResult[];
  message: string;
  combined_summary: string;
  rag_metadata?: RAGMetadata;
}

// ===== SEARCH RESULT TYPES =====

export type SearchMethod = 'rag' | 'legacy_enhanced' | 'legacy_quick';

export interface ComprehensiveSearchResult {
  success: boolean;
  data?: TransformedLegacyResponse;
  method: SearchMethod;
  error?: string;
}

// ===== ERROR TYPES =====

export interface ApiErrorResponse {
  detail: string;
  status_code?: number;
  error_type?: string;
}

export interface ApiError extends Error {
  response?: {
    status: number;
    statusText: string;
    data?: ApiErrorResponse;
  };
  code?: string;
}

// ===== UI STATE TYPES =====

export type BackendStatus = 'checking' | 'online' | 'offline';

export interface UIState {
  query: string;
  isSearching: boolean;
  searchProgress: string;
  backendStatus: BackendStatus;
  results: TransformedLegacyResponse | null;
  currentQuote: number;
}

// ===== CONFIGURATION TYPES =====

export interface ApiEndpoints {
  RAG_CHAT: string;
  RAG_STREAM: string;
  KNOWLEDGE_ADD: string;
  KNOWLEDGE_STATS: string;
  HEALTH: string;
  AGENT_STATUS: string;
  LEGACY_ENHANCED: string;
  LEGACY_QUICK: string;
}

export interface ApiTimeouts {
  RAG_CHAT: number;
  RAG_STREAM: number;
  HEALTH_CHECK: number;
  LEGACY: number;
}

export interface ApiDefaults {
  RAG_CHAT: {
    use_web_search: boolean;
    search_threshold: number;
  };
  LEGACY: {
    max_sources: number;
    summary_length: number;
    use_playwright: boolean;
    ai_method: string;
  };
}

export interface ApiConfig {
  BASE_URL: string;
  ENDPOINTS: ApiEndpoints;
  TIMEOUTS: ApiTimeouts;
  DEFAULTS: ApiDefaults;
}

// ===== UTILITY TYPES =====

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Type guards
export const isRAGChatResponse = (obj: unknown): obj is RAGChatResponse => {
  return typeof obj === 'object' &&
    obj !== null &&
    'content' in obj &&
    typeof (obj as Record<string, unknown>).content === 'string' &&
    'sources' in obj &&
    Array.isArray((obj as Record<string, unknown>).sources) &&
    'conversation_id' in obj &&
    typeof (obj as Record<string, unknown>).conversation_id === 'string' &&
    'processing_time' in obj &&
    typeof (obj as Record<string, unknown>).processing_time === 'number';
};

export const isLegacyApiResponse = (obj: unknown): obj is LegacyApiResponse => {
  return typeof obj === 'object' &&
    obj !== null && (
      'success' in obj ||
      'combined_summary' in obj ||
      'sources' in obj
    );
};

export const isApiError = (obj: unknown): obj is ApiError => {
  return obj instanceof Error && 'response' in obj;
};