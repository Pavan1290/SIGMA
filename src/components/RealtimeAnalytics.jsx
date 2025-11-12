import React, { useState, useEffect } from 'react';
import './RealtimeAnalytics.css';

const RealtimeAnalytics = ({ analyticsData = {} }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeWindow, setTimeWindow] = useState('24h');
  const [animateLoad, setAnimateLoad] = useState(false);

  useEffect(() => {
    setAnimateLoad(true);
  }, []);

  // Sample analytics data
  const analyticsMetrics = {
    totalTasks: 1247,
    successfulTasks: 1178,
    failedTasks: 42,
    pendingTasks: 27,
    successRate: 94.48,
    avgResponseTime: 1.24,
    peakLoadTime: '14:32',
    systemUptime: 99.87,
    agentsActive: 3,
    mccToolsUsed: 23,
  };

  const timeSeriesData = [
    { time: '00:00', success: 45, failed: 2, pending: 1 },
    { time: '04:00', success: 38, failed: 1, pending: 2 },
    { time: '08:00', success: 62, failed: 3, pending: 1 },
    { time: '12:00', success: 89, failed: 5, pending: 3 },
    { time: '16:00', success: 124, failed: 8, pending: 5 },
    { time: '20:00', success: 98, failed: 4, pending: 2 },
  ];

  const agentPerformance = [
    { name: 'System Agent', icon: '⚙️', tasks: 421, success: 97.6, avgTime: 0.89, health: 99.2 },
    { name: 'Email Agent', icon: '✉️', tasks: 534, success: 93.8, avgTime: 1.45, health: 94.5 },
    { name: 'Web Agent', icon: '🌐', tasks: 292, success: 92.1, avgTime: 1.67, health: 91.3 },
  ];

  const topPatterns = [
    { name: 'quick_send', success: 342, failed: 8, confidence: 0.97 },
    { name: 'error_recovery', success: 267, failed: 18, confidence: 0.91 },
    { name: 'context_analysis', success: 189, failed: 14, confidence: 0.86 },
    { name: 'bulk_process', success: 156, failed: 22, confidence: 0.81 },
  ];

  const recentEvents = [
    { id: 1, type: 'success', message: 'Batch email processing completed', time: '2 min ago', agent: 'Email Agent' },
    { id: 2, type: 'warning', message: 'High memory usage detected', time: '8 min ago', agent: 'System' },
    { id: 3, type: 'success', message: 'New pattern learned successfully', time: '15 min ago', agent: 'System Agent' },
    { id: 4, type: 'info', message: 'MCP server health check passed', time: '24 min ago', agent: 'System' },
    { id: 5, type: 'success', message: 'Web scraping task completed', time: '31 min ago', agent: 'Web Agent' },
  ];

  const getEventIcon = (type) => {
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️'
    };
    return icons[type] || 'ℹ️';
  };

  const getEventColor = (type) => {
    const colors = {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#0ea5e9'
    };
    return colors[type] || '#0ea5e9';
  };

  return (
    <div className={`realtime-analytics ${animateLoad ? 'loaded' : ''}`}>
      {/* Header */}
      <div className="analytics-header">
        <div className="header-title">
          <span className="header-icon">📊</span>
          <h1>Real-time Analytics Hub</h1>
          <span className="live-badge">● LIVE</span>
        </div>

        {/* Time Window Selector */}
        <div className="time-window-selector">
          {['1h', '6h', '24h', '7d', '30d'].map(window => (
            <button
              key={window}
              className={`time-window-btn ${timeWindow === window ? 'active' : ''}`}
              onClick={() => setTimeWindow(window)}
            >
              {window}
            </button>
          ))}
        </div>
      </div>

      {/* Top KPIs */}
      <div className="kpis-row">
        <div className="kpi-mini">
          <div className="kpi-label">Total Tasks</div>
          <div className="kpi-value">{analyticsMetrics.totalTasks}</div>
          <div className="kpi-trend">↑ 12% from last period</div>
        </div>

        <div className="kpi-mini success">
          <div className="kpi-label">Success Rate</div>
          <div className="kpi-value">{analyticsMetrics.successRate}%</div>
          <div className="kpi-trend">↑ 2.1% improvement</div>
        </div>

        <div className="kpi-mini">
          <div className="kpi-label">Avg Response</div>
          <div className="kpi-value">{analyticsMetrics.avgResponseTime}s</div>
          <div className="kpi-trend">↓ 0.2s faster</div>
        </div>

        <div className="kpi-mini">
          <div className="kpi-label">Uptime</div>
          <div className="kpi-value">{analyticsMetrics.systemUptime}%</div>
          <div className="kpi-trend">Excellent health</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        {['overview', 'agents', 'patterns', 'events'].map(tab => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content Panels */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* Time Series Chart */}
          <div className="analytics-panel">
            <h2>📈 Task Timeline</h2>
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-label">Successful</span>
                <span className="chart-label warning">Failed</span>
              </div>
              <div className="time-series-chart">
                {timeSeriesData.map((data, idx) => (
                  <div key={idx} className="chart-column">
                    <div className="column-bars">
                      <div
                        className="bar success"
                        style={{ height: `${(data.success / 130) * 100}%` }}
                        title={`${data.success} successful`}
                      ></div>
                      <div
                        className="bar failed"
                        style={{ height: `${(data.failed / 10) * 100}%` }}
                        title={`${data.failed} failed`}
                      ></div>
                    </div>
                    <span className="column-time">{data.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Status Summary Grid */}
          <div className="status-grid">
            <div className="status-card successful">
              <div className="status-icon">✓</div>
              <div className="status-info">
                <div className="status-label">Successful</div>
                <div className="status-number">{analyticsMetrics.successfulTasks}</div>
              </div>
            </div>

            <div className="status-card failed">
              <div className="status-icon">✕</div>
              <div className="status-info">
                <div className="status-label">Failed</div>
                <div className="status-number">{analyticsMetrics.failedTasks}</div>
              </div>
            </div>

            <div className="status-card pending">
              <div className="status-icon">⏳</div>
              <div className="status-info">
                <div className="status-label">Pending</div>
                <div className="status-number">{analyticsMetrics.pendingTasks}</div>
              </div>
            </div>

            <div className="status-card info">
              <div className="status-icon">🔧</div>
              <div className="status-info">
                <div className="status-label">MCP Tools Active</div>
                <div className="status-number">{analyticsMetrics.mccToolsUsed}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="tab-content">
          <div className="analytics-panel">
            <h2>🤖 Agent Performance Leaderboard</h2>
            <div className="agents-leaderboard">
              {agentPerformance.map((agent, idx) => (
                <div key={idx} className="leaderboard-item">
                  <div className="rank">{idx + 1}</div>

                  <div className="agent-info-section">
                    <span className="agent-icon">{agent.icon}</span>
                    <div>
                      <div className="agent-name">{agent.name}</div>
                      <div className="agent-meta">{agent.tasks} tasks processed</div>
                    </div>
                  </div>

                  <div className="metrics-columns">
                    <div className="metric">
                      <span className="metric-label">Success</span>
                      <div className="metric-bar">
                        <div
                          className="metric-fill"
                          style={{ width: `${agent.success}%` }}
                        ></div>
                      </div>
                      <span className="metric-value">{agent.success}%</span>
                    </div>

                    <div className="metric">
                      <span className="metric-label">Avg Time</span>
                      <span className="metric-value time">{agent.avgTime}s</span>
                    </div>

                    <div className="metric">
                      <span className="metric-label">Health</span>
                      <div className="health-indicator">
                        <div
                          className="health-bar"
                          style={{
                            width: `${agent.health}%`,
                            backgroundColor: agent.health > 95 ? '#10b981' : agent.health > 90 ? '#f59e0b' : '#ef4444'
                          }}
                        ></div>
                      </div>
                      <span className="metric-value">{agent.health}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'patterns' && (
        <div className="tab-content">
          <div className="analytics-panel">
            <h2>🧬 Top Learned Patterns</h2>
            <div className="patterns-table">
              <div className="table-header">
                <div>Pattern Name</div>
                <div>Successful</div>
                <div>Failed</div>
                <div>Confidence</div>
              </div>

              {topPatterns.map((pattern, idx) => {
                const total = pattern.success + pattern.failed;
                const failRate = (pattern.failed / total) * 100;
                return (
                  <div key={idx} className="table-row">
                    <div className="pattern-name">🔗 {pattern.name}</div>
                    <div className="pattern-stat success">{pattern.success}</div>
                    <div className="pattern-stat failed">{pattern.failed}</div>
                    <div className="pattern-confidence">
                      <div className="confidence-bar">
                        <div
                          className="confidence-fill"
                          style={{
                            width: `${pattern.confidence * 100}%`,
                            backgroundColor: pattern.confidence > 0.9 ? '#10b981' : pattern.confidence > 0.8 ? '#f59e0b' : '#ef4444'
                          }}
                        ></div>
                      </div>
                      <span>{(pattern.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'events' && (
        <div className="tab-content">
          <div className="analytics-panel">
            <h2>📋 Recent System Events</h2>
            <div className="events-list">
              {recentEvents.map(event => (
                <div key={event.id} className={`event-item event-${event.type}`}>
                  <div className="event-icon">{getEventIcon(event.type)}</div>

                  <div className="event-content">
                    <div className="event-message">{event.message}</div>
                    <div className="event-meta">
                      <span className="event-agent">{event.agent}</span>
                      <span className="event-time">{event.time}</span>
                    </div>
                  </div>

                  <div className="event-status-dot" style={{ backgroundColor: getEventColor(event.type) }}></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer with Export & Refresh */}
      <div className="analytics-footer">
        <div className="footer-info">
          <span className="last-updated">Last updated: Just now</span>
          <span className="refresh-rate">Auto-refresh: Every 5s</span>
        </div>

        <div className="footer-actions">
          <button className="action-button export">📥 Export Data</button>
          <button className="action-button refresh">🔄 Refresh Now</button>
        </div>
      </div>
    </div>
  );
};

export default RealtimeAnalytics;
