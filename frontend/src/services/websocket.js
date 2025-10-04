import { getToken } from './api';

export class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.listeners = new Map();
    this.connectionStatus = 'disconnected'; // disconnected, connecting, connected, error
    this.statusListeners = new Set();
    this.isManuallyDisconnected = false;
    this.heartbeatInterval = null;
    this.missedHeartbeats = 0;
    this.maxMissedHeartbeats = 3;
  }

  // Connection management
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }

    this.isManuallyDisconnected = false;
    return this._connect();
  }

  _connect() {
    return new Promise((resolve, reject) => {
      try {
        const token = getToken();
        if (!token) {
          this._setStatus('error');
          reject(new Error('No authentication token available'));
          return;
        }

        this._setStatus('connecting');
        console.log('Connecting to WebSocket...');

        // Create WebSocket connection with token authentication
        const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/tasks?token=${encodeURIComponent(token)}`;
        this.ws = new WebSocket(wsUrl);

        // Connection opened
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this._setStatus('connected');
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000; // Reset delay
          this._startHeartbeat();
          resolve();
        };

        // Message received
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this._handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error, event.data);
          }
        };

        // Connection closed
        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this._setStatus('disconnected');
          this._stopHeartbeat();
          
          if (!this.isManuallyDisconnected && !event.wasClean) {
            this._attemptReconnect();
          }
        };

        // Connection error
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this._setStatus('error');
          this._stopHeartbeat();
          reject(error);
        };

      } catch (error) {
        this._setStatus('error');
        reject(error);
      }
    });
  }

  disconnect() {
    this.isManuallyDisconnected = true;
    this._stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this._setStatus('disconnected');
  }

  // Heartbeat to keep connection alive
  _startHeartbeat() {
    this._stopHeartbeat(); // Clear any existing heartbeat
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
        this.missedHeartbeats++;
        
        if (this.missedHeartbeats >= this.maxMissedHeartbeats) {
          console.warn('Too many missed heartbeats, reconnecting...');
          this._attemptReconnect();
        }
      }
    }, 30000); // Send ping every 30 seconds
  }

  _stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.missedHeartbeats = 0;
  }

  // Handle incoming messages
  _handleMessage(data) {
    // Reset missed heartbeats on any message
    this.missedHeartbeats = 0;
    
    // Handle pong response
    if (data.type === 'pong') {
      return;
    }

    // Handle task events
    if (data.type && this.listeners.has(data.type)) {
      const callbacks = this.listeners.get(data.type);
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket message handler:', error);
        }
      });
    }

    // Handle generic message listeners
    if (this.listeners.has('message')) {
      const callbacks = this.listeners.get('message');
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket message handler:', error);
        }
      });
    }
  }

  // Reconnection logic
  _attemptReconnect() {
    if (this.isManuallyDisconnected || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnection attempts reached or manually disconnected');
      this._setStatus('error');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`);

    setTimeout(() => {
      if (!this.isManuallyDisconnected) {
        this._connect().catch(() => {
          // Exponential backoff with jitter
          this.reconnectDelay = Math.min(
            this.reconnectDelay * 2 + Math.random() * 1000,
            this.maxReconnectDelay
          );
        });
      }
    }, this.reconnectDelay);
  }

  // Event listeners
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);

    // Return unsubscribe function
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).delete(callback);
      if (this.listeners.get(eventType).size === 0) {
        this.listeners.delete(eventType);
      }
    }
  }

  // Connection status management
  _setStatus(status) {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      this.statusListeners.forEach(listener => {
        try {
          listener(status);
        } catch (error) {
          console.error('Error in status listener:', error);
        }
      });
    }
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
    // Immediately call with current status
    callback(this.connectionStatus);

    // Return unsubscribe function
    return () => this.statusListeners.delete(callback);
  }

  getStatus() {
    return this.connectionStatus;
  }

  isConnected() {
    return this.connectionStatus === 'connected';
  }

  // Send message (if needed for future features)
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    console.warn('WebSocket not connected, message not sent:', data);
    return false;
  }
}

// Create a singleton instance
export const webSocketService = new WebSocketService();

// Auto-connect when token is available
const initializeWebSocket = () => {
  const token = getToken();
  if (token) {
    webSocketService.connect().catch(error => {
      console.error('Failed to initialize WebSocket connection:', error);
    });
  }
};

// Initialize on module load if token exists
initializeWebSocket();

export default webSocketService;