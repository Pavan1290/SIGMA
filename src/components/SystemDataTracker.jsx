import React, { useState, useEffect, useRef } from 'react';
import './SystemDataTracker.css';

/**
 * System Data Tracker - Real-time system metrics with daily reset
 * Features: Real-time stats, daily reset at midnight, live connection status
 */
const SystemDataTracker = ({ selectedModels = {}, isConnected = false }) => {
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
  
  const startTimeRef = useRef(Date.now());
  const lastResetRef = useRef(new Date().toDateString());
  
  const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

  // Check if we need to reset daily metrics (every 24 hours or at midnight)
  useEffect(() => {
    const checkDailyReset = () => {
      const today = new Date().toDateString();
      if (lastResetRef.current !== today) {
        lastResetRef.current = today;
        // Reset counters to 0 for new day
        setSystemData(prev => ({
          ...prev,
          requests_processed: 0,
          error_count: 0,
          avg_response_time: 0,
          success_rate: 100,
          daily_reset: today
        }));
      }
    };

    const resetCheckInterval = setInterval(checkDailyReset, 60000); // Check every minute
    return () => clearInterval(resetCheckInterval);
  }, []);

  // Fetch system data periodically (real-time)
  useEffect(() => {
    const fetchSystemData = async () => {
      try {
        const response = await fetch(`${BACKEND_HTTP}/system/stats`);
        if (response.ok) {
          const data = await response.json();
          setSystemData(prev => ({
            ...prev,
            ...data,
            thinking_model: selectedModels.thinking || prev.thinking_model,
            execution_model: selectedModels.execution || prev.execution_model,
            daily_reset: prev.daily_reset
          }));
        }
      } catch (err) {
        // Silently handle errors - use cached data
      }
    };

    fetchSystemData();
    const interval = setInterval(fetchSystemData, 5000); // Update every 5 seconds
    
    return () => clearInterval(interval);
  }, [selectedModels, BACKEND_HTTP]);

  // Calculate uptime in real-time
  useEffect(() => {
    const updateUptime = () => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
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
  }, []);

  return (
    <div className="system-tracker">
      <div className="tracker-header">
        <h3 className="tracker-title">System Status (Real-time)</h3>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span className="status-text">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="tracker-content">
        {/* Active Models Section */}
        <div className="tracker-section">
          <h4 className="section-label">Active Models</h4>
          <div className="models-display">
            <div className="model-card">
              <span className="model-type">Thinking</span>
              <span className="model-value">
                {systemData.thinking_model && systemData.thinking_model !== 'Not Selected' 
                  ? systemData.thinking_model 
                  : 'Not Selected'}
              </span>
            </div>
            <div className="model-card">
              <span className="model-type">Execution</span>
              <span className="model-value">
                {systemData.execution_model && systemData.execution_model !== 'Not Selected' 
                  ? systemData.execution_model 
                  : 'Not Selected'}
              </span>
            </div>
          </div>
        </div>

        {/* System Metrics */}
        <div className="tracker-section">
          <div className="metrics-header">
            <h4 className="section-label">System Metrics</h4>
            <span className="daily-reset-badge">Daily Reset: {systemData.daily_reset}</span>
          </div>
          <div className="metrics-grid">
            <div className="metric-item">
              <span className="metric-label">Uptime</span>
              <span className="metric-value">{systemData.uptime}</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Requests</span>
              <span className="metric-value">{systemData.requests_processed}</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Avg Response</span>
              <span className="metric-value">{systemData.avg_response_time.toFixed(0)}ms</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Success Rate</span>
              <span className="metric-value">{(systemData.success_rate || 0).toFixed(0)}%</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Memory</span>
              <span className="metric-value">{(systemData.memory_usage || 0).toFixed(0)}MB</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Errors (Today)</span>
              <span className="metric-value">{systemData.error_count}</span>
            </div>
          </div>
        </div>

        {/* Performance Bar */}
        {systemData.success_rate >= 0 && (
          <div className="performance-section">
            <div className="performance-label">
              <span>Performance Health</span>
              <span className="health-score">
                {systemData.success_rate >= 95 ? 'Excellent' : 
                 systemData.success_rate >= 85 ? 'Good' : 
                 systemData.success_rate >= 70 ? 'Fair' : 'Poor'}
              </span>
            </div>
            <div className="performance-bar">
              <div 
                className="performance-fill"
                style={{ width: `${Math.min(systemData.success_rate, 100)}%` }}
              ></div>
            </div>
            <div className="performance-info">
              <span className="info-text">Based on today's statistics (resets daily at midnight)</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemDataTracker;
