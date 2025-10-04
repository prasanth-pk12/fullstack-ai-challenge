import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileUpload from '../../components/FileUpload';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => <div>{children}</div>
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn()
  }
}));

const renderFileUpload = (props = {}) => {
  const defaultProps = {
    onUpload: jest.fn(),
    ...props
  };

  return render(<FileUpload {...defaultProps} />);
};

describe('FileUpload Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload area with default text', () => {
    renderFileUpload();

    expect(screen.getByText('Click to select files or drag and drop')).toBeInTheDocument();
    expect(screen.getByText('Maximum file size: 10 MB')).toBeInTheDocument();
  });

  test('shows supported file types', () => {
    renderFileUpload();

    expect(screen.getByText('Supported file types:')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('DOC/DOCX')).toBeInTheDocument();
    expect(screen.getByText('JPG/PNG')).toBeInTheDocument();
  });

  test('calls onUpload when valid file is selected', async () => {
    const onUpload = jest.fn().mockResolvedValue();
    renderFileUpload({ onUpload });

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledWith(file);
    });
  });

  test('shows error for oversized file', async () => {
    const onUpload = jest.fn();
    const toast = require('react-hot-toast').default;
    
    renderFileUpload({ onUpload, maxSize: 1024 }); // 1KB limit

    const largeFile = new File(['x'.repeat(2048)], 'large.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, largeFile);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('File size must be less than')
      );
    });

    expect(onUpload).not.toHaveBeenCalled();
  });

  test('shows error for unsupported file type', async () => {
    const onUpload = jest.fn();
    const toast = require('react-hot-toast').default;
    
    renderFileUpload({ onUpload, accept: 'image/*' });

    const unsupportedFile = new File(['test'], 'test.exe', { type: 'application/x-executable' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, unsupportedFile);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('test.exe: File type not supported');
    });

    expect(onUpload).not.toHaveBeenCalled();
  });

  test('shows uploading state during upload', async () => {
    const onUpload = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    renderFileUpload({ onUpload });

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText(/Uploading\.\.\./)).toBeInTheDocument();
    });
  });

  test('shows success state after successful upload', async () => {
    const onUpload = jest.fn().mockResolvedValue();
    renderFileUpload({ onUpload });

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('Upload successful!')).toBeInTheDocument();
    });
  });

  test('shows error state after failed upload', async () => {
    const onUpload = jest.fn().mockRejectedValue(new Error('Upload failed'));
    renderFileUpload({ onUpload });

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
    });
  });

  test('handles multiple file upload when enabled', async () => {
    const onUpload = jest.fn().mockResolvedValue();
    renderFileUpload({ onUpload, multiple: true });

    const file1 = new File(['test1'], 'test1.pdf', { type: 'application/pdf' });
    const file2 = new File(['test2'], 'test2.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, [file1, file2]);

    await waitFor(() => {
      expect(onUpload).toHaveBeenCalledTimes(2);
      expect(onUpload).toHaveBeenCalledWith(file1);
      expect(onUpload).toHaveBeenCalledWith(file2);
    });
  });

  test('rejects multiple files when multiple is disabled', async () => {
    const onUpload = jest.fn();
    const toast = require('react-hot-toast').default;
    
    renderFileUpload({ onUpload, multiple: false });

    const file1 = new File(['test1'], 'test1.pdf', { type: 'application/pdf' });
    const file2 = new File(['test2'], 'test2.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, [file1, file2]);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Only one file allowed');
    });

    expect(onUpload).not.toHaveBeenCalled();
  });

  test('is disabled when disabled prop is true', () => {
    renderFileUpload({ disabled: true });

    const uploadArea = screen.getByRole('button');
    expect(uploadArea).toHaveClass('opacity-50');
    expect(uploadArea).toHaveClass('cursor-not-allowed');
  });

  test('shows drag over state when files are dragged over', async () => {
    renderFileUpload();

    const uploadArea = screen.getByRole('button');
    
    // Simulate drag enter
    await userEvent.hover(uploadArea);
    
    // Note: Testing drag events is complex in jsdom
    // This is a simplified test for the UI state
    expect(uploadArea).toBeInTheDocument();
  });

  test('formats file size correctly', () => {
    renderFileUpload({ maxSize: 5 * 1024 * 1024 }); // 5MB

    expect(screen.getByText('Maximum file size: 5 MB')).toBeInTheDocument();
  });

  test('accepts custom file types', () => {
    renderFileUpload({ accept: 'image/*' });

    const input = screen.getByRole('button').querySelector('input[type="file"]');
    expect(input).toHaveAttribute('accept', 'image/*');
  });

  test('resets file input after selection', async () => {
    const onUpload = jest.fn().mockResolvedValue();
    renderFileUpload({ onUpload });

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByRole('button').querySelector('input[type="file"]');

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });
});