import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  WifiIcon, 
  ExclamationTriangleIcon, 
  ArrowPathIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../contexts/AuthContext';

const ConnectionStatus = ({ className = '' }) => {
  const { user } = useAuth();
  const { connectionStatus, reconnect } = useWebSocket();

  // Only show connection status for admin users
  // Regular users don't need WebSocket connections
  if (!user || user.role !== 'admin') {
    return null;
  }

  const getStatusConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: WifiIcon,
          text: 'Connected',
          bgColor: 'bg-green-50',
          textColor: 'text-green-700',
          iconColor: 'text-green-500',
          borderColor: 'border-green-200'
        };
      case 'connecting':
        return {
          icon: ArrowPathIcon,
          text: 'Connecting...',
          bgColor: 'bg-yellow-50',
          textColor: 'text-yellow-700',
          iconColor: 'text-yellow-500',
          borderColor: 'border-yellow-200',
          animate: true
        };
      case 'disconnected':
        return {
          icon: XMarkIcon,
          text: 'Disconnected',
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-700',
          iconColor: 'text-gray-500',
          borderColor: 'border-gray-200'
        };
      case 'error':
        return {
          icon: ExclamationTriangleIcon,
          text: 'Connection Error',
          bgColor: 'bg-red-50',
          textColor: 'text-red-700',
          iconColor: 'text-red-500',
          borderColor: 'border-red-200'
        };
      default:
        return {
          icon: XMarkIcon,
          text: 'Unknown',
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-700',
          iconColor: 'text-gray-500',
          borderColor: 'border-gray-200'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  // Show connection status only when not connected or when there's an issue
  const shouldShow = connectionStatus !== 'connected';

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className={`${className}`}
        >
          <div className={`
            flex items-center justify-between px-4 py-3 rounded-lg border 
            ${config.bgColor} ${config.borderColor}
          `}>
            <div className="flex items-center gap-3">
              <Icon 
                className={`
                  w-5 h-5 ${config.iconColor}
                  ${config.animate ? 'animate-spin' : ''}
                `} 
              />
              <div>
                <p className={`text-sm font-medium ${config.textColor}`}>
                  Real-time Updates: {config.text}
                </p>
                {connectionStatus === 'error' && (
                  <p className="text-xs text-red-600 mt-1">
                    Live updates are temporarily unavailable
                  </p>
                )}
                {connectionStatus === 'disconnected' && (
                  <p className="text-xs text-gray-600 mt-1">
                    Changes will sync when connection is restored
                  </p>
                )}
              </div>
            </div>
            
            {(connectionStatus === 'error' || connectionStatus === 'disconnected') && (
              <button
                onClick={reconnect}
                className={`
                  px-3 py-1 text-xs font-medium rounded-md border transition-colors
                  ${connectionStatus === 'error' 
                    ? 'border-red-300 text-red-700 hover:bg-red-100' 
                    : 'border-gray-300 text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                Retry
              </button>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Compact version for header/navigation areas
export const ConnectionStatusIndicator = ({ className = '' }) => {
  const { connectionStatus } = useWebSocket();

  const getIndicatorConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: 'bg-green-400',
          tooltip: 'Real-time updates active'
        };
      case 'connecting':
        return {
          color: 'bg-yellow-400 animate-pulse',
          tooltip: 'Connecting to real-time updates...'
        };
      case 'disconnected':
        return {
          color: 'bg-gray-400',
          tooltip: 'Real-time updates disconnected'
        };
      case 'error':
        return {
          color: 'bg-red-400',
          tooltip: 'Real-time updates error'
        };
      default:
        return {
          color: 'bg-gray-400',
          tooltip: 'Real-time updates status unknown'
        };
    }
  };

  const config = getIndicatorConfig();

  return (
    <div 
      className={`relative ${className}`}
      title={config.tooltip}
    >
      <div className={`w-3 h-3 rounded-full ${config.color}`} />
      {connectionStatus === 'connecting' && (
        <div className="absolute inset-0 w-3 h-3 rounded-full bg-yellow-400 animate-ping" />
      )}
    </div>
  );
};

export default ConnectionStatus;