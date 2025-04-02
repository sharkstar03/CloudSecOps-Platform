import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Provider } from 'react-redux';
import theme from './theme';
import store from './store';

// Layout
import Dashboard from './layout/Dashboard';

// Pages
import Overview from './pages/Overview';
import VulnerabilitiesList from './pages/vulnerabilities/VulnerabilitiesList';
import VulnerabilityDetails from './pages/vulnerabilities/VulnerabilityDetails';
import ComplianceDashboard from './pages/compliance/ComplianceDashboard';
import ComplianceStandard from './pages/compliance/ComplianceStandard';
import AWSResources from './pages/aws/AWSResources';
import AzureResources from './pages/azure/AzureResources';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';
import Login from './pages/auth/Login';

// Auth context
import { AuthProvider, useAuth } from './context/AuthContext';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const App = () => {
  return (
    <Provider store={store}>
      <AuthProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              
              <Route 
                path="/" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/overview" replace />} />
                <Route path="overview" element={<Overview />} />
                
                <Route path="vulnerabilities">
                  <Route index element={<VulnerabilitiesList />} />
                  <Route path=":vulnerabilityId" element={<VulnerabilityDetails />} />
                </Route>
                
                <Route path="compliance">
                  <Route index element={<ComplianceDashboard />} />
                  <Route path=":standard" element={<ComplianceStandard />} />
                </Route>
                
                <Route path="aws">
                  <Route index element={<AWSResources />} />
                </Route>
                
                <Route path="azure">
                  <Route index element={<AzureResources />} />
                </Route>
                
                <Route path="settings" element={<Settings />} />
              </Route>
              
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Router>
        </ThemeProvider>
      </AuthProvider>
    </Provider>
  );
};

export default App;