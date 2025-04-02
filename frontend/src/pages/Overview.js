import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Button,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  WarningAmber as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartTooltip, 
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

import { fetchVulnerabilityStatistics } from '../store/slices/vulnerabilitiesSlice';
import { fetchComplianceSummary } from '../store/slices/complianceSlice';

const Overview = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  
  // Redux state
  const vulnerabilityStats = useSelector((state) => state.vulnerabilities.statistics);
  const complianceSummary = useSelector((state) => state.compliance?.summary);
  const vulnLoading = useSelector((state) => state.vulnerabilities.loading);
  const complianceLoading = useSelector((state) => state.compliance?.loading);
  
  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        dispatch(fetchVulnerabilityStatistics()),
        dispatch(fetchComplianceSummary()),
      ]);
      setLoading(false);
    };
    
    loadData();
  }, [dispatch]);
  
  // Handle refresh
  const handleRefresh = () => {
    dispatch(fetchVulnerabilityStatistics());
    dispatch(fetchComplianceSummary());
  };
  
  // Prepare data for charts
  const severityData = vulnerabilityStats ? [
    { name: 'Critical', value: vulnerabilityStats.by_severity.critical || 0, color: '#7f0000' },
    { name: 'High', value: vulnerabilityStats.by_severity.high || 0, color: '#d32f2f' },
    { name: 'Medium', value: vulnerabilityStats.by_severity.medium || 0, color: '#f57c00' },
    { name: 'Low', value: vulnerabilityStats.by_severity.low || 0, color: '#ffb74d' },
    { name: 'Info', value: vulnerabilityStats.by_severity.info || 0, color: '#64b5f6' },
  ] : [];
  
  const statusData = vulnerabilityStats ? [
    { name: 'Open', value: vulnerabilityStats.by_status.open || 0 },
    { name: 'In Progress', value: vulnerabilityStats.by_status.in_progress || 0 },
    { name: 'Resolved', value: vulnerabilityStats.by_status.resolved || 0 },
    { name: 'Accepted Risk', value: vulnerabilityStats.by_status.accepted_risk || 0 },
    { name: 'False Positive', value: vulnerabilityStats.by_status.false_positive || 0 },
  ] : [];
  
  const cloudProviderData = vulnerabilityStats ? [
    { name: 'AWS', value: vulnerabilityStats.by_cloud_provider.aws || 0, color: '#FF9900' },
    { name: 'Azure', value: vulnerabilityStats.by_cloud_provider.azure || 0, color: '#0078D4' },
    { name: 'GCP', value: vulnerabilityStats.by_cloud_provider.gcp || 0, color: '#4285F4' },
    { name: 'Other', value: vulnerabilityStats.by_cloud_provider.other || 0, color: '#757575' },
  ] : [];
  
  // Render loading state
  if (loading || vulnLoading || complianceLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  // Simulate data if not available (for demo/template purposes)
  const simulatedVulnStats = {
    total: 42,
    by_severity: {
      critical: 5,
      high: 12,
      medium: 18,
      low: 5,
      info: 2,
    },
    by_status: {
      open: 28,
      in_progress: 7,
      resolved: 4,
      accepted_risk: 2,
      false_positive: 1,
    },
    by_cloud_provider: {
      aws: 25,
      azure: 15,
      gcp: 0,
      other: 2,
    },
    recent_24h: 8,
  };
  
  const simulatedComplianceSummary = {
    summary: [
      { standard: 'CIS', total_controls: 30, compliant_controls: 24, compliance_percentage: 80 },
      { standard: 'NIST_800-53', total_controls: 45, compliant_controls: 37, compliance_percentage: 82.2 },
      { standard: 'PCI_DSS', total_controls: 20, compliant_controls: 18, compliance_percentage: 90 },
    ],
    overall: {
      total_controls: 95,
      compliant_controls: 79,
      compliance_percentage: 83.2,
    },
  };
  
  // Use real data if available, otherwise use simulated data
  const stats = vulnerabilityStats || simulatedVulnStats;
  const compliance = complianceSummary || simulatedComplianceSummary;
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Security Dashboard
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          variant="outlined"
          onClick={handleRefresh}
        >
          Refresh
        </Button>
      </Box>
      
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#f5f5f5' }}>
            <CardContent sx={{ padding: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Vulnerabilities
              </Typography>
              <Typography variant="h3" sx={{ my: 1 }}>
                {stats.total}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <WarningIcon sx={{ color: 'warning.main', mr: 1 }} />
                <Typography variant="body2">
                  {stats.recent_24h} new in last 24h
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fee8e7' }}>
            <CardContent sx={{ padding: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Critical & High
              </Typography>
              <Typography variant="h3" sx={{ my: 1 }}>
                {(stats.by_severity.critical || 0) + (stats.by_severity.high || 0)}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ErrorIcon sx={{ color: 'error.main', mr: 1 }} />
                <Typography variant="body2">
                  Requires immediate attention
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e3f2fd' }}>
            <CardContent sx={{ padding: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Open Issues
              </Typography>
              <Typography variant="h3" sx={{ my: 1 }}>
                {stats.by_status.open || 0}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <InfoIcon sx={{ color: 'info.main', mr: 1 }} />
                <Typography variant="body2">
                  Awaiting remediation
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e8f5e9' }}>
            <CardContent sx={{ padding: 2 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Compliance Score
              </Typography>
              <Typography variant="h3" sx={{ my: 1 }}>
                {compliance.overall.compliance_percentage.toFixed(1)}%
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircleIcon sx={{ color: 'success.main', mr: 1 }} />
                <Typography variant="body2">
                  Overall compliance
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Charts */}
      <Grid container spacing={3}>
        {/* Vulnerabilities by Severity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Vulnerabilities by Severity
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={[
                  {
                    name: 'Critical',
                    value: stats.by_severity.critical || 0,
                    color: '#7f0000',
                  },
                  {
                    name: 'High',
                    value: stats.by_severity.high || 0,
                    color: '#d32f2f',
                  },
                  {
                    name: 'Medium',
                    value: stats.by_severity.medium || 0,
                    color: '#f57c00',
                  },
                  {
                    name: 'Low',
                    value: stats.by_severity.low || 0,
                    color: '#ffb74d',
                  },
                  {
                    name: 'Info',
                    value: stats.by_severity.info || 0,
                    color: '#64b5f6',
                  },
                ]}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartTooltip />
                <Bar dataKey="value" name="Count">
                  {[
                    { name: 'Critical', color: '#7f0000' },
                    { name: 'High', color: '#d32f2f' },
                    { name: 'Medium', color: '#f57c00' },
                    { name: 'Low', color: '#ffb74d' },
                    { name: 'Info', color: '#64b5f6' },
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Button
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/vulnerabilities')}
              >
                View All Vulnerabilities
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* Cloud Provider Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Cloud Provider Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    {
                      name: 'AWS',
                      value: stats.by_cloud_provider.aws || 0,
                      color: '#FF9900',
                    },
                    {
                      name: 'Azure',
                      value: stats.by_cloud_provider.azure || 0,
                      color: '#0078D4',
                    },
                    {
                      name: 'GCP',
                      value: stats.by_cloud_provider.gcp || 0,
                      color: '#4285F4',
                    },
                    {
                      name: 'Other',
                      value: stats.by_cloud_provider.other || 0,
                      color: '#757575',
                    },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {[
                    { name: 'AWS', color: '#FF9900' },
                    { name: 'Azure', color: '#0078D4' },
                    { name: 'GCP', color: '#4285F4' },
                    { name: 'Other', color: '#757575' },
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartTooltip />
              </PieChart>
            </ResponsiveContainer>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/aws')}
                sx={{ mr: 2 }}
              >
                AWS Resources
              </Button>
              <Button
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/azure')}
              >
                Azure Resources
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* Compliance Standards */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Compliance Standards
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={compliance.summary}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="standard" />
                  <YAxis
                    yAxisId="left"
                    orientation="left"
                    stroke="#8884d8"
                    domain={[0, 100]}
                    label={{ value: 'Compliance %', angle: -90, position: 'insideLeft' }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke="#82ca9d"
                    label={{ value: 'Controls', angle: -90, position: 'insideRight' }}
                  />
                  <RechartTooltip />
                  <Legend />
                  <Bar
                    yAxisId="left"
                    dataKey="compliance_percentage"
                    name="Compliance %"
                    fill="#8884d8"
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="total_controls"
                    name="Total Controls"
                    fill="#82ca9d"
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Button
                endIcon={<ArrowForwardIcon />}
                onClick={() => navigate('/compliance')}
              >
                View Compliance Details
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon color="error" />
                </ListItemIcon>
                <ListItemText
                  primary="Critical vulnerability detected in AWS S3 bucket"
                  secondary="2 hours ago"
                />
                <Button
                  size="small"
                  onClick={() => navigate('/vulnerabilities')}
                >
                  View
                </Button>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <WarningIcon color="warning" />
                </ListItemIcon>
                <ListItemText
                  primary="Azure Storage Account has public access enabled"
                  secondary="5 hours ago"
                />
                <Button
                  size="small"
                  onClick={() => navigate('/vulnerabilities')}
                >
                  View
                </Button>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <CheckCircleIcon color="success" />
                </ListItemIcon>
                <ListItemText
                  primary="AWS EC2 Security Group issue remediated"
                  secondary="Yesterday"
                />
                <Button
                  size="small"
                  onClick={() => navigate('/vulnerabilities')}
                >
                  View
                </Button>
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Overview;