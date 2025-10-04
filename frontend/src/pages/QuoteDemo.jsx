import React from 'react';
import Quote from '../components/Quote';

const QuoteDemo = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Quote Component Demo
        </h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Basic Quote Component */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Standard Quote
            </h2>
            <Quote />
          </div>
          
          {/* Auto-refresh Quote Component */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Auto-refresh Quote (30s)
            </h2>
            <Quote 
              autoRefresh={true} 
              refreshInterval={30000}
              className="border-2 border-purple-200"
            />
          </div>
        </div>
        
        {/* Full width quote */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Full Width Quote
          </h2>
          <Quote className="w-full" />
        </div>
      </div>
    </div>
  );
};

export default QuoteDemo;