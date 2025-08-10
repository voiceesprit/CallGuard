// Content script for CallGuard extension
// This script runs in the context of web pages and enables communication
// between the webpage and the extension background script

(function() {
  'use strict';

  console.log('CallGuard content script loaded');

  // Listen for messages from the webpage
  window.addEventListener('message', function(event) {
    // Only accept messages from the same window
    if (event.source !== window) return;

    // Only accept messages that we know are ours
    if (event.data.type && event.data.type.startsWith('CALLGUARD_')) {
      console.log('CallGuard content script received message:', event.data);
      
      // Forward message to background script
      chrome.runtime.sendMessage({
        type: 'content_message',
        data: event.data,
        url: window.location.href,
        timestamp: Date.now()
      }).catch(error => {
        console.warn('Failed to send message to background script:', error);
      });
    }
  });

  // Listen for messages from the extension background script
  chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
    if (message.type === 'inject_script') {
      // Inject a script into the page context
      const script = document.createElement('script');
      script.textContent = message.script;
      (document.head || document.documentElement).appendChild(script);
      script.remove();
      sendResponse({ success: true });
    } else if (message.type === 'page_action') {
      // Perform actions on the page
      switch (message.action) {
        case 'highlight_suspicious_elements':
          highlightSuspiciousElements();
          break;
        case 'show_risk_indicator':
          showRiskIndicator(message.riskLevel);
          break;
        case 'inject_warning':
          injectWarning(message.warningText);
          break;
        default:
          console.log('Unknown page action:', message.action);
      }
      sendResponse({ success: true });
    }
  });

  // Function to highlight potentially suspicious elements on the page
  function highlightSuspiciousElements() {
    const suspiciousSelectors = [
      'input[type="password"]',
      'input[name*="ssn"]',
      'input[name*="social"]',
      'input[name*="credit"]',
      'input[name*="card"]',
      'input[name*="account"]',
      'input[name*="routing"]',
      'input[name*="bank"]'
    ];

    suspiciousSelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        element.style.border = '2px solid #ff6b6b';
        element.style.backgroundColor = '#fff5f5';
        
        // Add warning tooltip
        element.title = '⚠️ Sensitive information field - be cautious';
        
        // Add event listener for focus
        element.addEventListener('focus', function() {
          this.style.border = '2px solid #ff4757';
          this.style.boxShadow = '0 0 10px rgba(255, 71, 87, 0.3)';
        });
        
        element.addEventListener('blur', function() {
          this.style.border = '2px solid #ff6b6b';
          this.style.boxShadow = 'none';
        });
      });
    });
  }

  // Function to show risk indicator on the page
  function showRiskIndicator(riskLevel) {
    // Remove existing indicator if present
    const existingIndicator = document.getElementById('callguard-risk-indicator');
    if (existingIndicator) {
      existingIndicator.remove();
    }

    const indicator = document.createElement('div');
    indicator.id = 'callguard-risk-indicator';
    indicator.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      color: white;
      font-family: Arial, sans-serif;
      font-weight: bold;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transition: all 0.3s ease;
    `;

    // Set color based on risk level
    switch (riskLevel) {
      case 'high':
        indicator.style.backgroundColor = '#e74c3c';
        indicator.innerHTML = '🚨 HIGH RISK CALL DETECTED';
        break;
      case 'medium':
        indicator.style.backgroundColor = '#f39c12';
        indicator.innerHTML = '⚠️ MEDIUM RISK CALL DETECTED';
        break;
      case 'low':
        indicator.style.backgroundColor = '#27ae60';
        indicator.innerHTML = '✅ LOW RISK CALL DETECTED';
        break;
      default:
        indicator.style.backgroundColor = '#3498db';
        indicator.innerHTML = 'ℹ️ CALL MONITORING ACTIVE';
    }

    document.body.appendChild(indicator);

    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (indicator.parentNode) {
        indicator.style.opacity = '0';
        setTimeout(() => indicator.remove(), 300);
      }
    }, 10000);
  }

  // Function to inject warning message into the page
  function injectWarning(warningText) {
    const warning = document.createElement('div');
    warning.id = 'callguard-warning';
    warning.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: linear-gradient(135deg, #ff6b6b, #ee5a24);
      color: white;
      padding: 30px;
      border-radius: 15px;
      font-family: Arial, sans-serif;
      font-size: 18px;
      text-align: center;
      z-index: 10001;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      max-width: 400px;
      animation: callguardPulse 2s infinite;
    `;

    warning.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 20px;">🚨</div>
      <div style="font-weight: bold; margin-bottom: 15px;">CALLGUARD WARNING</div>
      <div>${warningText}</div>
      <button onclick="this.parentElement.remove()" style="
        margin-top: 20px;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        background: white;
        color: #ff6b6b;
        cursor: pointer;
        font-weight: bold;
      ">Dismiss</button>
    `;

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes callguardPulse {
        0% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.05); }
        100% { transform: translate(-50%, -50%) scale(1); }
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(warning);

    // Auto-hide after 30 seconds
    setTimeout(() => {
      if (warning.parentNode) {
        warning.remove();
      }
    }, 30000);
  }

  // Inject a script to enable webpage-to-extension communication
  const script = document.createElement('script');
  script.textContent = `
    // CallGuard webpage integration script
    window.CallGuard = {
      // Send message to extension
      sendMessage: function(type, data) {
        window.postMessage({
          type: 'CALLGUARD_' + type.toUpperCase(),
          data: data,
          timestamp: Date.now()
        }, '*');
      },

      // Request protection status
      getProtectionStatus: function() {
        window.postMessage({
          type: 'CALLGUARD_GET_STATUS',
          timestamp: Date.now()
        }, '*');
      },

      // Report suspicious activity
      reportSuspiciousActivity: function(activity) {
        window.postMessage({
          type: 'CALLGUARD_REPORT_ACTIVITY',
          data: activity,
          timestamp: Date.now()
        }, '*');
      },

      // Check if extension is active
      isActive: function() {
        return window.CallGuard._active || false;
      }
    };

    // Listen for extension responses
    window.addEventListener('message', function(event) {
      if (event.source !== window) return;
      
      if (event.data.type && event.data.type.startsWith('CALLGUARD_RESPONSE_')) {
        // Handle extension responses
        if (window.CallGuard._callbacks && window.CallGuard._callbacks[event.data.type]) {
          window.CallGuard._callbacks[event.data.type](event.data.data);
        }
      }
    });

    // Set up callback system
    window.CallGuard._callbacks = {};
    window.CallGuard.on = function(event, callback) {
      window.CallGuard._callbacks['CALLGUARD_RESPONSE_' + event.toUpperCase()] = callback;
    };

    console.log('CallGuard webpage integration loaded');
  `;

  (document.head || document.documentElement).appendChild(script);
  script.remove();

  // Notify background script that content script is loaded
  chrome.runtime.sendMessage({
    type: 'content_script_loaded',
    url: window.location.href,
    timestamp: Date.now()
  }).catch(() => {
    // Background script might not be ready yet
  });

})(); 