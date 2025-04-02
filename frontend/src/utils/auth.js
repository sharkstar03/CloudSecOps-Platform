/**
 * Authentication utilities for the CloudSecOps Platform
 */
import jwtDecode from 'jwt-decode';
import apiService from './api';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

/**
 * Get the stored authentication token
 * @returns {string|null} Authentication token
 */
export const getToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Check if user is authenticated
 * @returns {boolean} True if user is authenticated
 */
export const isAuthenticated = () => {
  const token = getToken();
  if (!token) return false;
  
  try {
    // Check token expiration
    const decoded = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    
    return decoded.exp > currentTime;
  } catch (error) {
    // Invalid token
    return false;
  }
};

/**
 * Get the current authenticated user
 * @returns {object|null} User object
 */
export const getUser = () => {
  const userJson = localStorage.getItem(USER_KEY);
  return userJson ? JSON.parse(userJson) : null;
};

/**
 * Get user roles
 * @returns {Array} Array of role strings
 */
export const getUserRoles = () => {
  const user = getUser();
  return user?.roles || [];
};

/**
 * Check if user has a specific role
 * @param {string} role - Role to check
 * @returns {boolean} True if user has the role
 */
export const hasRole = (role) => {
  const roles = getUserRoles();
  return roles.includes(role);
};

/**
 * Check if user has admin privileges
 * @returns {boolean} True if user is admin
 */
export const isAdmin = () => {
  return hasRole('admin');
};

/**
 * Login user and store authentication data
 * @param {object} credentials - Login credentials
 * @returns {Promise} Login result
 */
export const login = async (credentials) => {
  try {
    const response = await apiService.auth.login(credentials);
    const { token, user } = response.data;
    
    // Store token and user data
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    
    return { success: true, user };
  } catch (error) {
    return { 
      success: false, 
      error: error.response?.data?.message || 'Authentication failed'
    };
  }
};

/**
 * Register a new user
 * @param {object} userData - User registration data
 * @returns {Promise} Registration result
 */
export const register = async (userData) => {
  try {
    const response = await apiService.auth.register(userData);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.message || 'Registration failed'
    };
  }
};

/**
 * Logout current user
 */
export const logout = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  // Redirect to login page
  window.location.href = '/login';
};

/**
 * Refresh the authentication token
 * @returns {Promise} Token refresh result
 */
export const refreshToken = async () => {
  try {
    const response = await apiService.auth.refreshToken();
    const { token } = response.data;
    
    // Update stored token
    localStorage.setItem(TOKEN_KEY, token);
    
    return { success: true, token };
  } catch (error) {
    // If refresh fails, log out the user
    logout();
    return { 
      success: false, 
      error: error.response?.data?.message || 'Token refresh failed'
    };
  }
};

/**
 * Update the stored user data
 * @param {object} userData - Updated user data
 */
export const updateUserData = (userData) => {
  const currentUser = getUser();
  const updatedUser = { ...currentUser, ...userData };
  localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
};

/**
 * Initialize authentication state
 * Should be called when the application starts
 * @returns {Promise} Initialization result
 */
export const initAuth = async () => {
  if (!isAuthenticated()) {
    return { authenticated: false };
  }
  
  try {
    // Get fresh user data
    const response = await apiService.auth.me();
    const userData = response.data;
    
    // Update stored user data
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
    
    return { authenticated: true, user: userData };
  } catch (error) {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshResult = await refreshToken();
      if (refreshResult.success) {
        return initAuth(); // Try again with new token
      }
    }
    // If request fails, assume not authenticated
    logout();
    return { authenticated: false };
  }
};