import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CloudArrowUpIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { DocumentArrowUpIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

const FileUpload = ({ 
  onUpload, 
  accept = "*", 
  maxSize = 10 * 1024 * 1024, // 10MB
  multiple = false,
  disabled = false,
  className = ""
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, success, error
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',
    'application/rtf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/svg+xml',
    'application/zip',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
    'application/x-tar',
    'application/gzip',
    'audio/mpeg',
    'video/mp4',
    'video/x-msvideo',
    'video/quicktime',
    'video/x-ms-wmv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  ];

  const validateFile = (file) => {
    // Check file size
    if (file.size > maxSize) {
      return `File size must be less than ${formatFileSize(maxSize)}`;
    }

    // Check file type
    if (!allowedTypes.includes(file.type) && accept !== "*") {
      return 'File type not supported';
    }

    return null;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleFiles = async (files) => {
    const fileList = Array.from(files);
    
    // Validate files
    const validationErrors = [];
    const validFiles = [];
    
    fileList.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        validationErrors.push(`${file.name}: ${error}`);
      } else {
        validFiles.push(file);
      }
    });

    if (validationErrors.length > 0) {
      validationErrors.forEach(error => toast.error(error));
      return;
    }

    if (validFiles.length === 0) {
      toast.error('No valid files selected');
      return;
    }

    if (!multiple && validFiles.length > 1) {
      toast.error('Only one file allowed');
      return;
    }

    // Upload files
    setUploadStatus('uploading');
    setUploadProgress(0);

    try {
      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        setUploadProgress(((i + 1) / validFiles.length) * 100);
        
        await onUpload(file);
        toast.success(`${file.name} uploaded successfully`);
      }
      
      setUploadStatus('success');
      setTimeout(() => setUploadStatus('idle'), 2000);
    } catch (error) {
      setUploadStatus('error');
      toast.error(error.message || 'Upload failed');
      setTimeout(() => setUploadStatus('idle'), 3000);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled || uploadStatus === 'uploading') return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFiles(files);
    }
    // Reset input
    e.target.value = '';
  };

  const handleClick = () => {
    if (disabled || uploadStatus === 'uploading') return;
    fileInputRef.current?.click();
  };

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'uploading':
        return <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />;
      case 'success':
        return <CheckCircleIcon className="w-8 h-8 text-green-600" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />;
      default:
        return isDragOver ? 
          <DocumentArrowUpIcon className="w-8 h-8 text-blue-600" /> :
          <CloudArrowUpIcon className="w-8 h-8 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (uploadStatus) {
      case 'uploading':
        return `Uploading... ${Math.round(uploadProgress)}%`;
      case 'success':
        return 'Upload successful!';
      case 'error':
        return 'Upload failed';
      default:
        return isDragOver ? 
          'Drop files here' : 
          'Click to select files or drag and drop';
    }
  };

  const getStatusColor = () => {
    switch (uploadStatus) {
      case 'uploading':
        return 'border-blue-300 bg-blue-50';
      case 'success':
        return 'border-green-300 bg-green-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      default:
        return isDragOver ? 
          'border-blue-400 bg-blue-50' :
          'border-gray-300 bg-gray-50 hover:bg-gray-100';
    }
  };

  return (
    <div className={className}>
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        onChange={handleFileInput}
        className="hidden"
        disabled={disabled || uploadStatus === 'uploading'}
      />
      
      <motion.div
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled && uploadStatus !== 'uploading') {
            setIsDragOver(true);
          }
        }}
        onDragLeave={() => setIsDragOver(false)}
        whileHover={disabled || uploadStatus === 'uploading' ? {} : { scale: 1.02 }}
        whileTap={disabled || uploadStatus === 'uploading' ? {} : { scale: 0.98 }}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer
          ${getStatusColor()}
          ${disabled || uploadStatus === 'uploading' ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <div className="flex flex-col items-center space-y-3">
          {getStatusIcon()}
          
          <div>
            <p className="text-sm font-medium text-gray-900">
              {getStatusText()}
            </p>
            
            {uploadStatus === 'idle' && (
              <>
                <p className="text-xs text-gray-500 mt-1">
                  Supported files: PDF, DOC, DOCX, TXT, MD, Images, Archives, Audio, Video
                </p>
                <p className="text-xs text-gray-500">
                  Maximum file size: {formatFileSize(maxSize)}
                </p>
              </>
            )}
          </div>
        </div>
        
        {/* Progress Bar */}
        <AnimatePresence>
          {uploadStatus === 'uploading' && (
            <motion.div
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              exit={{ opacity: 0 }}
              className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600 rounded-b-xl"
              style={{ transformOrigin: 'left' }}
            />
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* File type hints */}
      <div className="mt-2 text-xs text-gray-500">
        <p className="font-medium mb-1">Supported file types:</p>
        <div className="flex flex-wrap gap-1">
          {['PDF', 'DOC/DOCX', 'TXT', 'MD', 'RTF', 'JPG/PNG', 'ZIP/RAR', 'MP3/MP4', 'XLS/CSV', 'PPT'].map((type) => (
            <span 
              key={type}
              className="px-1.5 py-0.5 bg-gray-100 rounded text-xs"
            >
              {type}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;