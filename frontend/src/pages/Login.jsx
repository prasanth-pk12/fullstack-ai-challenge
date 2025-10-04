import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, isLoading, error, clearError } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, from]);

  // Clear errors when component mounts or form data changes
  useEffect(() => {
    if (error) {
      clearError();
    }
  }, [formData, clearError, error]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username.trim() || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const result = await login(formData.username, formData.password);
      
      if (result.success) {
        toast.success('Welcome back!');
        navigate(from, { replace: true });
      } else {
        toast.error(result.error);
      }
    } catch (err) {
      toast.error('An unexpected error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '40px',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <h2 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
          Welcome back
        </h2>
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Username
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px'
              }}
              placeholder="Enter your username"
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  paddingRight: '40px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '16px'
                }}
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                {showPassword ? '👁️' : '🙈'}
              </button>
            </div>
          </div>

          {error && (
            <div style={{
              backgroundColor: '#fee',
              color: '#c33',
              padding: '10px',
              borderRadius: '4px',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '12px',
              backgroundColor: isSubmitting ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer'
            }}
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <p style={{ margin: 0, color: '#666' }}>
              Don't have an account?{' '}
              <Link to="/register" style={{ color: '#007bff', textDecoration: 'none' }}>
                Create one here
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
