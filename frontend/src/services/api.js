import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'auth_token';

export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token) => {
  localStorage.setItem(TOKEN_KEY, token);
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

export const removeToken = () => {
  localStorage.removeItem(TOKEN_KEY);
  delete api.defaults.headers.common['Authorization'];
};

// Initialize token from localStorage on app start
const existingToken = getToken();
if (existingToken) {
  api.defaults.headers.common['Authorization'] = `Bearer ${existingToken}`;
}

// Request interceptor for token injection
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only redirect to login if we're not already on auth pages
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        removeToken();
        window.location.href = '/login';
      }
      // If we're on login/register pages, don't redirect (let the component handle the error)
    }
    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  },

  register: async (username, email, password, role = 'user') => {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
      role,
    });
    return response.data;
  },

  logout: () => {
    removeToken();
    return Promise.resolve();
  },
};

// Tasks API endpoints
export const tasksAPI = {
  getTasks: async (skip = 0, limit = 100) => {
    const response = await api.get(`/tasks/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getTask: async (taskId) => {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  createTask: async (taskData) => {
    const response = await api.post('/tasks/', taskData);
    return response.data;
  },

  updateTask: async (taskId, taskData) => {
    const response = await api.put(`/tasks/${taskId}`, taskData);
    return response.data;
  },

  deleteTask: async (taskId) => {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  },

  getTaskStats: async () => {
    const response = await api.get('/tasks/stats/count');
    return response.data;
  },

  // File attachment endpoints
  uploadFile: async (taskId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/tasks/${taskId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getTaskAttachments: async (taskId) => {
    const response = await api.get(`/tasks/${taskId}/attachments`);
    return response.data;
  },

  deleteAttachment: async (attachmentId) => {
    const response = await api.delete(`/tasks/attachments/${attachmentId}`);
    return response.data;
  },
};

// External API endpoints
export const externalAPI = {
  getQuote: async (useFallback = true) => {
    const response = await api.get(`/external/quote?use_fallback=${useFallback}`);
    return response.data;
  },

  getDetailedQuote: async () => {
    const response = await api.get('/external/quote/detailed');
    return response.data;
  },

  getAPIHealth: async () => {
    const response = await api.get('/external/quote/health');
    return response.data;
  },
};

// WebSocket connection helper
export const createWebSocketConnection = (token) => {
  const wsURL = API_BASE_URL.replace('http', 'ws') + `/ws/tasks?token=${token}`;
  return new WebSocket(wsURL);
};

export default api;