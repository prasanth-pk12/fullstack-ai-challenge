import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI, setToken, removeToken, getToken } from '../services/api';

// Initial state
const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Action types
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  LOAD_USER_START: 'LOAD_USER_START',
  LOAD_USER_SUCCESS: 'LOAD_USER_SUCCESS',
  LOAD_USER_FAILURE: 'LOAD_USER_FAILURE',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case AUTH_ACTIONS.LOAD_USER_START:
      return {
        ...state,
        isLoading: true,
      };
    case AUTH_ACTIONS.LOAD_USER_SUCCESS:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case AUTH_ACTIONS.LOAD_USER_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

// Create context
const AuthContext = createContext();

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth Provider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Load user on app initialization
  useEffect(() => {
    const loadUser = async () => {
      const token = getToken();
      if (token) {
        try {
          dispatch({ type: AUTH_ACTIONS.LOAD_USER_START });
          const userData = await authAPI.getProfile();
          dispatch({
            type: AUTH_ACTIONS.LOAD_USER_SUCCESS,
            payload: userData,
          });
        } catch (error) {
          console.error('Failed to load user:', error);
          removeToken();
          dispatch({
            type: AUTH_ACTIONS.LOAD_USER_FAILURE,
            payload: 'Failed to authenticate user',
          });
        }
      } else {
        dispatch({
          type: AUTH_ACTIONS.LOAD_USER_FAILURE,
          payload: null,
        });
      }
    };

    loadUser();
  }, []);

  // Login function
  const login = async (username, password) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      const response = await authAPI.login(username, password);
      
      // Set token in localStorage and axios headers
      setToken(response.access_token);
      
      // Get user profile
      const userData = await authAPI.getProfile();
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user: userData,
          token: response.access_token,
        },
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.message || 
        'Login failed. Please check your credentials.';
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      
      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      removeToken();
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  // Register function
  const register = async (username, email, password, role = 'user') => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      await authAPI.register(username, email, password, role);
      
      // Auto-login after successful registration
      const loginResponse = await authAPI.login(username, password);
      setToken(loginResponse.access_token);
      
      const userData = await authAPI.getProfile();
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user: userData,
          token: loginResponse.access_token,
        },
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.message || 
        'Registration failed. Please try again.';
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      
      return { success: false, error: errorMessage };
    }
  };

  // Clear error function
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Context value
  const value = {
    ...state,
    login,
    logout,
    register,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;