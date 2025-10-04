import React from 'react';
import { render, screen } from '@testing-library/react';
import Register from '../pages/Register';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock the auth context
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    register: jest.fn(),
    isAuthenticated: false,
    isLoading: false,
    error: null,
    clearError: jest.fn(),
  }),
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}));

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  EyeIcon: () => <div>EyeIcon</div>,
  EyeSlashIcon: () => <div>EyeSlashIcon</div>,
}));

describe('Register Component', () => {
  test('renders register form', () => {
    render(<Register />);
    
    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create account' })).toBeInTheDocument();
  });

  test('renders all form fields', () => {
    render(<Register />);
    
    expect(screen.getByTestId('username-input')).toBeInTheDocument();
    expect(screen.getByTestId('email-input')).toBeInTheDocument();
    expect(screen.getByTestId('role-select')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('confirm-password-input')).toBeInTheDocument();
  });

  test('shows link to login page', () => {
    render(<Register />);
    
    const loginLink = screen.getByTestId('login-link');
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });
});