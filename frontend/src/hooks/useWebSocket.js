import { useState, useEffect, useCallback, useRef } from 'react';
import { webSocketService } from '../services/websocket';
import { useAuth } from '../contexts/AuthContext';

export const useWebSocket = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [taskEvents, setTaskEvents] = useState([]);
  const { user, token, isLoading } = useAuth();
  
  // Use refs to avoid stale closures
  const eventListenersRef = useRef(new Map());
  const taskEventHandlersRef = useRef(new Set());

  // Connection status handler
  const handleStatusChange = useCallback((status) => {
    console.log(`useWebSocket: Status change received: ${status}`);
    setConnectionStatus(status);
    setIsConnected(status === 'connected');
  }, []);

  // Generic message handler
  const handleMessage = useCallback((data) => {
    setLastMessage(data);
    
    // Add to task events if it's a task-related message
    if (data.type && ['task_created', 'task_updated', 'task_deleted'].includes(data.type)) {
      setTaskEvents(prev => [...prev.slice(-49), { ...data, timestamp: Date.now() }]); // Keep last 50 events
      
      // Notify task event handlers
      taskEventHandlersRef.current.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('Error in task event handler:', error);
        }
      });
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    console.log(`WebSocket Hook: Effect triggered - isLoading: ${isLoading}, user: ${user ? user.username : 'null'}, token: ${token ? 'exists' : 'null'}`);
    
    // Wait for auth loading to complete
    if (isLoading) {
      console.log('WebSocket: Waiting for auth to complete loading...');
      return;
    }
    
    if (!user || !token) {
      // Disconnect if user is not authenticated
      console.log('WebSocket: No user or token, disconnecting');
      webSocketService.disconnect();
      setConnectionStatus('disconnected');
      setIsConnected(false);
      return;
    }

    // Connect WebSocket for all authenticated users
    // Users receive updates for their own tasks, admins receive updates for all tasks
    console.log(`WebSocket: Setting up connection for user (${user.role}) - Username: ${user.username}`);

    // Set up status listener
    const unsubscribeStatus = webSocketService.onStatusChange(handleStatusChange);
    
    // Set up message listener
    const unsubscribeMessage = webSocketService.on('message', handleMessage);

    // Connect to WebSocket
    webSocketService.connect().catch(error => {
      console.error('Failed to connect to WebSocket:', error);
    });

    // Cleanup on unmount or user change
    return () => {
      console.log('WebSocket: Cleaning up connection listeners');
      unsubscribeStatus();
      unsubscribeMessage();
    };
  }, [user, token, isLoading, handleStatusChange, handleMessage]);

  // Subscribe to specific event types
  const subscribe = useCallback((eventType, callback) => {
    const unsubscribe = webSocketService.on(eventType, callback);
    
    // Store the unsubscribe function
    if (!eventListenersRef.current.has(eventType)) {
      eventListenersRef.current.set(eventType, new Set());
    }
    eventListenersRef.current.get(eventType).add(unsubscribe);

    // Return unsubscribe function
    return () => {
      unsubscribe();
      if (eventListenersRef.current.has(eventType)) {
        eventListenersRef.current.get(eventType).delete(unsubscribe);
      }
    };
  }, []);

  // Subscribe to task events specifically
  const onTaskEvent = useCallback((handler) => {
    taskEventHandlersRef.current.add(handler);
    
    // Return unsubscribe function
    return () => {
      taskEventHandlersRef.current.delete(handler);
    };
  }, []);

  // Send message (for future use)
  const sendMessage = useCallback((data) => {
    return webSocketService.send(data);
  }, []);

  // Force reconnect
  const reconnect = useCallback(() => {
    webSocketService.disconnect();
    setTimeout(() => {
      webSocketService.connect().catch(error => {
        console.error('Failed to reconnect to WebSocket:', error);
      });
    }, 1000);
  }, []);

  // Manual disconnect
  const disconnect = useCallback(() => {
    webSocketService.disconnect();
  }, []);

  return {
    // Connection state
    connectionStatus,
    isConnected,
    
    // Message data
    lastMessage,
    taskEvents,
    
    // Event subscription
    subscribe,
    onTaskEvent,
    
    // Connection control
    reconnect,
    disconnect,
    sendMessage,
    
    // Convenience getters
    isConnecting: connectionStatus === 'connecting',
    isDisconnected: connectionStatus === 'disconnected',
    hasError: connectionStatus === 'error'
  };
};

// Hook specifically for task events with handlers
export const useTaskEvents = (handlers = {}) => {
  const { onTaskEvent, isConnected, connectionStatus } = useWebSocket();
  
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = onTaskEvent((data) => {
      const { type, task, user: eventUser } = data;
      
      switch (type) {
        case 'task_created':
          handlers.onTaskCreated?.(task, eventUser);
          break;
        case 'task_updated':
          handlers.onTaskUpdated?.(task, eventUser);
          break;
        case 'task_deleted':
          handlers.onTaskDeleted?.(data.task_id, eventUser);
          break;
        default:
          handlers.onUnknownEvent?.(data);
      }
    });

    return unsubscribe;
  }, [isConnected, handlers, onTaskEvent]);

  return {
    isConnected,
    connectionStatus
  };
};

export default useWebSocket;