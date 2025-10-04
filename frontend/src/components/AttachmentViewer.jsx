import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  DocumentIcon, 
  TrashIcon,
  EyeIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { tasksAPI } from '../services/api';
import FileUpload from './FileUpload';
import toast from 'react-hot-toast';

const AttachmentViewer = ({ 
  isOpen, 
  onClose, 
  task,
  onAttachmentAdded,
  onAttachmentDeleted
}) => {
  const { user } = useAuth();
  const [attachments, setAttachments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const canUpload = user?.role === 'ADMIN' || task?.owner_id === user?.id;
  const canDelete = user?.role === 'ADMIN' || task?.owner_id === user?.id;

  useEffect(() => {
    const loadAttachments = async () => {
      setIsLoading(true);
      try {
        const data = await tasksAPI.getTaskAttachments(task.id);
        setAttachments(data);
      } catch (error) {
        toast.error('Failed to load attachments');
        console.error('Error loading attachments:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (isOpen && task?.id) {
      loadAttachments();
    }
  }, [isOpen, task?.id]);

  const refreshAttachments = async () => {
    setIsLoading(true);
    try {
      const data = await tasksAPI.getTaskAttachments(task.id);
      setAttachments(data);
    } catch (error) {
      toast.error('Failed to load attachments');
      console.error('Error loading attachments:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    try {
      const result = await tasksAPI.uploadFile(task.id, file);
      await refreshAttachments(); // Refresh the list
      onAttachmentAdded?.(result);
      return result;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (attachmentId) => {
    if (!window.confirm('Are you sure you want to delete this attachment?')) {
      return;
    }

    try {
      await tasksAPI.deleteAttachment(attachmentId);
      await refreshAttachments(); // Refresh the list
      onAttachmentDeleted?.(attachmentId);
      toast.success('Attachment deleted successfully');
    } catch (error) {
      toast.error('Failed to delete attachment');
      console.error('Error deleting attachment:', error);
    }
  };

  const getFileIcon = (contentType) => {
    if (contentType?.startsWith('image/')) {
      return '🖼️';
    } else if (contentType?.includes('pdf')) {
      return '📄';
    } else if (contentType?.includes('word') || contentType?.includes('document')) {
      return '📝';
    } else if (contentType?.includes('excel') || contentType?.includes('spreadsheet')) {
      return '📊';
    } else if (contentType?.includes('powerpoint') || contentType?.includes('presentation')) {
      return '📽️';
    } else if (contentType?.startsWith('audio/')) {
      return '🎵';
    } else if (contentType?.startsWith('video/')) {
      return '🎬';
    } else if (contentType?.includes('zip') || contentType?.includes('archive')) {
      return '📦';
    } else {
      return '📄';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className="flex min-h-full items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="relative w-full max-w-2xl bg-white rounded-xl shadow-xl max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  Task Attachments
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {task?.title}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Upload Section */}
              {canUpload && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">
                    Upload New Attachment
                  </h3>
                  <FileUpload
                    onUpload={handleUpload}
                    disabled={isUploading}
                    maxSize={10 * 1024 * 1024} // 10MB
                  />
                </div>
              )}

              {/* Attachments List */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium text-gray-900">
                    Attachments ({attachments.length})
                  </h3>
                  {isLoading && (
                    <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  )}
                </div>

                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : attachments.length === 0 ? (
                  <div className="text-center py-8">
                    <DocumentIcon className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No attachments yet</p>
                    {canUpload && (
                      <p className="text-sm text-gray-400 mt-1">
                        Upload your first file above
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {attachments.map((attachment) => (
                      <motion.div
                        key={attachment.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <div className="text-2xl">
                            {getFileIcon(attachment.content_type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {attachment.original_filename}
                            </p>
                            <div className="flex items-center space-x-2 text-xs text-gray-500">
                              <span>{formatFileSize(attachment.file_size)}</span>
                              <span>•</span>
                              <span>{formatDate(attachment.uploaded_at)}</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {/* View/Download Button */}
                          <a
                            href={attachment.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                            title="View/Download"
                          >
                            {attachment.content_type?.startsWith('image/') ? (
                              <EyeIcon className="w-4 h-4" />
                            ) : (
                              <ArrowDownTrayIcon className="w-4 h-4" />
                            )}
                          </a>
                          
                          {/* Delete Button */}
                          {canDelete && (
                            <button
                              onClick={() => handleDelete(attachment.id)}
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                              title="Delete attachment"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200">
              <button
                onClick={onClose}
                className="w-full px-4 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </AnimatePresence>
  );
};

export default AttachmentViewer;