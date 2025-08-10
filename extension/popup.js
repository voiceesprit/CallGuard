// Popup script for CallGuard extension
// Handles user interface interactions and communicates with background script

document.addEventListener('DOMContentLoaded', function() {
  console.log('CallGuard popup loaded');

  // Force popup dimensions
  forcePopupDimensions();

  // Get DOM elements
  const startButton = document.getElementById('start-protection');
  const stopButton = document.getElementById('stop-protection');
  const statusIndicator = document.getElementById('status-indicator');
  const riskScore = document.getElementById('risk-score');
  const riskLevel = document.getElementById('risk-level');
  const connectionStatus = document.getElementById('connection-status');
  const testButton = document.getElementById('test-connection');
  const callDetectionStatus = document.getElementById('call-detection-status');
  const realTimeAnalysisStatus = document.getElementById('real-time-analysis-status');
  const alertsContainer = document.getElementById('alerts-container');
  const sessionInfo = document.getElementById('session-info');
  const protectionToggle = document.getElementById('protection-toggle');

  // State management
  let isProtectionActive = false;
  let currentSession = null;
  let voiceIntensity = 0;

  // Initialize UI
  updateUI();

  // Event listeners
  startButton.addEventListener('click', startProtection);
  stopButton.addEventListener('click', stopProtection);
  testButton.addEventListener('click', testConnection);
  protectionToggle.addEventListener('change', handleProtectionToggle);

  // Handle protection toggle
  function handleProtectionToggle() {
    if (protectionToggle.checked) {
      startProtection();
    } else {
      stopProtection();
    }
  }

  // Simple protection start
  async function startProtection() {
    try {
      // Check if toggle is on
      if (!protectionToggle.checked) {
        console.log('Protection toggle is off, not starting protection');
        return;
      }
      
      console.log('Starting protection...');
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Update status
      updateCallDetectionStatus({ platform: 'Microphone', confidence: 1.0, participants: 1 });
      updateRealTimeAnalysisStatus('Active - Monitoring voice intensity');
      
      // Start session
      currentSession = {
        id: generateSessionId(),
        startTime: Date.now(),
        platform: 'Microphone',
        participants: 1,
        status: 'active'
      };
      
      updateSessionInfo(currentSession);
      
      isProtectionActive = true;
      updateUI();
      
      // Send message to background script
      chrome.runtime.sendMessage({ type: 'start_protection' }, (response) => {
        if (response && response.success) {
          console.log('Protection started successfully');
          showAlert('Protection started! Recording audio and monitoring voice intensity.', 'success');
        }
      });
      
    } catch (error) {
      console.error('Failed to start protection:', error);
      showAlert('Failed to start protection: ' + error.message, 'error');
      // Reset toggle if failed
      protectionToggle.checked = false;
    }
  }

  // Stop protection
  async function stopProtection() {
    try {
      console.log('Stopping protection...');
      
      // Stop recording and monitoring
      chrome.runtime.sendMessage({ type: 'stop_protection' }, (response) => {
        if (response && response.success) {
          console.log('Protection stopped successfully');
        }
      });
      
      // Update UI
      isProtectionActive = false;
      protectionToggle.checked = false;
      updateCallDetectionStatus(null);
      updateRealTimeAnalysisStatus('Inactive');
      updateSessionInfo(null);
      updateUI();
      
      showAlert('Protection stopped.', 'info');
      
    } catch (error) {
      console.error('Failed to stop protection:', error);
      showAlert('Failed to stop protection: ' + error.message, 'error');
    }
  }

  // Test connection to backend
  async function testConnection() {
    try {
      const response = await fetch('http://localhost:5000/test', {
        method: 'GET'
      });
      
      if (response.ok) {
        updateConnectionStatus('Connected');
        showAlert('Backend connection successful!', 'success');
      } else {
        updateConnectionStatus('Disconnected');
        showAlert('Backend connection failed: ' + response.statusText, 'error');
      }
    } catch (error) {
      updateConnectionStatus('Disconnected');
      showAlert('Backend connection failed: ' + error.message, 'error');
    }
  }

  // Update UI functions
  function updateUI() {
    if (isProtectionActive) {
      startButton.disabled = true;
      stopButton.disabled = false;
      statusIndicator.textContent = 'Active';
      statusIndicator.className = 'status-badge status-active';
    } else {
      startButton.disabled = false;
      stopButton.disabled = true;
      statusIndicator.textContent = 'Inactive';
      statusIndicator.className = 'status-badge status-inactive';
    }
  }

  function updateCallDetectionStatus(callContext) {
    if (callContext) {
      callDetectionStatus.innerHTML = `
        <div class="status-item">
          <label>Platform:</label>
          <span class="status-badge status-active">${callContext.platform}</span>
        </div>
        <div class="status-item">
          <label>Confidence:</label>
          <span>${(callContext.confidence * 100).toFixed(0)}%</span>
        </div>
        <div class="status-item">
          <label>Participants:</label>
          <span>${callContext.participants}</span>
        </div>
      `;
    } else {
      callDetectionStatus.innerHTML = '<div class="status-item">No active call detected</div>';
    }
  }

  function updateRealTimeAnalysisStatus(status) {
    realTimeAnalysisStatus.innerHTML = `
      <div class="status-item">
        <label>Status:</label>
        <span class="status-badge ${status.includes('Active') ? 'status-active' : 'status-inactive'}">${status}</span>
      </div>
      <div class="status-item">
        <label>Voice Intensity:</label>
        <span>${voiceIntensity.toFixed(0)}%</span>
      </div>
    `;
  }

  function updateSessionInfo(session) {
    if (session) {
      const duration = Math.floor((Date.now() - session.startTime) / 1000);
      sessionInfo.innerHTML = `
        <div class="status-item">
          <label>Session ID:</label>
          <span>${session.id}</span>
        </div>
        <div class="status-item">
          <label>Duration:</label>
          <span>${duration}s</span>
        </div>
        <div class="status-item">
          <label>Platform:</label>
          <span>${session.platform}</span>
        </div>
      `;
    } else {
      sessionInfo.innerHTML = '<div class="status-item">No active session</div>';
    }
  }

  function updateConnectionStatus(status) {
    connectionStatus.textContent = status;
    connectionStatus.className = `status-badge ${status === 'Connected' ? 'status-connected' : 'status-disconnected'}`;
  }

  function updateRiskScore(score) {
    riskScore.textContent = score;
    
    let level = 'LOW';
    let className = 'risk-low';
    
    if (score >= 80) {
      level = 'CRITICAL';
      className = 'risk-critical';
    } else if (score >= 60) {
      level = 'HIGH';
      className = 'risk-high';
    } else if (score >= 30) {
      level = 'MEDIUM';
      className = 'risk-medium';
    }
    
    riskLevel.textContent = level;
    riskLevel.className = `risk-level ${className}`;
  }

  // Alert functions
  function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `temp-alert temp-alert-${type}`;
    alertDiv.textContent = message;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.parentNode.removeChild(alertDiv);
      }
    }, 5000);
  }

  // Utility functions
  function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Listen for analysis reports from background
  window.addEventListener('analysisReport', (event) => {
    const report = event.detail;
    console.log('Analysis report received:', report);
    
    // Update risk score
    if (report.riskScore) {
      updateRiskScore(report.riskScore);
    }
    
    // Show success alert
    showAlert('Audio analysis complete! Check the report for details.', 'success');
    
    // You can display the full report here if needed
    addAlert({
      type: 'analysis',
      severity: 'low',
      message: 'Audio analysis completed',
      timestamp: Date.now()
    });
  });

  // Add alert to alerts container
  function addAlert(alert) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${alert.severity}`;
    
    const time = new Date(alert.timestamp).toLocaleTimeString();
    
    alertDiv.innerHTML = `
      <div class="alert-header">
        <span class="alert-type">${alert.type.toUpperCase()}</span>
        <span class="alert-severity">${alert.severity}</span>
      </div>
      <div class="alert-message">${alert.message}</div>
      <div class="alert-time">${time}</div>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Remove old alerts if too many
    while (alertsContainer.children.length > 5) {
      alertsContainer.removeChild(alertsContainer.firstChild);
    }
  }

  // Force popup dimensions
  function forcePopupDimensions() {
    document.body.style.width = '500px';
    document.body.style.minWidth = '500px';
    document.body.style.maxWidth = '500px';
  }

  // Initialize connection status
  updateConnectionStatus('Disconnected');
  
  // Test connection on load
  testConnection();
}); 