import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Async thunks
export const fetchVulnerabilities = createAsyncThunk(
  'vulnerabilities/fetchVulnerabilities',
  async ({
    page = 0,
    limit = 10,
    severity = null,
    status = null,
    cloudProvider = null,
    resourceType = null,
    region = null,
  } = {}, thunkAPI) => {
    try {
      // Build query params
      const params = new URLSearchParams();
      
      // Add pagination
      params.append('offset', page * limit);
      params.append('limit', limit);
      
      // Add filters if provided
      if (severity && severity.length > 0) {
        severity.forEach((s) => params.append('severity', s));
      }
      
      if (status && status.length > 0) {
        status.forEach((s) => params.append('status', s));
      }
      
      if (cloudProvider) {
        params.append('cloud_provider', cloudProvider);
      }
      
      if (resourceType) {
        params.append('resource_type', resourceType);
      }
      
      if (region) {
        params.append('region', region);
      }
      
      const response = await axios.get(`${API_URL}/vulnerabilities/?${params.toString()}`);
      return response.data;
    } catch (error) {
      return thunkAPI.rejectWithValue(error.response.data);
    }
  }
);

export const fetchVulnerabilityById = createAsyncThunk(
  'vulnerabilities/fetchVulnerabilityById',
  async (id, thunkAPI) => {
    try {
      const response = await axios.get(`${API_URL}/vulnerabilities/${id}`);
      return response.data;
    } catch (error) {
      return thunkAPI.rejectWithValue(error.response.data);
    }
  }
);

export const updateVulnerabilityStatus = createAsyncThunk(
  'vulnerabilities/updateVulnerabilityStatus',
  async ({ id, status }, thunkAPI) => {
    try {
      const response = await axios.post(`${API_URL}/vulnerabilities/${id}/status`, {
        status,
      });
      return { id, status, response: response.data };
    } catch (error) {
      return thunkAPI.rejectWithValue(error.response.data);
    }
  }
);

export const fetchVulnerabilityStatistics = createAsyncThunk(
  'vulnerabilities/fetchVulnerabilityStatistics',
  async (_, thunkAPI) => {
    try {
      const response = await axios.get(`${API_URL}/vulnerabilities/statistics/overview`);
      return response.data;
    } catch (error) {
      return thunkAPI.rejectWithValue(error.response.data);
    }
  }
);

// Initial state
const initialState = {
  vulnerabilities: [],
  currentVulnerability: null,
  statistics: null,
  loading: false,
  error: null,
  totalCount: 0,
  filters: {
    severity: [],
    status: [],
    cloudProvider: null,
    resourceType: null,
    region: null,
  },
};

// Slice
const vulnerabilitiesSlice = createSlice({
  name: 'vulnerabilities',
  initialState,
  reducers: {
    setFilters(state, action) {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters(state) {
      state.filters = {
        severity: [],
        status: [],
        cloudProvider: null,
        resourceType: null,
        region: null,
      };
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch vulnerabilities
      .addCase(fetchVulnerabilities.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchVulnerabilities.fulfilled, (state, action) => {
        state.loading = false;
        state.vulnerabilities = action.payload;
        state.totalCount = action.payload.length; // In a real API, this would come from response headers or metadata
      })
      .addCase(fetchVulnerabilities.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch vulnerabilities';
      })
      
      // Fetch vulnerability by ID
      .addCase(fetchVulnerabilityById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchVulnerabilityById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentVulnerability = action.payload;
      })
      .addCase(fetchVulnerabilityById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch vulnerability details';
      })
      
      // Update vulnerability status
      .addCase(updateVulnerabilityStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateVulnerabilityStatus.fulfilled, (state, action) => {
        state.loading = false;
        
        // Update the current vulnerability if it's the one being updated
        if (state.currentVulnerability && state.currentVulnerability.id === action.payload.id) {
          state.currentVulnerability.status = action.payload.status;
        }
        
        // Update in the list
        const index = state.vulnerabilities.findIndex((v) => v.id === action.payload.id);
        if (index !== -1) {
          state.vulnerabilities[index].status = action.payload.status;
        }
      })
      .addCase(updateVulnerabilityStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to update vulnerability status';
      })
      
      // Fetch statistics
      .addCase(fetchVulnerabilityStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchVulnerabilityStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.statistics = action.payload;
      })
      .addCase(fetchVulnerabilityStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload || 'Failed to fetch vulnerability statistics';
      });
  },
});

// Export actions and reducer
export const { setFilters, clearFilters } = vulnerabilitiesSlice.actions;
export default vulnerabilitiesSlice.reducer;

// Selectors
export const selectVulnerabilities = (state) => state.vulnerabilities.vulnerabilities;
export const selectCurrentVulnerability = (state) => state.vulnerabilities.currentVulnerability;
export const selectVulnerabilityStatistics = (state) => state.vulnerabilities.statistics;
export const selectVulnerabilitiesLoading = (state) => state.vulnerabilities.loading;
export const selectVulnerabilitiesError = (state) => state.vulnerabilities.error;
export const selectVulnerabilitiesFilters = (state) => state.vulnerabilities.filters;
export const selectVulnerabilitiesTotalCount = (state) => state.vulnerabilities.totalCount;