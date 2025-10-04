import React, { useState } from 'react';
import Quote from '../components/Quote';

const QuoteShowcase = () => {
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [autoRefresh, setAutoRefresh] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Quote Component Showcase
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            A beautiful, responsive React component that fetches motivational quotes 
            with elegant loading states, error handling, and auto-refresh functionality.
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Component Controls
          </h2>
          <div className="flex flex-wrap gap-4 items-center">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-sm font-medium text-gray-700">Auto Refresh</span>
            </label>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Interval:</label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="rounded border-gray-300 text-sm"
                disabled={!autoRefresh}
              >
                <option value={10000}>10 seconds</option>
                <option value={30000}>30 seconds</option>
                <option value={60000}>1 minute</option>
                <option value={300000}>5 minutes</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quote Variations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Standard Quote */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📝 Standard Quote
            </h3>
            <Quote 
              autoRefresh={autoRefresh}
              refreshInterval={refreshInterval}
            />
          </div>

          {/* Compact Quote */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📋 With Custom Styling
            </h3>
            <Quote 
              className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50"
              autoRefresh={autoRefresh}
              refreshInterval={refreshInterval}
            />
          </div>
        </div>

        {/* Full Width Quote */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            📖 Full Width Quote
          </h3>
          <Quote 
            className="w-full"
            autoRefresh={autoRefresh}
            refreshInterval={refreshInterval}
          />
        </div>

        {/* Features List */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">
            ✨ Component Features
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">API Integration</p>
                <p className="text-sm text-gray-600">Fetches from /external/quote endpoint</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Loading States</p>
                <p className="text-sm text-gray-600">Smooth loading animations</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Error Handling</p>
                <p className="text-sm text-gray-600">Graceful error states with retry</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Auto Refresh</p>
                <p className="text-sm text-gray-600">Configurable refresh intervals</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Responsive Design</p>
                <p className="text-sm text-gray-600">Works on all screen sizes</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-indigo-500 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Rich Metadata</p>
                <p className="text-sm text-gray-600">Shows author, tags, and source</p>
              </div>
            </div>
          </div>
        </div>

        {/* Code Examples */}
        <div className="mt-8 bg-gray-900 rounded-xl p-6 overflow-x-auto">
          <h3 className="text-lg font-semibold text-white mb-4">
            💻 Usage Examples
          </h3>
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-sm mb-2">Basic Usage:</p>
              <code className="text-green-400 text-sm">
                {`<Quote />`}
              </code>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm mb-2">With Auto-refresh:</p>
              <code className="text-green-400 text-sm">
                {`<Quote autoRefresh={true} refreshInterval={60000} />`}
              </code>
            </div>
            
            <div>
              <p className="text-gray-400 text-sm mb-2">Custom Styling:</p>
              <code className="text-green-400 text-sm">
                {`<Quote className="border-2 border-purple-200" />`}
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuoteShowcase;