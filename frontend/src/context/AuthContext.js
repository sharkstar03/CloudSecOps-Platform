import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

// Create the context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        
        if (token) {
          // Set default headers for all axios requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Get user profile
          // In a real app, you would have an API endpoint to get the user profile
          // For this template, we'll simulate it
          
          // Simulated user data - in a real app, this would come from the API
          const userData = {
            id: '1',
            name: 'Admin User',
            email: 'admin@example.com',
            role: 'admin',
          };
          
          setUser(userData);
        }
      } catch (err) {
        console.error('Authentication error:', err);
        setError(err.message);
        // Clear any invalid tokens
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      // In a real app, you would call an API to authenticate
      // For this template, we'll simulate a successful login
      
      // Simulated API response
      const response = {
        token: 'simulated_jwt_token',
        user: {
          id: '1',
          name: 'Admin User',
          email: email,
          role: 'admin',
        },
      };
      
      // Store the token
      localStorage.setItem('token', response.token);
      
      // Set default headers for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.token}`;
      
      // Update state
      setUser(response.user);
      
      return response.user;
    } catch (err) {
      setError(err.message || 'Failed to login');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    // Clear token from storage
    localStorage.removeItem('token');
    
    // Remove default header
    delete axios.defaults.headers.common['Authorization'];
    
    // Clear user from state
    setUser(null);
  };

  // Check if user is authenticated
  const isAuthenticated = !!user;

  // Context value
  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};