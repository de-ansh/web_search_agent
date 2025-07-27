// Enhanced API Client for RAG Backend
import axios, { AxiosResponse } from 'axios';
import { API_CONFIG } from './api-config';
import type {
    RAGChatRequest,
    RAGChatResponse,
    AgentStatusResponse,
    KnowledgeStatsResponse,
    HealthCheckResponse,
    LegacyApiResponse,
    ComprehensiveSearchResult,
    TransformedLegacyResponse
} from './types';

// Create axios instance with base configuration
const apiClient = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Enhanced RAG API Functions
export class RAGApiClient {

    /**
     * Check backend health and RAG agent status
     */
    static async checkHealth(): Promise<HealthCheckResponse> {
        try {
            const response = await apiClient.get(API_CONFIG.ENDPOINTS.HEALTH, {
                timeout: API_CONFIG.TIMEOUTS.HEALTH_CHECK
            });
            return response.data;
        } catch (error) {
            console.error('Health check failed:', error);
            throw error;
        }
    }

    /**
     * Get detailed agent status
     */
    static async getAgentStatus(): Promise<AgentStatusResponse> {
        try {
            const response = await apiClient.get(API_CONFIG.ENDPOINTS.AGENT_STATUS, {
                timeout: API_CONFIG.TIMEOUTS.HEALTH_CHECK
            });
            return response.data;
        } catch (error) {
            console.error('Agent status check failed:', error);
            throw error;
        }
    }

    /**
     * Chat with RAG agent (Primary method)
     */
    static async chatWithRAG(request: RAGChatRequest): Promise<RAGChatResponse> {
        try {
            console.log('🤖 Starting RAG chat request:', request);
            const startTime = Date.now();

            const response: AxiosResponse<RAGChatResponse> = await apiClient.post(
                API_CONFIG.ENDPOINTS.RAG_CHAT,
                {
                    ...API_CONFIG.DEFAULTS.RAG_CHAT,
                    ...request,
                },
                {
                    timeout: API_CONFIG.TIMEOUTS.RAG_CHAT
                }
            );

            const endTime = Date.now();
            console.log(`✅ RAG chat completed in ${endTime - startTime}ms`);

            return response.data;
        } catch (error) {
            console.error('❌ RAG chat failed:', error);
            throw error;
        }
    }

    /**
     * Get knowledge base statistics
     */
    static async getKnowledgeStats(): Promise<KnowledgeStatsResponse> {
        try {
            const response = await apiClient.get(API_CONFIG.ENDPOINTS.KNOWLEDGE_STATS);
            return response.data;
        } catch (error) {
            console.error('Knowledge stats failed:', error);
            throw error;
        }
    }

    /**
     * Legacy enhanced research (Fallback method)
     */
    static async legacyEnhancedResearch(query: string): Promise<LegacyApiResponse> {
        try {
            console.log('🔄 Falling back to legacy enhanced research');
            const response = await apiClient.post(
                API_CONFIG.ENDPOINTS.LEGACY_ENHANCED,
                {
                    ...API_CONFIG.DEFAULTS.LEGACY,
                    query: query.trim(),
                },
                {
                    timeout: API_CONFIG.TIMEOUTS.LEGACY
                }
            );
            return response.data;
        } catch (error) {
            console.error('Legacy enhanced research failed:', error);
            throw error;
        }
    }

    /**
     * Legacy quick research (Final fallback)
     */
    static async legacyQuickResearch(query: string): Promise<LegacyApiResponse> {
        try {
            console.log('⚡ Falling back to legacy quick research');
            const response = await apiClient.post(
                API_CONFIG.ENDPOINTS.LEGACY_QUICK,
                {
                    query: query.trim(),
                    max_sources: 3,
                    ai_method: "gemini"
                },
                {
                    timeout: API_CONFIG.TIMEOUTS.LEGACY
                }
            );
            return response.data;
        } catch (error) {
            console.error('Legacy quick research failed:', error);
            throw error;
        }
    }

    /**
     * Comprehensive search with multiple fallback strategies
     */
    static async comprehensiveSearch(query: string, conversationId?: string): Promise<ComprehensiveSearchResult> {
        // Strategy 1: Try RAG Chat (Primary)
        try {
            const ragResponse = await this.chatWithRAG({
                query,
                conversation_id: conversationId,
                use_web_search: true,
            });

            return {
                success: true,
                data: this.transformRAGResponseToLegacyFormat(ragResponse),
                method: 'rag'
            };
        } catch (ragError) {
            console.log('RAG chat failed, trying legacy methods...', ragError);
        }

        // Strategy 2: Try Legacy Enhanced Research
        try {
            const legacyResponse = await this.legacyEnhancedResearch(query);
            return {
                success: true,
                data: this.transformLegacyResponseToStandardFormat(legacyResponse),
                method: 'legacy_enhanced'
            };
        } catch (legacyError) {
            console.log('Legacy enhanced failed, trying quick research...', legacyError);
        }

        // Strategy 3: Try Legacy Quick Research
        try {
            const quickResponse = await this.legacyQuickResearch(query);
            return {
                success: true,
                data: this.transformLegacyResponseToStandardFormat(quickResponse),
                method: 'legacy_quick'
            };
        } catch (quickError) {
            console.log('All search methods failed', quickError);
        }

        // All methods failed
        return {
            success: false,
            method: 'rag',
            error: 'All search methods failed. Please check if the backend is running and try again.'
        };
    }

