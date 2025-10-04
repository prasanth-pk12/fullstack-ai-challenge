import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowPathIcon, 
  ExclamationTriangleIcon,
  ChatBubbleLeftIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { externalAPI } from '../services/api';
import toast from 'react-hot-toast';

const Quote = ({ className = '', autoRefresh = false, refreshInterval = 30000 }) => {
  const [quote, setQuote] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetched, setLastFetched] = useState(null);

  const fetchQuote = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('Fetching quote from API...');
      const quoteData = await externalAPI.getQuote();
      console.log('Quote data received:', quoteData);
      
      setQuote(quoteData);
      setLastFetched(new Date());
      
      // Show fallback notification if applicable
      if (quoteData.fallback_reason) {
        const isSSLError = quoteData.fallback_reason.includes('SSL') || quoteData.fallback_reason.includes('certificate');
        const message = isSSLError 
          ? 'External API unavailable (SSL issue) - using local quote'
          : `Using fallback: ${quoteData.fallback_reason.substring(0, 50)}...`;
        
        toast(message, {
          duration: 4000,
          icon: isSSLError ? '🔒' : '📝'
        });
      }
      
    } catch (err) {
      console.error('Failed to fetch quote:', err);
      
      // More specific error handling
      let errorMessage = 'Failed to fetch quote';
      
      if (err.response?.status === 502) {
        errorMessage = 'External quote service unavailable';
      } else if (err.response?.status === 503) {
        errorMessage = 'Quote service temporarily unavailable';
      } else if (err.response?.status === 504) {
        errorMessage = 'Quote service timeout';
      } else if (err.response?.data?.detail?.message) {
        errorMessage = err.response.data.detail.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      toast.error('Failed to load inspirational quote');
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchQuote();
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh || !refreshInterval) return;

    const interval = setInterval(fetchQuote, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const handleRefresh = () => {
    if (!isLoading) {
      fetchQuote();
    }
  };

  const formatTimeAgo = (date) => {
    if (!date) return '';
    
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const getSourceIcon = (source) => {
    if (source === 'fallback' || source === 'local_fallback') return '📝';
    if (source?.includes('quotable')) return '💭';
    if (source?.includes('local')) return '🏠';
    return '✨';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 shadow-sm border border-indigo-100 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <SparklesIcon className="w-4 h-4 text-indigo-600" />
          <h3 className="text-base font-semibold text-gray-900">Daily Inspiration</h3>
        </div>
        
        <motion.button
          onClick={handleRefresh}
          disabled={isLoading}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="p-1.5 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Get new quote"
        >
          <ArrowPathIcon 
            className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} 
          />
        </motion.button>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {isLoading && !quote ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-6"
          >
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-2"></div>
            <p className="text-gray-600 text-xs">Loading inspiration...</p>
          </motion.div>
        ) : error ? (
          <motion.div
            key="error"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="flex flex-col items-center justify-center py-6"
          >
            <ExclamationTriangleIcon className="w-8 h-8 text-orange-500 mb-2" />
            <p className="text-gray-700 font-medium mb-1 text-sm">Unable to load quote</p>
            <p className="text-gray-500 text-xs text-center mb-3">{error}</p>
            <motion.button
              onClick={handleRefresh}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-xs font-medium"
            >
              Try Again
            </motion.button>
          </motion.div>
        ) : quote ? (
          <motion.div
            key="quote"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-2"
          >
            {/* Quote Content */}
            <div className="relative">
              <ChatBubbleLeftIcon className="absolute -top-1 -left-1 w-5 h-5 text-indigo-200" />
              <blockquote className="text-gray-800 text-sm font-medium leading-relaxed pl-4 pr-1">
                "{quote.content}"
              </blockquote>
            </div>

            {/* Author */}
            <div className="flex items-center justify-between">
              <cite className="text-indigo-700 font-semibold not-italic text-sm">
                — {quote.author}
              </cite>
              
              {/* Source & metadata */}
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                <span className="flex items-center space-x-1">
                  <span>{getSourceIcon(quote.source)}</span>
                  <span>
                    {quote.source === 'fallback' || quote.source === 'local_fallback' 
                      ? 'Local' 
                      : quote.source?.includes('quotable') ? 'API' : 'External'
                    }
                  </span>
                </span>
                {lastFetched && (
                  <span>• {formatTimeAgo(lastFetched)}</span>
                )}
              </div>
            </div>

            {/* Tags */}
            {quote.tags && quote.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-1">
                {quote.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded-full font-medium"
                  >
                    #{tag}
                  </span>
                ))}
                {quote.tags.length > 3 && (
                  <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                    +{quote.tags.length - 3} more
                  </span>
                )}
              </div>
            )}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
};

export default Quote;