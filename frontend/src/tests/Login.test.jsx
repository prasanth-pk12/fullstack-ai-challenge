import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Login from '../pages/Login';
import { AuthProvider } from '../contexts/AuthContext';
import { authAPI, setToken, removeToken, getToken } from '../services/api';

// Mock the auth API
jest.mock('../services/api', () => ({
  authAPI: {
    login: jest.fn(),
    getProfile: jest.fn(),
  },
  setToken: jest.fn(),
  removeToken: jest.fn(),
  getToken: jest.fn(),
}));

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

// Mock react-router-dom navigation
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
      <Toaster />
    </AuthProvider>
  </BrowserRouter>
);

describe('Login Component - Authentication and Redirect Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  const renderLogin = () => {
    return render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );
  };

  const fillLoginForm = async (user, email = 'test@example.com', password = 'password123') => {
    const emailInput = screen.getByTestId('email-input');
    const passwordInput = screen.getByTestId('password-input');

    await user.type(emailInput, email);
    await user.type(passwordInput, password);
  };

  describe('Successful Login and Redirect', () => {
    test('should redirect to /tasks after successful login', async () => {
      const user = userEvent.setup();
      
      // Mock successful login response
      authAPI.login.mockResolvedValue({
        access_token: 'test-jwt-token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          role: 'user'
        }
      });

      authAPI.getProfile.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'user'
      });

      renderLogin();

      await fillLoginForm(user);
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      // Wait for the login process and redirect
      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalledWith('test@example.com', 'password123');
      });

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('test-jwt-token');
      });

      // Check that redirect happens with 500ms delay
      await waitFor(
        () => {
          expect(mockNavigate).toHaveBeenCalledWith('/tasks', { replace: true });
        },
        { timeout: 1000 }
      );
    });

    test('should show loading state during login process', async () => {
      const user = userEvent.setup();
      
      // Mock login with delay to test loading state
      authAPI.login.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            access_token: 'test-jwt-token',
            token_type: 'bearer',
            user: { id: 1, email: 'test@example.com', username: 'testuser', role: 'user' }
          }), 200)
        )
      );

      authAPI.getProfile.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'user'
      });

      renderLogin();

      await fillLoginForm(user);
      
      const submitButton = screen.getByTestId('submit-button');
      
      await user.click(submitButton);

      // Check loading state is shown
      expect(screen.getByTestId('submit-button')).toBeDisabled();
      expect(screen.getByText('Signing in...')).toBeInTheDocument();

      // Wait for completion
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/tasks', { replace: true });
      });
    });

    test('should store JWT token securely in localStorage', async () => {
      const user = userEvent.setup();
      const testToken = 'test-jwt-token-12345';
      
      authAPI.login.mockResolvedValue({
        access_token: testToken,
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com', username: 'testuser', role: 'user' }
      });

      authAPI.getProfile.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'user'
      });

      renderLogin();

      await fillLoginForm(user);
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith(testToken);
      });
    });
  });

  describe('Authentication Error Handling', () => {
    test('should handle invalid credentials gracefully', async () => {
      const user = userEvent.setup();
      
      authAPI.login.mockRejectedValue({
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      });

      renderLogin();

      await fillLoginForm(user, 'wrong@example.com', 'wrongpassword');
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalledWith('wrong@example.com', 'wrongpassword');
      });

      // Should not redirect on error
      expect(mockNavigate).not.toHaveBeenCalled();

      // Should not store token on error
      expect(setToken).not.toHaveBeenCalled();
    });

    test('should handle network errors gracefully', async () => {
      const user = userEvent.setup();
      
      authAPI.login.mockRejectedValue(new Error('Network error'));

      renderLogin();

      await fillLoginForm(user);
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalled();
      });

      // Should not redirect on error
      expect(mockNavigate).not.toHaveBeenCalled();
      expect(setToken).not.toHaveBeenCalled();
    });

    test('should clear loading state after error', async () => {
      const user = userEvent.setup();
      
      authAPI.login.mockRejectedValue({
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      });

      renderLogin();

      await fillLoginForm(user);
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      // Initially should show loading
      expect(submitButton).toBeDisabled();

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalled();
      });

      // After error, should clear loading state
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
      
      expect(screen.queryByText('Signing in...')).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    test('should prevent submission with empty fields', async () => {
      const user = userEvent.setup();
      
      renderLogin();
      
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      // Should not call API with empty fields
      expect(authAPI.login).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    test('should validate email format', async () => {
      const user = userEvent.setup();
      
      renderLogin();

      const emailInput = screen.getByTestId('email-input');
      await user.type(emailInput, 'invalid-email');

      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      // Should not proceed with invalid email
      expect(authAPI.login).not.toHaveBeenCalled();
    });
  });

  describe('Token Management Integration', () => {
    test('should use existing token if user is already authenticated', async () => {
      // Mock existing token
      getToken.mockReturnValue('existing-token');
      
      authAPI.getProfile.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'user'
      });

      renderLogin();

      // Should automatically redirect if already authenticated
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/tasks', { replace: true });
      });
    });

    test('should handle invalid existing token by staying on login page', async () => {
      // Mock invalid token scenario
      getToken.mockReturnValue('invalid-token');
      authAPI.getProfile.mockRejectedValue({ response: { status: 401 } });

      renderLogin();

      // Should clear invalid token and stay on login page
      await waitFor(() => {
        expect(removeToken).toHaveBeenCalled();
      });

      // Should not redirect
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Navigation and UX', () => {
    test('should show register link with correct href', () => {
      renderLogin();
      
      const registerLink = screen.getByTestId('register-link');
      expect(registerLink).toHaveAttribute('href', '/register');
      expect(screen.getByText("Don't have an account?")).toBeInTheDocument();
    });

    test('should toggle password visibility', async () => {
      const user = userEvent.setup();
      
      renderLogin();
      
      const passwordInput = screen.getByTestId('password-input');
      const passwordToggle = screen.getByTestId('password-toggle');

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Click to show password
      await user.click(passwordToggle);
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Click to hide password again
      await user.click(passwordToggle);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    test('should maintain responsive design classes', () => {
      renderLogin();
      
      const form = screen.getByTestId('login-form');
      expect(form).toBeInTheDocument();

      const emailInput = screen.getByTestId('email-input');
      expect(emailInput).toHaveClass('w-full');

      const passwordInput = screen.getByTestId('password-input');
      expect(passwordInput).toHaveClass('w-full');
    });
  });

  describe('Accessibility', () => {
    test('should have proper ARIA labels and roles', () => {
      renderLogin();
      
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    test('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      
      renderLogin();
      
      const emailInput = screen.getByTestId('email-input');
      const passwordInput = screen.getByTestId('password-input');
      const submitButton = screen.getByTestId('submit-button');

      // Tab through form elements
      await user.tab();
      expect(emailInput).toHaveFocus();

      await user.tab();
      expect(passwordInput).toHaveFocus();

      await user.tab();
      expect(submitButton).toHaveFocus();
    });
  });
});