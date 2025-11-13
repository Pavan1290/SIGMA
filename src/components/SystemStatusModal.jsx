import React, { useState, useEffect } from 'react';
import './SystemStatusModal.css';

/**
 * System Status Modal - Clickable modal showing real-time system metrics
 * Opens from header button, displays live stats, daily reset tracking
 */
const SystemStatusModal = ({ isOpen, onClose, selectedModels = {}, isConnected = false }) => {
  const [systemData, setSystemData] = useState({
    thinking_model: selectedModels.thinking || 'Not Selected',
    execution_model: selectedModels.execution || 'Not Selected',
    uptime: '0:00:00',
    requests_processed: 0,
    avg_response_time: 0,
    success_rate: 100,
    memory_usage: 0,
    error_count: 0,
    daily_reset: new Date().toDateString()
  });

  const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

  // Real-time uptime counter
  useEffect(() => {
    if (!isOpen) return;

    const sessionStart = Date.now();
    const updateUptime = () => {
      const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
      const hours = Math.floor(elapsed / 3600);
      const minutes = Math.floor((elapsed % 3600) / 60);
      const seconds = elapsed % 60;

      setSystemData(prev => ({
        ...prev,
        uptime: `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      }));
    };

    const interval = setInterval(updateUptime, 1000);
    return () => clearInterval(interval);
  }, [isOpen]);

  // Fetch system stats periodically
  useEffect(() => {
    if (!isOpen) return;

    const fetchStats = async () => {
      try {
        const response = await fetch(`${BACKEND_HTTP}/system/stats`);
        if (response.ok) {
          const data = await response.json();
          setSystemData(prev => ({
            ...prev,
            ...data,
            thinking_model: selectedModels.thinking || prev.thinking_model,
            execution_model: selectedModels.execution || prev.execution_model
          }));
        }
      } catch (err) {
        // Silently handle - use cached data
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 2000); // Update every 2 seconds while modal open
    return () => clearInterval(interval);
  }, [isOpen, selectedModels, BACKEND_HTTP]);

  if (!isOpen) return null;

  return (
    <div className="status-modal-overlay" onClick={onClose}>
      <div className="status-modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="status-modal-header">
          <h2 className="status-modal-title">System Status</h2>
          <button className="status-modal-close" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6L18 18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="status-modal-body">
          {/* Connection Status */}
          <div className="status-section">
            <div className="section-header">
              <h3>Connection Status</h3>
              <div className="connection-badge">
                <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
                <span className="connection-text">{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
            </div>
          </div>

          {/* Active Models */}
          <div className="status-section">
            <h3>Active Models</h3>
            <div className="models-grid">
              <div className="model-box">
                <div className="model-label">Thinking Model</div>
                <div className="model-name">{systemData.thinking_model}</div>
              </div>
              <div className="model-box">
                <div className="model-label">Execution Model</div>
                <div className="model-name">{systemData.execution_model}</div>
              </div>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="status-section">
            <h3>System Metrics</h3>
            <div className="metrics-grid">
              <div className="metric">
                <div className="metric-label">Uptime</div>
                <div className="metric-value">{systemData.uptime}</div>
              </div>
              <div className="metric">
                <div className="metric-label">Requests</div>
                <div className="metric-value">{systemData.requests_processed}</div>
              </div>
              <div className="metric">
                <div className="metric-label">Avg Response</div>
                <div className="metric-value">{systemData.avg_response_time.toFixed(0)}ms</div>
              </div>
              <div className="metric">
                <div className="metric-label">Success Rate</div>
                <div className="metric-value">{(systemData.success_rate || 0).toFixed(0)}%</div>
              </div>
              <div className="metric">
                <div className="metric-label">Memory</div>
                <div className="metric-value">{(systemData.memory_usage || 0).toFixed(0)}MB</div>
              </div>
              <div className="metric">
                <div className="metric-label">Errors (Today)</div>
                <div className="metric-value error-count">{systemData.error_count}</div>
              </div>
            </div>
          </div>

          {/* Performance Bar */}
          <div className="status-section">
            <h3>Performance Health</h3>
            <div className="health-container">
              <div className="health-bar">
                <div 
                  className="health-fill"
                  style={{ width: `${Math.min(systemData.success_rate, 100)}%` }}
                ></div>
              </div>
              <div className="health-info">
                <span className="health-status">
                  {systemData.success_rate >= 95 ? '✓ Excellent' : 
                   systemData.success_rate >= 85 ? '✓ Good' : 
                   systemData.success_rate >= 70 ? '⚠ Fair' : '✗ Poor'}
                </span>
                <span className="health-percent">{(systemData.success_rate || 0).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Daily Reset Info */}
          <div className="status-section info-section">
            <div className="reset-info">
              <span className="info-label">📅 Daily Reset:</span>
              <span className="reset-date">{systemData.daily_reset}</span>
            </div>
            <div className="info-text">
              Metrics reset daily at midnight. Uptime continues from session start.
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="status-modal-footer">
          <button className="btn-close" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default SystemStatusModal;
