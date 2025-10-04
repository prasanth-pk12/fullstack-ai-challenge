import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Register from '../pages/Register';
import { AuthProvider } from '../contexts/AuthContext';

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

describe('Register Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderRegister = () => {
    return render(
      <TestWrapper>
        <Register />
      </TestWrapper>
    );
  };

  describe('Layout and UI Elements', () => {
    test('renders all form elements correctly', () => {
      renderRegister();

      expect(screen.getByText('Create your account')).toBeInTheDocument();
      expect(screen.getByText('Join us and start managing your tasks efficiently')).toBeInTheDocument();
      
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Role')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
      
      expect(screen.getByRole('button', { name: 'Create account' })).toBeInTheDocument();
      expect(screen.getByText('Already have an account?')).toBeInTheDocument();
      expect(screen.getByTestId('login-link')).toHaveAttribute('href', '/login');
    });

    test('renders form with proper ARIA attributes and test IDs', () => {
      renderRegister();

      expect(screen.getByTestId('register-form')).toBeInTheDocument();
      expect(screen.getByTestId('username-input')).toBeInTheDocument();
      expect(screen.getByTestId('email-input')).toBeInTheDocument();
      expect(screen.getByTestId('role-select')).toBeInTheDocument();
      expect(screen.getByTestId('password-input')).toBeInTheDocument();
      expect(screen.getByTestId('confirm-password-input')).toBeInTheDocument();
      expect(screen.getByTestId('submit-button')).toBeInTheDocument();
    });

    test('applies correct CSS classes for responsive design', () => {
      renderRegister();

      const registerForm = screen.getByTestId('register-form');
      expect(registerForm).toBeInTheDocument();

      const usernameInput = screen.getByTestId('username-input');
      expect(usernameInput).toHaveClass('w-full', 'px-3', 'py-2.5', 'text-sm');
    });

    test('password fields have proper right padding to accommodate toggle buttons', () => {
      renderRegister();

      const passwordInput = screen.getByTestId('password-input');
      const confirmPasswordInput = screen.getByTestId('confirm-password-input');

      expect(passwordInput).toHaveClass('pr-10');
      expect(confirmPasswordInput).toHaveClass('pr-10');
    });
  });

  describe('Form Interactions', () => {
    test('allows user to type in all form fields', async () => {
      const user = userEvent.setup();
      renderRegister();

      const usernameInput = screen.getByTestId('username-input');
      const emailInput = screen.getByTestId('email-input');
      const roleSelect = screen.getByTestId('role-select');
      const passwordInput = screen.getByTestId('password-input');
      const confirmPasswordInput = screen.getByTestId('confirm-password-input');

      await user.type(usernameInput, 'testuser');
      await user.type(emailInput, 'test@example.com');
      await user.selectOptions(roleSelect, 'admin');
      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'password123');

      expect(usernameInput).toHaveValue('testuser');
      expect(emailInput).toHaveValue('test@example.com');
      expect(roleSelect).toHaveValue('admin');
      expect(passwordInput).toHaveValue('password123');
      expect(confirmPasswordInput).toHaveValue('password123');
    });

    test('toggles password visibility when toggle buttons are clicked', async () => {
      const user = userEvent.setup();
      renderRegister();

      const passwordInput = screen.getByTestId('password-input');
      const confirmPasswordInput = screen.getByTestId('confirm-password-input');
      const passwordToggle = screen.getByTestId('password-toggle');
      const confirmPasswordToggle = screen.getByTestId('confirm-password-toggle');

      // Initially passwords should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(confirmPasswordInput).toHaveAttribute('type', 'password');

      // Click to show passwords
      await user.click(passwordToggle);
      await user.click(confirmPasswordToggle);

      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(confirmPasswordInput).toHaveAttribute('type', 'text');

      // Click to hide passwords again
      await user.click(passwordToggle);
      await user.click(confirmPasswordToggle);

      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(confirmPasswordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('Form Validation', () => {
    test('shows validation errors for empty required fields', async () => {
      const user = userEvent.setup();
      renderRegister();

      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('username-error')).toHaveTextContent('Username is required');
      });
      
      expect(screen.getByTestId('email-error')).toHaveTextContent('Email is required');
      expect(screen.getByTestId('password-error')).toHaveTextContent('Password is required');
      expect(screen.getByTestId('confirm-password-error')).toHaveTextContent('Please confirm your password');
    });

    test('shows validation error for short username', async () => {
      const user = userEvent.setup();
      renderRegister();

      const usernameInput = screen.getByTestId('username-input');
      const submitButton = screen.getByTestId('submit-button');

      await user.type(usernameInput, 'ab');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('username-error')).toHaveTextContent('Username must be at least 3 characters');
      });
    });

    test('shows validation error for invalid email', async () => {
      const user = userEvent.setup();
      renderRegister();

      const emailInput = screen.getByTestId('email-input');
      const submitButton = screen.getByTestId('submit-button');

      await user.type(emailInput, 'invalid-email');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('email-error')).toHaveTextContent('Please enter a valid email address');
      });
    });

    test('shows validation error for short password', async () => {
      const user = userEvent.setup();
      renderRegister();

      const passwordInput = screen.getByTestId('password-input');
      const submitButton = screen.getByTestId('submit-button');

      await user.type(passwordInput, '123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('password-error')).toHaveTextContent('Password must be at least 6 characters');
      });
    });

    test('shows validation error when passwords do not match', async () => {
      const user = userEvent.setup();
      renderRegister();

      const passwordInput = screen.getByTestId('password-input');
      const confirmPasswordInput = screen.getByTestId('confirm-password-input');
      const submitButton = screen.getByTestId('submit-button');

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'different123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('confirm-password-error')).toHaveTextContent('Passwords do not match');
      });
    });

    test('applies error styling to fields with validation errors', async () => {
      const user = userEvent.setup();
      renderRegister();

      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        const usernameInput = screen.getByTestId('username-input');
        expect(usernameInput).toHaveClass('border-red-300', 'focus:ring-red-500');
      });
    });
  });

  describe('Responsive Design', () => {
    test('uses responsive text sizing classes', () => {
      renderRegister();

      const heading = screen.getByText('Create your account');
      expect(heading).toHaveClass('text-2xl', 'sm:text-3xl');
    });

    test('uses responsive padding classes', () => {
      renderRegister();

      const registerForm = screen.getByTestId('register-form');
      expect(registerForm).toBeInTheDocument();
      expect(registerForm).toHaveClass('space-y-4');
    });

    test('maintains proper spacing between form elements', () => {
      renderRegister();

      const form = screen.getByTestId('register-form');
      expect(form).toHaveClass('space-y-4');
    });
  });

  describe('Accessibility', () => {
    test('all form inputs have proper labels', () => {
      renderRegister();

      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Role')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
    });

    test('submit button is properly identified', () => {
      renderRegister();

      const submitButton = screen.getByRole('button', { name: 'Create account' });
      expect(submitButton).toBeInTheDocument();
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    test('form has proper structure for screen readers', () => {
      renderRegister();

      const form = screen.getByRole('form');
      expect(form).toBeInTheDocument();
    });
  });

  describe('Visual Consistency', () => {
    test('applies consistent styling across all input fields', () => {
      renderRegister();

      const inputs = [
        screen.getByTestId('username-input'),
        screen.getByTestId('email-input'),
        screen.getByTestId('password-input'),
        screen.getByTestId('confirm-password-input'),
      ];

      inputs.forEach(input => {
        expect(input).toHaveClass(
          'appearance-none',
          'relative',
          'block',
          'w-full',
          'px-3',
          'py-2.5',
          'border',
          'rounded-xl',
          'text-sm'
        );
      });
    });

    test('error messages have consistent styling', async () => {
      const user = userEvent.setup();
      renderRegister();

      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      await waitFor(() => {
        const errorMessages = [
          screen.getByTestId('username-error'),
          screen.getByTestId('email-error'),
          screen.getByTestId('password-error'),
          screen.getByTestId('confirm-password-error'),
        ];

        errorMessages.forEach(error => {
          expect(error).toHaveClass('mt-1', 'text-xs', 'text-red-600');
        });
      });
    });
  });
});