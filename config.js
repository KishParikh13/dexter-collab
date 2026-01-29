/**
 * Dexter Dashboard Configuration
 */

window.DEXTER_CONFIG = {
  // API Endpoint
  apiEndpoint: 'https://d0kzdquajc.execute-api.us-east-1.amazonaws.com/prod',
  
  // API Key for write operations
  apiKey: 'Ak5YL5VOFt1xXnABMEygg4MeKRyS1UGs6zVU1M6U',
  
  // Polling intervals (ms)
  sessionPollInterval: 5000,
  taskPollInterval: 10000,
  
  // Enable API
  useApi: true,
  
  // Fallback to localStorage if API fails
  fallbackToLocalStorage: true,
  
  // Debug mode
  debug: false
};
