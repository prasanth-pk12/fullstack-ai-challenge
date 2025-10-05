import React from 'react';
import { motion } from 'framer-motion';
import { 
  CalendarIcon, 
  ClockIcon, 
  PaperClipIcon, 
  TrashIcon, 
  PencilIcon,
  UserIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleIconSolid } from '@heroicons/react/24/solid';
import { useAuth } from '../contexts/AuthContext';

// Animation variants for real-time updates
const cardVariants = {
  initial: { 
    opacity: 0, 
    scale: 0.95,
    y: 20 
  },
  animate: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: "easeOut"
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    x: -100,
    transition: {
      duration: 0.2,
      ease: "easeIn"
    }
  },
  updated: {
    scale: [1, 1.02, 1],
    boxShadow: [
      '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      '0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
    ],
    transition: {
      duration: 0.6,
      ease: "easeInOut"
    }
  }
};

const TaskCard = ({ 
  task, 
  onEdit, 
  onDelete, 
  onStatusChange, 
  onViewAttachments,
  className = '',
  animateUpdate = false, // Add prop to trigger update animation
  isDeleting = false, // Loading state for delete operation
  isUpdatingStatus = false // Loading state for status updates
}) => {
  const { user } = useAuth();
  
  const canDelete = user?.role === 'admin' || task.owner_id === user?.id;
  const canEdit = user?.role === 'admin' || task.owner_id === user?.id;
  
  const handleStatusChange = async (newStatus) => {
    if (!canEdit || isUpdatingStatus) return;
    await onStatusChange(task.id, newStatus);
  };

  const getStatusBadge = () => {
    const statusConfig = {
      'todo': {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        icon: ClockIcon,
        label: 'To Do'
      },
      'in-progress': {
        bg: 'bg-blue-100',
        text: 'text-blue-800',
        icon: ExclamationTriangleIcon,
        label: 'In Progress'
      },
      'done': {
        bg: 'bg-green-100',
        text: 'text-green-800',
        icon: CheckCircleIconSolid,
        label: 'Done'
      }
    };
    
    const config = statusConfig[task.status] || statusConfig['todo'];
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  const getPriorityColor = () => {
    if (task.due_date) {
      const dueDate = new Date(task.due_date);
      const today = new Date();
      const diffDays = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (diffDays < 0) return 'border-l-red-500';
      if (diffDays <= 3) return 'border-l-yellow-500';
      return 'border-l-green-500';
    }
    return 'border-l-gray-300';
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    
    // Debug: Log the raw date string from backend
    console.log('Raw date from backend:', dateString);
    
    // Handle different date formats from backend
    let date;
    if (dateString.endsWith('Z') || dateString.includes('+')) {
      // ISO string with timezone info - parse as-is
      date = new Date(dateString);
    } else {
      // Assume it's a UTC datetime string without 'Z'
      date = new Date(dateString + (dateString.includes('T') ? 'Z' : ''));
    }
    
    // Debug: Log the parsed date and current time
    console.log('Parsed date:', date);
    console.log('Current local time:', new Date());
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid date:', dateString);
      return 'Invalid Date';
    }
    
    // Format to local time
    const formatted = new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true // Use 12-hour format with AM/PM
    }).format(date);
    
    console.log('Formatted date:', formatted);
    return formatted;
  };

  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

  return (
    <motion.div
      key={`task-${task.id}-${task.updated_at}`}
      variants={cardVariants}
      initial="initial"
      animate={animateUpdate ? "updated" : "animate"}
      exit="exit"
      whileHover={{ y: -2 }}
      layout
      className={`
        bg-white rounded-xl shadow-sm border-l-4 ${getPriorityColor()} 
        hover:shadow-lg transition-all duration-200 p-6 
        ${isOverdue ? 'ring-2 ring-red-100' : ''}
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {task.title}
          </h3>
          {task.description && (
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
              {task.description}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          {getStatusBadge()}
          {canEdit && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onEdit(task)}
                className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Edit task"
              >
                <PencilIcon className="w-4 h-4" />
              </button>
              {canDelete && (
                <button
                  onClick={() => onDelete(task.id)}
                  disabled={isDeleting}
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Delete task"
                >
                  {isDeleting ? (
                    <div className="w-4 h-4 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <TrashIcon className="w-4 h-4" />
                  )}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Status Toggle Buttons */}
      {canEdit && (
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs font-medium text-gray-500">Quick Actions:</span>
          <div className="flex items-center gap-1">
            {['todo', 'in-progress', 'done'].map((status) => (
              <button
                key={status}
                onClick={() => handleStatusChange(status)}
                disabled={isUpdatingStatus || task.status === status}
                className={`
                  px-2 py-1 text-xs rounded-md transition-all duration-200
                  ${task.status === status 
                    ? 'bg-blue-100 text-blue-800 cursor-default' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                  ${isUpdatingStatus ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {isUpdatingStatus ? (
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin" />
                    <span>...</span>
                  </div>
                ) : (
                  status.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-4">
            {task.due_date && (
              <div className={`flex items-center gap-1 ${isOverdue ? 'text-red-600' : ''}`}>
                <CalendarIcon className="w-3 h-3" />
                <span>Due: {formatDate(task.due_date)}</span>
                {isOverdue && <span className="text-red-600 font-medium">(Overdue)</span>}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-1">
            <UserIcon className="w-3 h-3" />
            <span>
              Created by: {task.owner?.username || `User ${task.owner_id}`}
              {task.owner_id === user?.id && ' (You)'}
            </span>
          </div>
        </div>
        
        {/* Attachment Section */}
        {task.attachment && (
          <div className="p-2 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <PaperClipIcon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {task.attachment.original_filename}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(task.attachment.file_size / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>
              <button
                onClick={() => onViewAttachments(task)}
                className="flex-shrink-0 px-2 py-1 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
              >
                View
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Created/Updated timestamps */}
      <div className="flex items-center justify-between text-xs text-gray-400 mt-2 pt-2 border-t border-gray-100">
        <span>Created: {formatDate(task.created_at)}</span>
        {task.updated_at !== task.created_at && (
          <span>Updated: {formatDate(task.updated_at)}</span>
        )}
      </div>
    </motion.div>
  );
};

export default TaskCard;