    /**
     * Transform legacy API response to standardized format
     */
    private static transformLegacyResponseToStandardFormat(legacyResponse: LegacyApiResponse): TransformedLegacyResponse {
        // Handle enhanced research response format
        if (legacyResponse.individual_summaries) {
            return {
                is_valid: legacyResponse.success ?? true,
                found_similar: false,
                results: legacyResponse.individual_summaries.map(summary => ({
                    title: summary.source_title,
                    url: summary.source_url,
                    summary: summary.summary,
                    summary_method: summary.method,
                    confidence: summary.confidence,
                    content_length: summary.word_count,
                    scraped_successfully: summary.scraping_success,
                    success: summary.scraping_success,
                    method: summary.scraping_method,
                    word_count: summary.word_count,
                    processing_time: summary.processing_time
                })),
                message: legacyResponse.combined_summary ?
                    `Legacy research completed. Processed ${legacyResponse.total_sources || 0} sources in ${legacyResponse.processing_time?.toFixed(1) || 'N/A'}s.` :
                    'Legacy research completed with limited results.',
                combined_summary: legacyResponse.combined_summary || ''
            };
        }

        // Handle basic sources format
        if (legacyResponse.sources) {
            return {
                is_valid: legacyResponse.success ?? true,
                found_similar: false,
                results: legacyResponse.sources.map(source => ({
                    title: source.title,
                    url: source.url,
                    summary: '', // Legacy sources don't have summaries
                    summary_method: source.method || 'legacy',
                    confidence: 0.5, // Default confidence
                    content_length: source.word_count || 0,
                    scraped_successfully: source.success,
                    success: source.success,
                    method: source.method || 'legacy',
                    word_count: source.word_count || 0,
                    processing_time: source.processing_time || 0
                })),
                message: `Legacy research completed. Found ${legacyResponse.sources.length} sources.`,
                combined_summary: legacyResponse.combined_summary || ''
            };
        }

        // Fallback for error cases
        return {
            is_valid: false,
            found_similar: false,
            results: [],
            message: legacyResponse.error || 'Legacy research failed with unknown error.',
            combined_summary: ''
        };
    }

    /**
     * Transform RAG response to legacy format for frontend compatibility
     */
    private static transformRAGResponseToLegacyFormat(ragResponse: RAGChatResponse): TransformedLegacyResponse {
        return {
            is_valid: true,
            found_similar: false,
            results: ragResponse.sources.map(source => ({
                title: source.title,
                url: source.url,
                summary: source.content.substring(0, 200) + '...',
                summary_method: 'rag_agent',
                confidence: source.relevance_score || source.score,
                content_length: source.content.length,
                scraped_successfully: true,
                success: true,
                method: source.source_type,
                word_count: source.content.split(' ').length,
                processing_time: ragResponse.processing_time / ragResponse.sources.length
            })),
            message: `Enhanced RAG research completed using ${ragResponse.method_used}. ` +
                `Processed ${ragResponse.sources.length} sources in ${ragResponse.processing_time.toFixed(1)}s. ` +
                `Confidence: ${(ragResponse.confidence_score * 100).toFixed(0)}%`,
            combined_summary: ragResponse.content,
            // Additional RAG-specific data
            rag_metadata: {
                conversation_id: ragResponse.conversation_id,
                method_used: ragResponse.method_used,
                confidence_score: ragResponse.confidence_score,
                citations: ragResponse.citations,
                processing_time: ragResponse.processing_time
            }
        };
    }

    /**
     * Type guard to check if error is an axios error
     */
    static isAxiosError(error: unknown): error is import('axios').AxiosError {
        return axios.isAxiosError(error);
    }

    /**
     * Extract error message from various error types
     */
    static getErrorMessage(error: unknown): string {
        if (this.isAxiosError(error)) {
            // Type assertion for error response data
            const errorData = error.response?.data as { detail?: string } | undefined;
            if (errorData?.detail) {
                return errorData.detail;
            }
            if (error.response?.statusText) {
                return error.response.statusText;
            }
            if (error.message) {
                return error.message;
            }
        }

        if (error instanceof Error) {
            return error.message;
        }

        return 'An unknown error occurred';
    }
}

export default RAGApiClient;