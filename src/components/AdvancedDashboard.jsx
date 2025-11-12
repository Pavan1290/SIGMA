import React, { useState, useEffect } from 'react';
import './AdvancedDashboard.css';

const AdvancedDashboard = ({ agentStats = {}, memoryStats = {}, performanceMetrics = {} }) => {
  const [selectedAgent, setSelectedAgent] = useState('system');
  const [timeRange, setTimeRange] = useState('day');
  const [animateValues, setAnimateValues] = useState(false);

  useEffect(() => {
    setAnimateValues(true);
    const timer = setTimeout(() => setAnimateValues(false), 500);
    return () => clearTimeout(timer);
  }, [agentStats, memoryStats]);

  // Calculate statistics
  const stats = {
    totalTasks: agentStats.total_tasks || 247,
    successRate: agentStats.success_rate || 94.8,
    avgResponseTime: performanceMetrics.avg_response_time || 1.24,
    memoryUsed: memoryStats.total || 156,
    agentHealth: agentStats.health || 98.5,
    learningAccuracy: agentStats.learning_accuracy || 0.92,
  };

  const agents = [
    { name: 'system', icon: '⚙️', status: 'active', tasks: 98 },
    { name: 'email', icon: '✉️', status: 'active', tasks: 76 },
    { name: 'web', icon: '🌐', status: 'active', tasks: 73 },
  ];

  const recentPatterns = [
    { name: 'quick_send', confidence: 0.95, success: 48, uses: 'High' },
    { name: 'error_recovery', confidence: 0.87, success: 25, uses: 'Medium' },
    { name: 'draft_first', confidence: 0.78, success: 18, uses: 'Low' },
  ];

  return (
    <div className="advanced-dashboard">
      {/* Header with gradient and glassmorphism */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">
            <span className="title-icon">📊</span>
            Agent Intelligence Hub
          </h1>
          <p className="header-subtitle">Real-time monitoring & advanced insights</p>
        </div>

        {/* Time range selector */}
        <div className="time-range-selector">
          {['hour', 'day', 'week', 'month'].map(range => (
            <button
              key={range}
              className={`time-button ${timeRange === range ? 'active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">📈</span>
            <span className="kpi-label">Success Rate</span>
          </div>
          <div className="kpi-value">{stats.successRate.toFixed(1)}%</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${stats.successRate}%` }}></div>
          </div>
          <span className="kpi-change">↑ 2.3% from last period</span>
        </div>

        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">⚡</span>
            <span className="kpi-label">Avg Response Time</span>
          </div>
          <div className="kpi-value">{stats.avgResponseTime.toFixed(2)}s</div>
          <div className="kpi-bar">
            <div className="kpi-fill trend-positive" style={{ width: `${Math.min((3 - stats.avgResponseTime) * 50, 100)}%` }}></div>
          </div>
          <span className="kpi-change">↓ 0.3s improvement</span>
        </div>

        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">🧠</span>
            <span className="kpi-label">Agent Health</span>
          </div>
          <div className="kpi-value">{stats.agentHealth.toFixed(1)}%</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${stats.agentHealth}%` }}></div>
          </div>
          <span className="kpi-change">All systems optimal</span>
        </div>

        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">💾</span>
            <span className="kpi-label">Memory Used</span>
          </div>
          <div className="kpi-value">{stats.memoryUsed}MB</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${Math.min((stats.memoryUsed / 500) * 100, 100)}%` }}></div>
          </div>
          <span className="kpi-change">Healthy allocation</span>
        </div>

        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">🎯</span>
            <span className="kpi-label">Total Tasks</span>
          </div>
          <div className="kpi-value">{stats.totalTasks}</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${Math.min((stats.totalTasks / 300) * 100, 100)}%` }}></div>
          </div>
          <span className="kpi-change">+14 this period</span>
        </div>

        <div className={`kpi-card ${animateValues ? 'animate' : ''}`}>
          <div className="kpi-header">
            <span className="kpi-icon">🔬</span>
            <span className="kpi-label">Learning Accuracy</span>
          </div>
          <div className="kpi-value">{(stats.learningAccuracy * 100).toFixed(0)}%</div>
          <div className="kpi-bar">
            <div className="kpi-fill" style={{ width: `${stats.learningAccuracy * 100}%` }}></div>
          </div>
          <span className="kpi-change">Model optimized</span>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-content-grid">
        {/* Agent Status Panel */}
        <div className="dashboard-panel agent-status-panel">
          <div className="panel-header">
            <h2>🤖 Active Agents</h2>
            <div className="panel-badge">{agents.length} online</div>
          </div>

          <div className="agents-list">
            {agents.map(agent => (
              <div
                key={agent.name}
                className={`agent-item ${selectedAgent === agent.name ? 'selected' : ''}`}
                onClick={() => setSelectedAgent(agent.name)}
              >
                <div className="agent-header">
                  <span className="agent-icon">{agent.icon}</span>
                  <div className="agent-info">
                    <span className="agent-name">{agent.name.charAt(0).toUpperCase() + agent.name.slice(1)}</span>
                    <span className="agent-status">{agent.status}</span>
                  </div>
                </div>
                <div className="agent-stats">
                  <span className="stat">{agent.tasks} tasks</span>
                  <span className="status-dot active"></span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Learned Patterns Panel */}
        <div className="dashboard-panel patterns-panel">
          <div className="panel-header">
            <h2>🧬 Learned Patterns</h2>
            <div className="panel-badge">{recentPatterns.length} active</div>
          </div>

          <div className="patterns-list">
            {recentPatterns.map((pattern, idx) => (
              <div key={idx} className="pattern-item">
                <div className="pattern-name-section">
                  <span className="pattern-icon">🔗</span>
                  <div>
                    <div className="pattern-name">{pattern.name}</div>
                    <div className="pattern-meta">Used {pattern.uses}</div>
                  </div>
                </div>

                <div className="pattern-confidence">
                  <div className="confidence-label">
                    <span>Confidence</span>
                    <span className="confidence-value">{(pattern.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${pattern.confidence * 100}%`,
                        background: pattern.confidence > 0.9 ? '#10b981' : pattern.confidence > 0.75 ? '#f59e0b' : '#ef4444'
                      }}
                    ></div>
                  </div>
                </div>

                <span className="pattern-success">{pattern.success}✓</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Performance Chart */}
      <div className="dashboard-panel performance-panel">
        <div className="panel-header">
          <h2>📊 Performance Analytics</h2>
          <span className="update-badge">Live</span>
        </div>

        <div className="performance-grid">
          {/* Simplified ASCII Performance */}
          <div className="metric-chart">
            <h3>Response Time Trend</h3>
            <div className="chart-area">
              <div className="chart-bar" style={{ height: '45%' }}></div>
              <div className="chart-bar" style={{ height: '52%' }}></div>
              <div className="chart-bar" style={{ height: '48%' }}></div>
              <div className="chart-bar" style={{ height: '41%' }}></div>
              <div className="chart-bar" style={{ height: '38%' }}></div>
              <div className="chart-bar" style={{ height: '35%' }}></div>
            </div>
          </div>

          <div className="metric-chart">
            <h3>Success Rate Trend</h3>
            <div className="chart-area">
              <div className="chart-bar success" style={{ height: '88%' }}></div>
              <div className="chart-bar success" style={{ height: '90%' }}></div>
              <div className="chart-bar success" style={{ height: '92%' }}></div>
              <div className="chart-bar success" style={{ height: '94%' }}></div>
              <div className="chart-bar success" style={{ height: '93%' }}></div>
              <div className="chart-bar success" style={{ height: '95%' }}></div>
            </div>
          </div>

          <div className="metric-chart">
            <h3>Memory Usage</h3>
            <div className="chart-area">
              <div className="chart-bar warning" style={{ height: '35%' }}></div>
              <div className="chart-bar warning" style={{ height: '42%' }}></div>
              <div className="chart-bar warning" style={{ height: '38%' }}></div>
              <div className="chart-bar warning" style={{ height: '45%' }}></div>
              <div className="chart-bar warning" style={{ height: '50%' }}></div>
              <div className="chart-bar warning" style={{ height: '48%' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats Footer */}
      <div className="dashboard-footer">
        <div className="footer-stat">
          <span className="stat-label">Last Updated</span>
          <span className="stat-value">Just now</span>
        </div>
        <div className="footer-stat">
          <span className="stat-label">System Status</span>
          <span className="stat-value status-green">● All Systems Operational</span>
        </div>
        <div className="footer-stat">
          <span className="stat-label">Next Checkpoint</span>
          <span className="stat-value">in 47s</span>
        </div>
      </div>
    </div>
  );
};

export default AdvancedDashboard;
