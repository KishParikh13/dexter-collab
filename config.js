/**
 * Dexter Dashboard Configuration
 * 
 * This file contains API configuration for the dashboard.
 * Do NOT commit API keys to public repos - use environment-specific overrides.
 * 
 * For local development, create config.local.js with your API key:
 * window.DEXTER_CONFIG = { ...window.DEXTER_CONFIG, apiKey: 'your-key' };
 */

window.DEXTER_CONFIG = {
  // API Endpoint - Update after deployment
  // Format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}
  apiEndpoint: '',  // Will be populated after AWS deployment
  
  // API Key for write operations (POST/PUT/DELETE)
  // In production, this should be loaded securely, not hardcoded
  apiKey: '',  // Will be populated after AWS deployment
  
  // Polling interval for session status (ms)
  sessionPollInterval: 5000,
  
  // Polling interval for tasks (ms)
  taskPollInterval: 10000,
  
  // Enable/disable API (set to false to use localStorage only)
  useApi: true,
  
  // Fallback to localStorage if API fails
  fallbackToLocalStorage: true,
  
  // Debug mode
  debug: false
};

// Allow local config override (not committed to repo)
if (typeof window.DEXTER_CONFIG_LOCAL !== 'undefined') {
  window.DEXTER_CONFIG = { ...window.DEXTER_CONFIG, ...window.DEXTER_CONFIG_LOCAL };
}
