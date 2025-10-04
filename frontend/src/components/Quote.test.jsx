import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Quote from './Quote';
import { externalAPI } from '../services/api';

// Mock the API service
jest.mock('../services/api', () => ({
  externalAPI: {
    getQuote: jest.fn()
  }
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    info: jest.fn(),
    error: jest.fn()
  }
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>
  },
  AnimatePresence: ({ children }) => children
}));

describe('Quote Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading state initially', () => {
    externalAPI.getQuote.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<Quote />);
    
    expect(screen.getByText('Daily Inspiration')).toBeInTheDocument();
    expect(screen.getByText('Loading inspiration...')).toBeInTheDocument();
  });

  test('renders quote successfully', async () => {
    const mockQuote = {
      content: 'Test quote content',
      author: 'Test Author',
      tags: ['motivational', 'test'],
      length: 18,
      source: 'quotable.io',
      fallback_reason: null
    };

    externalAPI.getQuote.mockResolvedValue(mockQuote);

    render(<Quote />);

    await waitFor(() => {
      expect(screen.getByText('"Test quote content"')).toBeInTheDocument();
    });

    expect(screen.getByText('— Test Author')).toBeInTheDocument();
    expect(screen.getByText('#motivational')).toBeInTheDocument();
    expect(screen.getByText('#test')).toBeInTheDocument();
    expect(screen.getByText('API')).toBeInTheDocument();
  });

  test('renders error state on API failure', async () => {
    const mockError = {
      response: {
        data: {
          detail: {
            message: 'API Error'
          }
        }
      }
    };

    externalAPI.getQuote.mockRejectedValue(mockError);

    render(<Quote />);

    await waitFor(() => {
      expect(screen.getByText('Unable to load quote')).toBeInTheDocument();
    });

    expect(screen.getByText('API Error')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  test('refresh button works', async () => {
    const mockQuote = {
      content: 'Test quote',
      author: 'Test Author',
      tags: [],
      length: 10,
      source: 'quotable.io'
    };

    externalAPI.getQuote.mockResolvedValue(mockQuote);

    render(<Quote />);

    await waitFor(() => {
      expect(screen.getByText('"Test quote"')).toBeInTheDocument();
    });

    // Click refresh button
    const refreshButton = screen.getByTitle('Get new quote');
    fireEvent.click(refreshButton);

    // Should call API again
    expect(externalAPI.getQuote).toHaveBeenCalledTimes(2);
  });

  test('handles fallback quotes with notification', async () => {
    const mockQuote = {
      content: 'Fallback quote',
      author: 'Local Author',
      tags: ['fallback'],
      length: 14,
      source: 'fallback',
      fallback_reason: 'External API unavailable'
    };

    externalAPI.getQuote.mockResolvedValue(mockQuote);

    render(<Quote />);

    await waitFor(() => {
      expect(screen.getByText('"Fallback quote"')).toBeInTheDocument();
    });

    expect(screen.getByText('Local')).toBeInTheDocument();
  });

  test('auto-refresh functionality', async () => {
    jest.useFakeTimers();
    
    const mockQuote = {
      content: 'Auto refresh test',
      author: 'Test Author',
      tags: [],
      length: 17,
      source: 'quotable.io'
    };

    externalAPI.getQuote.mockResolvedValue(mockQuote);

    render(<Quote autoRefresh={true} refreshInterval={1000} />);

    await waitFor(() => {
      expect(screen.getByText('"Auto refresh test"')).toBeInTheDocument();
    });

    // Fast-forward time
    jest.advanceTimersByTime(1000);

    // Should call API again due to auto-refresh
    expect(externalAPI.getQuote).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });

  test('displays tags correctly', async () => {
    const mockQuote = {
      content: 'Quote with many tags',
      author: 'Tag Author',
      tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6'],
      length: 19,
      source: 'quotable.io'
    };

    externalAPI.getQuote.mockResolvedValue(mockQuote);

    render(<Quote />);

    await waitFor(() => {
      expect(screen.getByText('#tag1')).toBeInTheDocument();
    });

    expect(screen.getByText('#tag2')).toBeInTheDocument();
    expect(screen.getByText('#tag3')).toBeInTheDocument();
    expect(screen.getByText('#tag4')).toBeInTheDocument();
    expect(screen.getByText('+2 more')).toBeInTheDocument(); // Shows only first 4 tags
  });
});