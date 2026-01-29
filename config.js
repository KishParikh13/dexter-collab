/**
 * Dexter Dashboard Configuration
 */

window.DEXTER_CONFIG = {
  // API Endpoint
  apiEndpoint: 'https://d0kzdquajc.execute-api.us-east-1.amazonaws.com/prod',
  
  // API Key for write operations
  apiKey: 's5D9GeYUFT39s3rPGTcUJ8jjlfQjm9QH57El8sKG',
  
  // Chat History Server (local)
  // Run: node scripts/chat-server.js
  chatServerUrl: 'http://localhost:3847',
  
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
