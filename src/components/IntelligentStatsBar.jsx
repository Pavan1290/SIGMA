import { useState, useEffect } from 'react';
import './IntelligentStatsBar.css';

const IntelligentStatsBar = ({ messagesCount, backendOnline }) => {
  const [stats, setStats] = useState({
    tasksCompleted: 0,
    successRate: 95.2,
    avgResponseTime: 1.3,
    agentsActive: 3,
  });

  const [animateStats, setAnimateStats] = useState(false);

  useEffect(() => {
    // Animate stats on mount
    setAnimateStats(true);
    const timer = setTimeout(() => setAnimateStats(false), 600);
    return () => clearTimeout(timer);
  }, []);

  // Update tasks completed based on messages
  useEffect(() => {
    setStats(prev => ({
      ...prev,
      tasksCompleted: Math.floor(messagesCount / 2)
    }));
  }, [messagesCount]);

  return (
    <div className="intelligent-stats-bar">
      <div className="stats-grid">
        <div className={`stat-card ${animateStats ? 'animate' : ''}`}>
          <div className="stat-icon">⚡</div>
          <div className="stat-content">
            <div className="stat-value">{stats.tasksCompleted}</div>
            <div className="stat-label">Tasks Completed</div>
          </div>
        </div>

        <div className={`stat-card ${animateStats ? 'animate' : ''}`}>
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{stats.successRate}%</div>
            <div className="stat-label">Success Rate</div>
          </div>
        </div>

        <div className={`stat-card ${animateStats ? 'animate' : ''}`}>
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">{stats.avgResponseTime}s</div>
            <div className="stat-label">Avg Response</div>
          </div>
        </div>

        <div className={`stat-card ${animateStats ? 'animate' : ''}`}>
          <div className="stat-icon">🤖</div>
          <div className="stat-content">
            <div className="stat-value">{stats.agentsActive}</div>
            <div className="stat-label">Agents Active</div>
          </div>
        </div>

        <div className={`stat-card status-card ${animateStats ? 'animate' : ''}`}>
          <div className={`status-indicator ${backendOnline ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            <span className="status-text">{backendOnline ? 'System Online' : 'Connecting...'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligentStatsBar;
