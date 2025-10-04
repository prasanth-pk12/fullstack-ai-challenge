import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Mock the auth API
jest.mock('../services/api', () => ({
  authAPI: {
    register: jest.fn(),
    login: jest.fn(),
    getProfile: jest.fn(),
  },
  setToken: jest.fn(),
  removeToken: jest.fn(),
  getToken: jest.fn(),
}));

// Import the mocked API functions
const { authAPI, setToken, removeToken, getToken } = require('../services/api');

// Test component to access auth context
const TestComponent = () => {
  const { user, login, register, logout, isAuthenticated } = useAuth();
  
  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="user-info">
        {user ? JSON.stringify(user) : 'no-user'}
      </div>
      <button 
        data-testid="login-btn" 
        onClick={() => login('test@example.com', 'password123')}
      >
        Login
      </button>
      <button 
        data-testid="register-btn" 
        onClick={() => register('testuser', 'test@example.com', 'password123', 'user')}
      >
        Register
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('AuthContext - Token Management and Authentication Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  const renderTestComponent = () => {
    return render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );
  };

  describe('Authentication State Management', () => {
    test('should initialize with unauthenticated state', () => {
      getToken.mockReturnValue(null);
      
      renderTestComponent();
      
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-info')).toHaveTextContent('no-user');
    });

    test('should authenticate user on successful login', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      authAPI.login.mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        user: mockUser
      });

      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      const loginBtn = screen.getByTestId('login-btn');
      await user.click(loginBtn);

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalledWith('test@example.com', 'password123');
      });

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('test-token');
      });

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      await waitFor(() => {
        expect(screen.getByTestId('user-info')).toHaveTextContent(JSON.stringify(mockUser));
      });
    });

    test('should handle login errors gracefully', async () => {
      const user = userEvent.setup();

      authAPI.login.mockRejectedValue({
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      });

      renderTestComponent();

      const loginBtn = screen.getByTestId('login-btn');
      await user.click(loginBtn);

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalled();
      });

      // Should remain unauthenticated on error
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(setToken).not.toHaveBeenCalled();
    });
  });

  describe('Registration Flow with Auto-Login', () => {
    test('should register user and auto-login successfully', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      // Mock successful registration
      authAPI.register.mockResolvedValue({
        message: 'User registered successfully',
        user: mockUser
      });

      // Mock successful auto-login
      authAPI.login.mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        user: mockUser
      });

      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      const registerBtn = screen.getByTestId('register-btn');
      await user.click(registerBtn);

      await waitFor(() => {
        expect(authAPI.register).toHaveBeenCalledWith({
          username: 'testuser',
          email: 'test@example.com',
          password: 'password123',
          role: 'user'
        });
      });

      // Should attempt auto-login after registration
      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalledWith('test@example.com', 'password123');
      });

      await waitFor(() => {
        expect(setToken).toHaveBeenCalledWith('test-token');
      });

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });
    });

    test('should handle registration success but auto-login failure', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      // Mock successful registration
      authAPI.register.mockResolvedValue({
        message: 'User registered successfully',
        user: mockUser
      });

      // Mock failed auto-login
      authAPI.login.mockRejectedValue({
        response: {
          status: 401,
          data: { detail: 'User not found' }
        }
      });

      renderTestComponent();

      const registerBtn = screen.getByTestId('register-btn');
      await user.click(registerBtn);

      await waitFor(() => {
        expect(authAPI.register).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalled();
      });

      // Should remain unauthenticated but registration should be successful
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(setToken).not.toHaveBeenCalled();
    });

    test('should handle registration errors', async () => {
      const user = userEvent.setup();

      authAPI.register.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'Email already exists' }
        }
      });

      renderTestComponent();

      const registerBtn = screen.getByTestId('register-btn');
      await user.click(registerBtn);

      await waitFor(() => {
        expect(authAPI.register).toHaveBeenCalled();
      });

      // Should not attempt auto-login on registration failure
      expect(authAPI.login).not.toHaveBeenCalled();
      expect(setToken).not.toHaveBeenCalled();
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });
  });

  describe('Token Management', () => {
    test('should logout user and clear token', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      // Setup authenticated user
      getToken.mockReturnValue('existing-token');
      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      // Wait for initial authentication check
      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      const logoutBtn = screen.getByTestId('logout-btn');
      await user.click(logoutBtn);

      await waitFor(() => {
        expect(removeToken).toHaveBeenCalled();
      });

      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
      expect(screen.getByTestId('user-info')).toHaveTextContent('no-user');
    });

    test('should load user profile from existing token on init', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      getToken.mockReturnValue('existing-token');
      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      await waitFor(() => {
        expect(authAPI.getProfile).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      });

      await waitFor(() => {
        expect(screen.getByTestId('user-info')).toHaveTextContent(JSON.stringify(mockUser));
      });
    });

    test('should handle invalid token by clearing it', async () => {
      getToken.mockReturnValue('invalid-token');
      authAPI.getProfile.mockRejectedValue({
        response: { status: 401 }
      });

      renderTestComponent();

      await waitFor(() => {
        expect(authAPI.getProfile).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(removeToken).toHaveBeenCalled();
      });

      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });
  });

  describe('Timing and Race Conditions', () => {
    test('should handle rapid login/logout operations', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      authAPI.login.mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        user: mockUser
      });

      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      const loginBtn = screen.getByTestId('login-btn');
      const logoutBtn = screen.getByTestId('logout-btn');

      // Rapid login/logout
      await user.click(loginBtn);
      await user.click(logoutBtn);

      await waitFor(() => {
        expect(removeToken).toHaveBeenCalled();
      });

      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    test('should handle registration with timing delay for auto-login', async () => {
      const user = userEvent.setup();
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user'
      };

      // Mock registration with delay
      authAPI.register.mockImplementation(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            message: 'User registered successfully',
            user: mockUser
          }), 50)
        )
      );

      // Mock login with additional delay to simulate timing issues
      authAPI.login.mockImplementation(() =>
        new Promise(resolve =>
          setTimeout(() => resolve({
            access_token: 'test-token',
            token_type: 'bearer',
            user: mockUser
          }), 150) // Includes the 100ms delay from AuthContext
        )
      );

      authAPI.getProfile.mockResolvedValue(mockUser);

      renderTestComponent();

      const registerBtn = screen.getByTestId('register-btn');
      await user.click(registerBtn);

      // Should eventually authenticate after timing delay
      await waitFor(
        () => {
          expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
        },
        { timeout: 3000 }
      );
    });
  });
});