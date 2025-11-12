import React, { useState, useEffect } from 'react';
import './AgentMemoryVisualizer.css';

const AgentMemoryVisualizer = ({ memoryData = {} }) => {
  const [expandedMemory, setExpandedMemory] = useState('short-term');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterConfidence, setFilterConfidence] = useState(0);
  const [animateLoad, setAnimateLoad] = useState(false);

  useEffect(() => {
    setAnimateLoad(true);
  }, []);

  // Sample memory structure
  const memoryStructure = {
    'short-term': {
      label: 'Short-term Memory (Active Context)',
      icon: '⚡',
      color: '#0ea5e9',
      capacity: 100,
      used: 67,
      ttl: '5 minutes',
      items: [
        { id: 1, content: 'User asked about email automation', confidence: 0.98, timestamp: '2 min ago', type: 'query' },
        { id: 2, content: 'Email subject pattern: urgent vs normal', confidence: 0.95, timestamp: '3 min ago', type: 'pattern' },
        { id: 3, content: 'Last 5 emails processed successfully', confidence: 0.99, timestamp: '1 min ago', type: 'result' },
        { id: 4, content: 'User preference: detailed responses', confidence: 0.87, timestamp: '5 min ago', type: 'preference' },
      ]
    },
    'long-term': {
      label: 'Long-term Memory (Persistent Knowledge)',
      icon: '💾',
      color: '#10b981',
      capacity: 1000,
      used: 347,
      ttl: '30 days',
      items: [
        { id: 5, content: 'User email filter rules', confidence: 0.92, timestamp: '2 days ago', type: 'rule' },
        { id: 6, content: 'Common response patterns', confidence: 0.88, timestamp: '5 days ago', type: 'pattern' },
        { id: 7, content: 'Email scheduling preferences', confidence: 0.85, timestamp: '1 week ago', type: 'preference' },
        { id: 8, content: 'Integration history & API calls', confidence: 0.79, timestamp: '2 weeks ago', type: 'history' },
      ]
    },
    'episodic': {
      label: 'Episodic Memory (Events & Context)',
      icon: '📖',
      color: '#f59e0b',
      capacity: 500,
      used: 234,
      ttl: '90 days',
      items: [
        { id: 9, content: 'Session with user #12345 - resolved email issue', confidence: 0.91, timestamp: '3 hours ago', type: 'event' },
        { id: 10, content: 'Batch email processing - 500 emails', confidence: 0.89, timestamp: '6 hours ago', type: 'event' },
        { id: 11, content: 'Model update applied successfully', confidence: 0.97, timestamp: '1 day ago', type: 'event' },
        { id: 12, content: 'Integration test with Gmail API', confidence: 0.84, timestamp: '2 days ago', type: 'event' },
      ]
    },
    'semantic': {
      label: 'Semantic Memory (Concepts & Knowledge)',
      icon: '🧠',
      color: '#a855f7',
      capacity: 800,
      used: 512,
      ttl: 'Indefinite',
      items: [
        { id: 13, content: 'Email classification taxonomy', confidence: 0.93, timestamp: '1 month ago', type: 'concept' },
        { id: 14, content: 'User communication style', confidence: 0.86, timestamp: '2 weeks ago', type: 'concept' },
        { id: 15, content: 'Domain-specific terminology', confidence: 0.90, timestamp: '3 weeks ago', type: 'concept' },
        { id: 16, content: 'Relationship between agents & tasks', confidence: 0.88, timestamp: '1 month ago', type: 'concept' },
      ]
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      query: '#06b6d4',
      pattern: '#8b5cf6',
      result: '#10b981',
      preference: '#f59e0b',
      rule: '#ef4444',
      history: '#3b82f6',
      event: '#ec4899',
      concept: '#a855f7'
    };
    return colors[type] || '#0ea5e9';
  };

  const getTypeEmoji = (type) => {
    const emojis = {
      query: '❓',
      pattern: '🔗',
      result: '✅',
      preference: '⚙️',
      rule: '📋',
      history: '📚',
      event: '📌',
      concept: '💡'
    };
    return emojis[type] || '📝';
  };

  const filteredItems = memoryStructure[expandedMemory].items.filter(item =>
    (item.content.toLowerCase().includes(searchQuery.toLowerCase()) || searchQuery === '') &&
    item.confidence >= filterConfidence
  );

  const totalCapacity = Object.values(memoryStructure).reduce((sum, mem) => sum + mem.used, 0);
  const totalCapacityMax = Object.values(memoryStructure).reduce((sum, mem) => sum + mem.capacity, 0);
  const overallUsage = (totalCapacity / totalCapacityMax) * 100;

  return (
    <div className={`agent-memory-visualizer ${animateLoad ? 'loaded' : ''}`}>
      {/* Header */}
      <div className="memory-header">
        <div className="header-title">
          <span className="title-icon">🧠</span>
          <h1>Agent Memory Hierarchy</h1>
        </div>
        <div className="header-stats">
          <div className="stat">
            <span className="stat-label">Total Capacity Used</span>
            <span className="stat-value">{totalCapacity} / {totalCapacityMax} units</span>
          </div>
          <div className="usage-bar">
            <div className="usage-fill" style={{ width: `${overallUsage}%` }}></div>
          </div>
        </div>
      </div>

      {/* Memory Type Selector */}
      <div className="memory-selector">
        {Object.entries(memoryStructure).map(([key, memory]) => (
          <button
            key={key}
            className={`memory-type-button ${expandedMemory === key ? 'active' : ''}`}
            onClick={() => setExpandedMemory(key)}
          >
            <span className="button-icon">{memory.icon}</span>
            <span className="button-label">
              {memory.label.split('(')[0].trim()}
              <span className="button-capacity">({memory.used}/{memory.capacity})</span>
            </span>
          </button>
        ))}
      </div>

      {/* Memory Hierarchy Visualization */}
      <div className="memory-hierarchy-panel">
        <div className="hierarchy-title">
          <span>Memory Hierarchy Overview</span>
        </div>

        <div className="hierarchy-visualization">
          {Object.entries(memoryStructure).map(([key, memory], idx) => {
            const usagePercent = (memory.used / memory.capacity) * 100;
            return (
              <div key={key} className="hierarchy-item">
                <div className="hierarchy-layer">
                  <div className="layer-header">
                    <span className="layer-icon">{memory.icon}</span>
                    <div className="layer-info">
                      <span className="layer-name">{memory.label.split('(')[0].trim()}</span>
                      <span className="layer-ttl">TTL: {memory.ttl}</span>
                    </div>
                  </div>
                  <div className="layer-capacity-bar">
                    <div
                      className="capacity-fill"
                      style={{
                        width: `${usagePercent}%`,
                        background: memory.color,
                        boxShadow: `0 0 15px ${memory.color}80`
                      }}
                    ></div>
                  </div>
                  <div className="layer-stats">
                    <span>{usagePercent.toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Controls Panel */}
      <div className="controls-panel">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="confidence-filter">
          <label>Min Confidence: {(filterConfidence * 100).toFixed(0)}%</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={filterConfidence}
            onChange={(e) => setFilterConfidence(parseFloat(e.target.value))}
          />
        </div>
      </div>

      {/* Memory Items Display */}
      <div className="memory-items-panel">
        <div className="panel-header">
          <h2>{memoryStructure[expandedMemory].label}</h2>
          <span className="items-count">{filteredItems.length} items</span>
        </div>

        <div className="memory-items-list">
          {filteredItems.length > 0 ? (
            filteredItems.map((item, idx) => (
              <div
                key={item.id}
                className="memory-item"
                style={{
                  animationDelay: `${idx * 50}ms`
                }}
              >
                <div className="item-type">
                  <span className="type-emoji">{getTypeEmoji(item.type)}</span>
                  <span
                    className="type-badge"
                    style={{
                      backgroundColor: `${getTypeColor(item.type)}30`,
                      borderColor: getTypeColor(item.type),
                      color: getTypeColor(item.type)
                    }}
                  >
                    {item.type}
                  </span>
                </div>

                <div className="item-content">
                  <p className="content-text">{item.content}</p>
                  <span className="item-timestamp">{item.timestamp}</span>
                </div>

                <div className="item-confidence">
                  <div className="confidence-label">
                    <span>Confidence</span>
                    <span className="confidence-percent">{(item.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="confidence-bar">
                    <div
                      className="confidence-indicator"
                      style={{
                        width: `${item.confidence * 100}%`,
                        background: item.confidence > 0.9
                          ? '#10b981'
                          : item.confidence > 0.75
                          ? '#f59e0b'
                          : '#ef4444'
                      }}
                    ></div>
                  </div>
                </div>

                <div className="item-actions">
                  <button className="action-btn" title="View details">📖</button>
                  <button className="action-btn" title="Pin memory">📌</button>
                  <button className="action-btn" title="Export">💾</button>
                </div>
              </div>
            ))
          ) : (
            <div className="no-items">
              <p>No memories match your filters</p>
            </div>
          )}
        </div>
      </div>

      {/* Memory Stats Footer */}
      <div className="memory-stats-footer">
        <div className="stat-group">
          <span className="stat-title">Total Memories</span>
          <span className="stat-number">{Object.values(memoryStructure).reduce((sum, mem) => sum + mem.items.length, 0)}</span>
        </div>

        <div className="stat-group">
          <span className="stat-title">Avg Confidence</span>
          <span className="stat-number">
            {(Object.values(memoryStructure)
              .reduce((sum, mem) => sum + mem.items.reduce((s, item) => s + item.confidence, 0), 0) /
              Object.values(memoryStructure).reduce((sum, mem) => sum + mem.items.length, 0) * 100).toFixed(0)}%
          </span>
        </div>

        <div className="stat-group">
          <span className="stat-title">Memory Health</span>
          <span className="stat-number health-good">Optimal</span>
        </div>

        <div className="stat-group">
          <span className="stat-title">Last Pruning</span>
          <span className="stat-number">2 hours ago</span>
        </div>
      </div>
    </div>
  );
};

export default AgentMemoryVisualizer;
