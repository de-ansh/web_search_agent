'use client';

import { useState, useEffect } from 'react';
import { Search, Loader2, Brain, Lightbulb, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

interface SearchResult {
  title: string;
  url: string;
  summary?: string;
  summary_method?: string;
  confidence?: number;
  content_length?: number;
  scraped_successfully?: boolean;
}

interface ApiResponse {
  is_valid: boolean;
  found_similar: boolean;
  results: SearchResult[];
  message: string;
  combined_summary?: string;
}

const searchQuotes = [
  "The best way to find out if you can trust somebody is to trust them. - Ernest Hemingway",
  "Knowledge is power. Information is liberating. Education is the premise of progress. - Kofi Annan",
  "The important thing is not to stop questioning. Curiosity has its own reason for existing. - Albert Einstein",
  "In the middle of difficulty lies opportunity. - Albert Einstein",
  "The only true wisdom is in knowing you know nothing. - Socrates",
  "Research is what I'm doing when I don't know what I'm doing. - Wernher von Braun",
  "The greatest enemy of knowledge is not ignorance, it is the illusion of knowledge. - Stephen Hawking",
  "Learning never exhausts the mind. - Leonardo da Vinci",
  "The more that you read, the more things you will know. - Dr. Seuss",
  "Information is not knowledge. - Albert Einstein"
];

const fetchSearchResults = async (query: string) => {
  const endpoint = '/api/search';
  const requestData = { query: query.trim() };
  const timeoutMs = 120000; // 30 seconds timeout for optimized backend

  console.log(`Starting search request to ${endpoint} with timeout ${timeoutMs}ms`);
  const startTime = Date.now();
  
  try {
    const response = await axios.post<ApiResponse>(endpoint, requestData, { timeout: timeoutMs });
    const endTime = Date.now();
    console.log(`Search completed in ${endTime - startTime}ms`);
    return response.data;
  } catch (error) {
    const endTime = Date.now();
    console.log(`Search failed after ${endTime - startTime}ms:`, error);
    throw error;
  }
};

export default function Home() {
  const [query, setQuery] = useState('');
  const [currentQuote, setCurrentQuote] = useState(0);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [searchProgress, setSearchProgress] = useState('');
  const [results, setResults] = useState<ApiResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Check backend status on mount
  useEffect(() => {
    const checkBackendStatus = async () => {
      try {
        await axios.get('/api/health', { timeout: 10000 });
        setBackendStatus('online');
      } catch (error) {
        setBackendStatus('offline');
        console.error('Backend status check failed:', error);
      }
    };
    checkBackendStatus();
  }, []);

  // Clear results when input is empty
  useEffect(() => {
    if (!query.trim() && results) {
      setResults(null);
    }
  }, [query, results]);

  // Rotate quotes while searching
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSearching) {
      interval = setInterval(() => {
        setCurrentQuote((prev) => (prev + 1) % searchQuotes.length);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isSearching]);

  const performSearch = async (searchQuery: string) => {
    try {
      setIsSearching(true);
      setSearchProgress('Checking backend connection...');
      
      // Quick health check to ensure backend is responsive
      try {
        await axios.get('/api/health', { timeout: 5000 });
      } catch {
        throw new Error('Backend server is not responding. Please make sure the backend is running.');
      }
      
      setSearchProgress('Validating query...');
      
      // Show progress updates
      const progressMessages = [
        'Validating query...',
        'Searching web engines...',
        'Processing sources in parallel...',
        'Generating comprehensive summary...',
        'Finalizing results...'
      ];
      
      let messageIndex = 0;
      const progressTimer = setInterval(() => {
        messageIndex = Math.min(messageIndex + 1, progressMessages.length - 1);
        setSearchProgress(progressMessages[messageIndex]);
      }, 4000); // Faster progression for optimized backend

      const result = await fetchSearchResults(searchQuery);
      clearInterval(progressTimer);
      setResults(result);
      setSearchProgress('');
    } catch (error) {
      console.error('Search error:', error);
      let errorMessage = 'Search failed. ';
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
          errorMessage += 'Cannot connect to the backend server. Please make sure the backend is running on http://localhost:8000';
        } else if (error.response?.status === 404) {
          errorMessage += 'API endpoint not found. Please check the backend configuration.';
        } else if (error.response?.status && error.response.status >= 500) {
          errorMessage += `Server error (${error.response.status}): ${error.response?.data?.detail || error.response?.statusText || 'Internal server error'}`;
        } else if (error.code === 'ECONNABORTED') {
          errorMessage += 'Search timed out after 30 seconds. This can happen when websites are slow to respond or have heavy protection. ';
          errorMessage += 'Tips: Try more specific search terms, search for popular topics, or try again in a moment.';
        } else {
          errorMessage += `Error: ${error.response?.data?.detail || error.message}`;
        }
      } else {
        errorMessage += 'An unexpected error occurred. Please try again.';
      }
      setResults({
        is_valid: false,
        found_similar: false,
        results: [],
        message: errorMessage
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isSearching) return;
    await performSearch(query.trim());
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setSearchProgress('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-4">
            <Brain className="w-8 h-8 text-indigo-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-800">Web Search Agent</h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-3">
            Intelligent web search with AI-powered comprehensive summaries. Get Perplexity-style insights from multiple sources in seconds.
          </p>
          <div className="flex items-center justify-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${
              backendStatus === 'online' ? 'bg-green-500' : 
              backendStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <span className="text-gray-500">
              Backend: {backendStatus === 'online' ? 'Connected' : 
                       backendStatus === 'offline' ? 'Disconnected' : 'Checking...'} | 
              Frontend: v2.0 (Optimized Parallel Processing)
            </span>
          </div>
        </motion.div>

        {/* Search Form */}
        <motion.form 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onSubmit={handleSearch}
          className="max-w-4xl mx-auto mb-8"
        >
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask me anything... (e.g., 'artificial intelligence trends 2024')"
              className="w-full pl-12 pr-12 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-lg"
              disabled={isSearching}
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600"
              >
                <span className="text-xl">×</span>
              </button>
            )}
          </div>
          


          <div className="text-center mt-4">
            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="px-8 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
                              {isSearching ? (
                <span className="flex items-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Searching...
                </span>
              ) : (
                'Search'
              )}
            </button>
          </div>
        </motion.form>

        {/* Loading Quotes */}
        <AnimatePresence>
          {isSearching && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="max-w-3xl mx-auto mb-8"
            >
              <div className="bg-white rounded-xl shadow-lg p-8 text-center">
                <div className="flex items-center justify-center mb-4">
                  <Lightbulb className="w-6 h-6 text-yellow-500 mr-2" />
                  <span className="text-sm font-medium text-gray-500">
                    {searchProgress || 'Searching the web & analyzing content... This may take 1-3 minutes'}
                  </span>
                </div>
                <motion.blockquote
                  key={currentQuote}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="text-lg text-gray-700 italic leading-relaxed"
                >
                  &quot;{searchQuotes[currentQuote]}&quot;
                </motion.blockquote>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {results && !isSearching && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-6xl mx-auto"
            >
              {!results.is_valid ? (
                <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                  <div className="flex items-center mb-2">
                    <Zap className="w-5 h-5 text-red-500 mr-2" />
                    <h3 className="text-lg font-semibold text-red-800">Invalid Query</h3>
                  </div>
                  <p className="text-red-700">{results.message}</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* AI Overview - Prominent at the top */}
                  <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-xl shadow-lg border border-indigo-100 overflow-hidden">
                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-4">
                      <h2 className="text-xl font-bold text-white flex items-center">
                        <Brain className="w-6 h-6 mr-3" />
                        AI-Powered Overview
                      </h2>
                      <p className="text-indigo-100 text-sm mt-1">
                        {results.combined_summary ? 
                          `Comprehensive summary from ${results.results.length} analyzed sources` :
                          `Analysis of ${results.results.length} search results`
                        }
                      </p>
                    </div>
                    <div className="p-6">
                      {results.combined_summary ? (
                        <div className="prose prose-lg prose-gray max-w-none">
                          <div className="text-gray-800 leading-relaxed text-lg whitespace-pre-line">
                            {results.combined_summary}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-4">
                          <div className="text-gray-600 mb-2">
                            <Lightbulb className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                            No comprehensive summary available
                          </div>
                          <p className="text-gray-500 text-sm">
                            This may be due to content protection on the websites or scraping limitations. 
                            Individual source details are available below.
                          </p>
                        </div>
                      )}
                      <div className="mt-4 pt-4 border-t border-indigo-100 flex items-center justify-between text-sm text-gray-600">
                        <span className="flex items-center">
                          <Zap className="w-4 h-4 mr-1 text-indigo-500" />
                          {results.combined_summary ? 'Generated from multiple sources' : 'Individual sources available below'}
                        </span>
                        {results.found_similar && (
                          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                            From Cache
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Search Results Section */}
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-bold text-gray-800">Detailed Sources</h2>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Found {results.results.length} results</span>
                        <span className="text-gray-400">•</span>
                        <span className="flex items-center">
                          <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                          {results.results.filter(r => r.scraped_successfully).length} successfully analyzed
                        </span>
                      </div>
                    </div>

                    {/* Individual Sources */}
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600 mb-4 flex items-center">
                        <span className="flex items-center mr-4">
                          <span className="w-3 h-3 bg-indigo-500 rounded-full mr-2"></span>
                          Source materials used for the overview above
                        </span>
                      </div>
                      {results.results.map((result, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-all hover:border-indigo-200"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-start flex-1">
                              <div className="mr-3 mt-1">
                                {result.scraped_successfully ? (
                                  <div className="w-2 h-2 bg-green-500 rounded-full" title="Successfully analyzed for overview"></div>
                                ) : (
                                  <div className="w-2 h-2 bg-gray-400 rounded-full" title="Not used in overview generation"></div>
                                )}
                              </div>
                              <div className="flex-1">
                                <h3 className="text-lg font-semibold text-gray-800">
                                  <a 
                                    href={result.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="hover:text-indigo-600 transition-colors"
                                  >
                                    {result.title}
                                  </a>
                                </h3>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2 ml-4">
                              {result.scraped_successfully !== undefined && (
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  result.scraped_successfully 
                                    ? 'bg-green-100 text-green-700' 
                                    : 'bg-gray-100 text-gray-600'
                                }`}>
                                  {result.scraped_successfully ? '✓ Analyzed' : '⚠ Limited'}
                                </span>
                              )}
                              {result.confidence !== undefined && (
                                <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                                  {Math.round(result.confidence * 100)}% confidence
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <p className="text-sm text-indigo-600 mb-3 truncate font-mono bg-gray-50 px-2 py-1 rounded">
                            {result.url}
                          </p>
                          
                          {result.summary && (
                            <div className="mt-3 bg-gray-50 rounded-lg p-4">
                              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <span className="w-1 h-4 bg-indigo-500 rounded mr-2"></span>
                                Source Summary
                              </h4>
                              <p className="text-gray-700 leading-relaxed">{result.summary}</p>
                              {result.summary_method && (
                                <p className="text-xs text-gray-500 mt-2 flex items-center">
                                  <Zap className="w-3 h-3 mr-1" />
                                  Method: {result.summary_method}
                                </p>
                              )}
                            </div>
                          )}
                          
                          {result.content_length !== undefined && (
                            <p className="text-xs text-gray-500 mt-2">
                              Content length: {result.content_length} characters
                            </p>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <motion.footer 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-16 text-gray-500"
        >
          <p>Powered by AI • Built with Next.js and Tailwind CSS</p>
        </motion.footer>
      </div>
    </div>
  );
}
