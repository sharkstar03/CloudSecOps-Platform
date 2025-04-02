import { configureStore } from '@reduxjs/toolkit';
import vulnerabilitiesReducer from './slices/vulnerabilitiesSlice';
import complianceReducer from './slices/complianceSlice';
import awsResourcesReducer from './slices/awsResourcesSlice';
import azureResourcesReducer from './slices/azureResourcesSlice';
import settingsReducer from './slices/settingsSlice';

const store = configureStore({
  reducer: {
    vulnerabilities: vulnerabilitiesReducer,
    compliance: complianceReducer,
    awsResources: awsResourcesReducer,
    azureResources: azureResourcesReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export default store;