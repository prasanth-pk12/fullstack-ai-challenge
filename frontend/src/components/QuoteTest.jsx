import React, { useState } from 'react';
import { externalAPI } from '../services/api';

const QuoteTest = () => {
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const testQuote = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Testing quote API...');
      
      const result = await externalAPI.getQuote();
      console.log('Quote result:', result);
      setQuote(result);
      
    } catch (err) {
      console.error('Quote test error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">Quote API Test</h1>
      
      <button
        onClick={testQuote}
        disabled={loading}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Quote API'}
      </button>
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700">Error: {error}</p>
        </div>
      )}
      
      {quote && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="font-semibold mb-2">Quote Data:</h3>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(quote, null, 2)}
          </pre>
          
          <div className="mt-4 p-4 bg-white border rounded">
            <blockquote className="text-lg font-medium italic">
              "{quote.content}"
            </blockquote>
            <cite className="block mt-2 text-sm text-gray-600">
              — {quote.author}
            </cite>
            <div className="mt-2 text-xs text-gray-500">
              Source: {quote.source}
              {quote.fallback_reason && (
                <div className="mt-1 text-orange-600">
                  Fallback reason: {quote.fallback_reason}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuoteTest;