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
          // Decode user data from existing token
          const tokenPayload = decodeJWTPayload(token);
          if (tokenPayload) {
            const userData = {
              id: tokenPayload.user_id,
              username: tokenPayload.sub,
              role: tokenPayload.role,
              token: token
            };
            
            dispatch({
              type: AUTH_ACTIONS.LOAD_USER_SUCCESS,
              payload: userData,
            });
          } else {
            // Invalid token, remove it
            removeToken();
            dispatch({
              type: AUTH_ACTIONS.LOAD_USER_FAILURE,
              payload: null,
            });
          }
        } catch (error) {
          // Token decoding failed, remove invalid token
          removeToken();
          dispatch({
            type: AUTH_ACTIONS.LOAD_USER_FAILURE,
            payload: null,
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

  // Helper function to decode JWT payload (simple base64 decode)
  const decodeJWTPayload = (token) => {
    try {
      const payload = token.split('.')[1];
      const decoded = atob(payload);
      return JSON.parse(decoded);
    } catch (error) {
      console.error('Failed to decode JWT:', error);
      return null;
    }
  };

  // Login function
  const login = async (username, password) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });
      
      console.log('AuthContext: Attempting login API call'); // Debug log
      const response = await authAPI.login(username, password);
      console.log('AuthContext: Login API success:', response); // Debug log
      
      // Set token in localStorage and axios headers
      setToken(response.access_token);
      
      // Decode user data from JWT token
      const tokenPayload = decodeJWTPayload(response.access_token);
      const userData = {
        id: tokenPayload?.user_id,
        username: tokenPayload?.sub || username,
        role: tokenPayload?.role,
        token: response.access_token
      };
      
      console.log('AuthContext: Decoded user data:', userData); // Debug log
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user: userData,
          token: response.access_token,
        },
      });
      
      console.log('AuthContext: Login successful'); // Debug log
      return { success: true };
    } catch (error) {
      console.log('AuthContext: Login error caught:', error); // Debug log
      console.log('AuthContext: Error response:', error.response?.data); // Debug log
      
      let errorMessage = 'Login failed. Please check your credentials.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      console.log('AuthContext: Final error message:', errorMessage); // Debug log
      
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
      
      // First, register the user
      await authAPI.register(username, email, password, role);
      
      // Small delay to ensure user is properly saved in database
      await new Promise(resolve => setTimeout(resolve, 100));
      
      try {
        // Try to auto-login after successful registration
        const loginResponse = await authAPI.login(username, password);
        setToken(loginResponse.access_token);
        
        // Decode user data from JWT token
        const tokenPayload = decodeJWTPayload(loginResponse.access_token);
        const userData = {
          id: tokenPayload?.user_id,
          username: tokenPayload?.sub || username,
          role: tokenPayload?.role,
          email: email,
          token: loginResponse.access_token
        };
        
        dispatch({
          type: AUTH_ACTIONS.LOGIN_SUCCESS,
          payload: {
            user: userData,
            token: loginResponse.access_token,
          },
        });
        
        return { success: true, message: 'Registration successful! Welcome!', autoLogin: true };
      } catch (loginError) {
        // If auto-login fails, that's okay - registration was still successful
        dispatch({
          type: AUTH_ACTIONS.LOGIN_FAILURE,
          payload: null,
        });
        
        return { 
          success: true, 
          message: 'Registration successful! Please log in with your credentials.', 
          autoLogin: false 
        };
      }
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