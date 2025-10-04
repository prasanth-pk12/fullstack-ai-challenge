import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #dee2e6',
        padding: '0 20px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '64px',
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              width: '32px',
              height: '32px',
              backgroundColor: '#007bff',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '16px'
            }}>
              <span style={{ color: 'white', fontSize: '18px' }}>✓</span>
            </div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>Task Manager</h1>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ fontSize: '14px', color: '#666' }}>
              Welcome, <span style={{ fontWeight: '500' }}>{user?.username}</span>
            </div>
            <button
              onClick={handleLogout}
              style={{
                backgroundColor: '#f8f9fa',
                border: '1px solid #dee2e6',
                color: '#495057',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px' }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '32px', fontWeight: 'bold', color: '#212529', marginBottom: '16px' }}>
            Welcome to your Dashboard
          </h2>
          <p style={{ fontSize: '18px', color: '#6c757d', marginBottom: '32px' }}>
            Your task management hub is ready. Let's get things done!
          </p>
          
          {/* User Info Card */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            padding: '24px',
            maxWidth: '400px',
            margin: '0 auto 48px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '64px',
                height: '64px',
                backgroundColor: '#e3f2fd',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                  {user?.username?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div style={{ textAlign: 'left' }}>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: '600', color: '#212529' }}>
                  {user?.username}
                </h3>
                <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: '#6c757d' }}>
                  {user?.email}
                </p>
                <p style={{ margin: 0, fontSize: '12px', color: '#007bff', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {user?.role}
                </p>
              </div>
            </div>
          </div>

          {/* Coming Soon */}
          <div style={{
            background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
            borderRadius: '12px',
            padding: '32px'
          }}>
            <h3 style={{ fontSize: '20px', fontWeight: '600', color: '#212529', marginBottom: '8px' }}>
              Task Management Features Coming Soon
            </h3>
            <p style={{ margin: 0, color: '#6c757d' }}>
              We're working on bringing you an amazing task management experience.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;