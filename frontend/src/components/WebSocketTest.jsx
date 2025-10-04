import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { tasksAPI } from '../services/api';

// Simple test component to verify WebSocket functionality
const WebSocketTest = () => {
  const { 
    connectionStatus, 
    isConnected, 
    lastMessage, 
    taskEvents, 
    reconnect 
  } = useWebSocket();
  
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  // Log connection status changes
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString();
    setTestResults(prev => [...prev, {
      type: 'connection',
      message: `Connection status: ${connectionStatus}`,
      timestamp
    }]);
  }, [connectionStatus]);

  // Log WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const timestamp = new Date().toLocaleTimeString();
      setTestResults(prev => [...prev, {
        type: 'message',
        message: `Received: ${JSON.stringify(lastMessage, null, 2)}`,
        timestamp
      }]);
    }
  }, [lastMessage]);

  const runTests = async () => {
    setIsRunning(true);
    setTestResults([]);
    
    try {
      // Test 1: Check connection
      addTestResult('Test 1: Checking WebSocket connection...');
      if (!isConnected) {
        addTestResult('❌ WebSocket not connected. Attempting to reconnect...', 'error');
        reconnect();
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      if (isConnected) {
        addTestResult('✅ WebSocket connected successfully', 'success');
      } else {
        addTestResult('❌ WebSocket connection failed', 'error');
        return;
      }

      // Test 2: Create a test task
      addTestResult('Test 2: Creating test task...');
      const testTask = {
        title: `WebSocket Test Task ${Date.now()}`,
        description: 'This is a test task created to verify WebSocket functionality',
        status: 'todo',
        priority: 'medium'
      };
      
      await tasksAPI.createTask(testTask);
      addTestResult('✅ Test task created successfully', 'success');
      
      // Wait for WebSocket event
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Test 3: Check if WebSocket event was received
      const recentTaskEvents = taskEvents.filter(event => 
        event.type === 'task_created' && 
        Date.now() - event.timestamp < 5000
      );
      
      if (recentTaskEvents.length > 0) {
        addTestResult('✅ WebSocket task_created event received', 'success');
      } else {
        addTestResult('❌ WebSocket task_created event not received', 'error');
      }

      addTestResult('Test completed!', 'info');
      
    } catch (error) {
      addTestResult(`❌ Test failed: ${error.message}`, 'error');
    } finally {
      setIsRunning(false);
    }
  };

  const addTestResult = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setTestResults(prev => [...prev, {
      type,
      message,
      timestamp
    }]);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">WebSocket Test Console</h2>
          <p className="text-gray-600">Test real-time functionality and connection status</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-400' : connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'
          }`} />
          <span className="text-sm font-medium">
            {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
          </span>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <button
          onClick={runTests}
          disabled={isRunning}
          className={`px-4 py-2 rounded-lg font-medium text-white transition-colors ${
            isRunning 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isRunning ? 'Running Tests...' : 'Run WebSocket Tests'}
        </button>
        
        <button
          onClick={reconnect}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
        >
          Reconnect
        </button>
        
        <button
          onClick={clearResults}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          Clear Results
        </button>
      </div>

      {/* Test Results */}
      <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
        <h3 className="font-medium text-gray-900 mb-3">Test Results & Events</h3>
        
        {testResults.length === 0 ? (
          <p className="text-gray-500 text-sm">No test results yet. Click "Run WebSocket Tests" to begin.</p>
        ) : (
          <div className="space-y-2">
            {testResults.map((result, index) => (
              <div key={index} className={`text-sm p-2 rounded ${
                result.type === 'success' ? 'bg-green-100 text-green-800' :
                result.type === 'error' ? 'bg-red-100 text-red-800' :
                result.type === 'connection' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                <span className="font-mono text-xs text-gray-500">[{result.timestamp}]</span>{' '}
                <span className="whitespace-pre-wrap">{result.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* WebSocket Stats */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{taskEvents.length}</div>
          <div className="text-sm text-blue-800">Task Events Received</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {taskEvents.filter(e => e.type === 'task_created').length}
          </div>
          <div className="text-sm text-green-800">Tasks Created</div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {taskEvents.filter(e => e.type === 'task_updated').length}
          </div>
          <div className="text-sm text-purple-800">Tasks Updated</div>
        </div>
      </div>
    </div>
  );
};

export default WebSocketTest;