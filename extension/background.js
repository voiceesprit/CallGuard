// Simple background script for CallGuard extension
// This is a temporary version to get the extension working

console.log('CallGuard background script loaded');

// Basic message handling
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message);
  
  switch (message.type) {
    case 'start_protection':
      console.log('Starting protection...');
      sendResponse({ success: true, sessionId: 'test_session_' + Date.now() });
      break;
      
    case 'stop_protection':
      console.log('Stopping protection...');
      sendResponse({ success: true });
      break;
      
    case 'get_status':
      const status = {
        isActive: false,
        isBackendConnected: false,
        sessionId: null,
        currentSession: null,
        config: {
          enabled: false,
          chunkDuration: 3,
          riskThresholds: { low: 30, medium: 60, high: 80 }
        }
      };
      sendResponse(status);
      break;
      
    case 'test_connection':
      sendResponse({ success: false, connected: false, error: 'Backend not implemented yet' });
      break;
      
    case 'content_message':
      console.log('Content script message:', message.data);
      sendResponse({ success: true });
      break;
      
    case 'content_script_loaded':
      console.log('Content script loaded on:', message.url);
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ error: 'Unknown message type' });
  }
  
  return true; // Keep message channel open for async response
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('CallGuard extension installed');
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('CallGuard extension started');
});

// Basic notification support
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: title,
    message: message,
    priority: 1
  });
} 