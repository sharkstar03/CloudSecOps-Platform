/**
 * API client utilities for the CloudSecOps Platform
 */
import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;
    
    // Handle session expiration
    if (response && response.status === 401) {
      // Clear localStorage and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    
    // Handle other errors
    return Promise.reject(error);
  }
);

// API service object with endpoints grouped by resource
const apiService = {
  // Authentication endpoints
  auth: {
    login: (credentials) => api.post('/auth/login', credentials),
    register: (userData) => api.post('/auth/register', userData),
    refreshToken: () => api.post('/auth/refresh-token'),
    forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
    resetPassword: (token, newPassword) => 
      api.post('/auth/reset-password', { token, new_password: newPassword }),
    me: () => api.get('/auth/me'),
  },
  
  // AWS resources endpoints
  aws: {
    getResources: (filters) => api.get('/aws/resources', { params: filters }),
    getSecurityGroups: () => api.get('/aws/security-groups'),
    getIAMUsers: () => api.get('/aws/iam/users'),
    getIAMRoles: () => api.get('/aws/iam/roles'),
    getS3Buckets: () => api.get('/aws/s3/buckets'),
    scanResource: (resourceId, scanType) => 
      api.post(`/aws/resources/${resourceId}/scan`, { scan_type: scanType }),
  },
  
  // Azure resources endpoints
  azure: {
    getResources: (filters) => api.get('/azure/resources', { params: filters }),
    getStorageAccounts: () => api.get('/azure/storage-accounts'),
    getVirtualMachines: () => api.get('/azure/virtual-machines'),
    getKeyVaults: () => api.get('/azure/key-vaults'),
    scanResource: (resourceId, scanType) => 
      api.post(`/azure/resources/${resourceId}/scan`, { scan_type: scanType }),
  },
  
  // Vulnerability management endpoints
  vulnerabilities: {
    getAll: (filters) => api.get('/vulnerabilities', { params: filters }),
    getById: (id) => api.get(`/vulnerabilities/${id}`),
    updateStatus: (id, status) => api.patch(`/vulnerabilities/${id}/status`, { status }),
    getStatistics: () => api.get('/vulnerabilities/statistics'),
  },
  
  // Compliance endpoints
  compliance: {
    getFrameworks: () => api.get('/compliance/frameworks'),
    getControls: (frameworkId) => api.get(`/compliance/frameworks/${frameworkId}/controls`),
    getResults: (filters) => api.get('/compliance/results', { params: filters }),
    runAssessment: (config) => api.post('/compliance/assessments', config),
  },
  
  // Dashboard endpoints
  dashboard: {
    getSummary: () => api.get('/dashboard/summary'),
    getTopVulnerabilities: () => api.get('/dashboard/top-vulnerabilities'),
    getComplianceStatus: () => api.get('/dashboard/compliance-status'),
    getSecurityScore: () => api.get('/dashboard/security-score'),
    getRecentActivity: () => api.get('/dashboard/recent-activity'),
  },
  
  // Settings endpoints
  settings: {
    getNotificationSettings: () => api.get('/settings/notifications'),
    updateNotificationSettings: (settings) => api.put('/settings/notifications', settings),
    getIntegrations: () => api.get('/settings/integrations'),
    updateIntegration: (id, config) => api.put(`/settings/integrations/${id}`, config),
    getScanSettings: () => api.get('/settings/scans'),
    updateScanSettings: (settings) => api.put('/settings/scans', settings),
  },
};

export default apiService;