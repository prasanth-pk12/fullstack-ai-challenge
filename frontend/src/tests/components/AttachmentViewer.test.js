import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AttachmentViewer from '../../components/AttachmentViewer';
import { tasksAPI } from '../../services/api';

// Mock the API
jest.mock('../../services/api', () => ({
  tasksAPI: {
    getTaskAttachments: jest.fn(),
    deleteAttachment: jest.fn()
  }
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn()
  }
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>
  },
  AnimatePresence: ({ children }) => <div>{children}</div>
}));

const mockAttachments = [
  {
    id: 1,
    filename: 'document.pdf',
    size: 1024000, // 1MB
    url: 'http://localhost:8000/files/document.pdf'
  },
  {
    id: 2,
    filename: 'image.png',
    size: 512000, // 512KB
    url: 'http://localhost:8000/files/image.png'
  },
  {
    id: 3,
    filename: 'very-long-filename-that-should-be-truncated.docx',
    size: 2048000, // 2MB
    url: 'http://localhost:8000/files/very-long-filename-that-should-be-truncated.docx'
  }
];

const defaultProps = {
  taskId: 1,
  isOpen: true,
  onClose: jest.fn()
};

describe('AttachmentViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    tasksAPI.getTaskAttachments.mockResolvedValue(mockAttachments);
  });

  test('renders when open and fetches attachments', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    expect(screen.getByText('Attachments')).toBeInTheDocument();
    expect(tasksAPI.getTaskAttachments).toHaveBeenCalledWith(1);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    expect(screen.getByText('image.png')).toBeInTheDocument();
    expect(screen.getByText('very-long-filename-that-should-be-truncated.docx')).toBeInTheDocument();
  });

  test('does not render when closed', () => {
    render(<AttachmentViewer {...defaultProps} isOpen={false} />);

    expect(screen.queryByText('Attachments')).not.toBeInTheDocument();
    expect(tasksAPI.getTaskAttachments).not.toHaveBeenCalled();
  });

  test('displays file sizes correctly', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('1.0 MB')).toBeInTheDocument();
    });

    expect(screen.getByText('512.0 KB')).toBeInTheDocument();
    expect(screen.getByText('2.0 MB')).toBeInTheDocument();
  });

  test('shows loading state initially', () => {
    render(<AttachmentViewer {...defaultProps} />);

    expect(screen.getByText('Loading attachments...')).toBeInTheDocument();
  });

  test('shows empty state when no attachments', async () => {
    tasksAPI.getTaskAttachments.mockResolvedValue([]);
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('No attachments found')).toBeInTheDocument();
    });

    expect(screen.getByText('This task has no file attachments.')).toBeInTheDocument();
  });

  test('handles API error gracefully', async () => {
    tasksAPI.getTaskAttachments.mockRejectedValue(new Error('API Error'));
    const toast = require('react-hot-toast').default;

    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to load attachments');
    });

    expect(screen.getByText('No attachments found')).toBeInTheDocument();
  });

  test('closes modal when close button is clicked', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    const closeButton = screen.getByTitle('Close');
    await userEvent.click(closeButton);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  test('closes modal when backdrop is clicked', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    // Click outside the modal content by finding the backdrop overlay
    const backdrop = screen.getByTestId('modal-backdrop');
    await userEvent.click(backdrop);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  test('does not close modal when clicking inside modal content', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Click on the modal content
    const modalContent = screen.getByRole('dialog');
    await userEvent.click(modalContent);

    expect(defaultProps.onClose).not.toHaveBeenCalled();
  });

  test('deletes attachment when delete button is clicked', async () => {
    tasksAPI.deleteAttachment.mockResolvedValue();
    const toast = require('react-hot-toast').default;

    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Find and click delete button for first attachment
    const deleteButtons = screen.getAllByTitle('Delete attachment');
    await userEvent.click(deleteButtons[0]);

    expect(tasksAPI.deleteAttachment).toHaveBeenCalledWith(1, 1);
    
    // Verify success toast
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith('Attachment deleted successfully');
    });

    // Verify attachments are reloaded
    expect(tasksAPI.getTaskAttachments).toHaveBeenCalledTimes(2);
  });

  test('handles delete error gracefully', async () => {
    tasksAPI.deleteAttachment.mockRejectedValue(new Error('Delete failed'));
    const toast = require('react-hot-toast').default;

    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByTitle('Delete attachment');
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to delete attachment');
    });
  });

  test('downloads attachment when download button is clicked', async () => {
    // Mock window.open
    const originalOpen = window.open;
    window.open = jest.fn();

    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Find and click download button for first attachment
    const downloadButtons = screen.getAllByTitle('Download');
    await userEvent.click(downloadButtons[0]);

    expect(window.open).toHaveBeenCalledWith(
      'http://localhost:8000/files/document.pdf',
      '_blank'
    );

    // Restore window.open
    window.open = originalOpen;
  });

  test('displays correct file type icons', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Check that different file types are handled
    const attachmentItems = screen.getAllByRole('listitem');
    expect(attachmentItems).toHaveLength(3);

    // Each attachment should have an icon
    expect(screen.getAllByTestId(/file-icon-/)).toHaveLength(3);
  });

  test('truncates long filenames correctly', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('very-long-filename-that-should-be-truncated.docx')).toBeInTheDocument();
    });

    // The filename should be displayed with proper truncation handling
    const longFilename = screen.getByText('very-long-filename-that-should-be-truncated.docx');
    expect(longFilename).toHaveClass('truncate');
  });

  test('formats file sizes correctly for different units', () => {
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1024 * 1024)).toBe('1.0 MB');
    expect(formatFileSize(512 * 1024)).toBe('512.0 KB');
    expect(formatFileSize(2 * 1024 * 1024)).toBe('2.0 MB');
  });

  test('shows attachment count in header', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Attachments (3)')).toBeInTheDocument();
    });
  });

  test('updates attachment count after deletion', async () => {
    tasksAPI.deleteAttachment.mockResolvedValue();
    // After deletion, return fewer attachments
    tasksAPI.getTaskAttachments
      .mockResolvedValueOnce(mockAttachments)
      .mockResolvedValueOnce(mockAttachments.slice(1));

    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Attachments (3)')).toBeInTheDocument();
    });

    // Delete an attachment
    const deleteButtons = screen.getAllByTitle('Delete attachment');
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Attachments (2)')).toBeInTheDocument();
    });
  });

  test('handles keyboard navigation', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Test escape key closes modal
    await userEvent.keyboard('{Escape}');
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  test('maintains focus management', async () => {
    render(<AttachmentViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('document.pdf')).toBeInTheDocument();
    });

    // Modal should be focusable
    const modal = screen.getByRole('dialog');
    expect(modal).toHaveAttribute('tabIndex', '-1');
  });
});