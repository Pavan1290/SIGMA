import React, { useState, useEffect } from 'react';
import './ReasoningEvaluator.css';

const ReasoningEvaluator = ({ reasoningData = {} }) => {
  const [selectedApproach, setSelectedApproach] = useState(0);
  const [showDetails, setShowDetails] = useState(false);
  const [animateLoad, setAnimateLoad] = useState(false);

  useEffect(() => {
    setAnimateLoad(true);
  }, []);

  // Sample reasoning paths
  const reasoningPaths = [
    {
      id: 1,
      name: 'Direct Resolution',
      icon: '🎯',
      riskLevel: 'Low',
      riskScore: 12,
      confidence: 0.94,
      steps: [
        { step: 1, action: 'Identify email type', status: 'completed', duration: 0.23 },
        { step: 2, action: 'Check filters', status: 'completed', duration: 0.15 },
        { step: 3, action: 'Apply rule', status: 'completed', duration: 0.08 },
        { step: 4, action: 'Send confirmation', status: 'completed', duration: 0.12 },
      ],
      reasoning: 'Pattern matching found in previous successful tasks',
      successRate: 96.8,
      usageFrequency: 'High'
    },
    {
      id: 2,
      name: 'Contextual Analysis',
      icon: '🧩',
      riskLevel: 'Medium',
      riskScore: 38,
      confidence: 0.87,
      steps: [
        { step: 1, action: 'Extract context', status: 'completed', duration: 0.45 },
        { step: 2, action: 'Compare patterns', status: 'completed', duration: 0.62 },
        { step: 3, action: 'Evaluate alternatives', status: 'completed', duration: 0.53 },
        { step: 4, action: 'Select best match', status: 'completed', duration: 0.34 },
      ],
      reasoning: 'Multi-approach comparison with weighted factors',
      successRate: 83.5,
      usageFrequency: 'Medium'
    },
    {
      id: 3,
      name: 'Adaptive Learning',
      icon: '🔄',
      riskLevel: 'High',
      riskScore: 62,
      confidence: 0.71,
      steps: [
        { step: 1, action: 'Analyze anomalies', status: 'completed', duration: 0.78 },
        { step: 2, action: 'Retrain local model', status: 'completed', duration: 1.23 },
        { step: 3, action: 'Test hypothesis', status: 'completed', duration: 0.91 },
        { step: 4, action: 'Update strategy', status: 'completed', duration: 0.45 },
      ],
      reasoning: 'Experimental approach with model adaptation',
      successRate: 72.1,
      usageFrequency: 'Low'
    },
    {
      id: 4,
      name: 'Fallback Handler',
      icon: '🛡️',
      riskLevel: 'Low',
      riskScore: 15,
      confidence: 0.99,
      steps: [
        { step: 1, action: 'Queue request', status: 'completed', duration: 0.08 },
        { step: 2, action: 'Alert escalation', status: 'completed', duration: 0.12 },
        { step: 3, action: 'Log event', status: 'completed', duration: 0.15 },
        { step: 4, action: 'Send notification', status: 'completed', duration: 0.18 },
      ],
      reasoning: 'Safety-first approach for edge cases',
      successRate: 99.2,
      usageFrequency: 'Critical'
    }
  ];

  const selectedPath = reasoningPaths[selectedApproach];
  const totalSteps = selectedPath.steps.length;
  const completedSteps = selectedPath.steps.filter(s => s.status === 'completed').length;

  const getRiskColor = (level) => {
    switch (level) {
      case 'Low':
        return '#10b981';
      case 'Medium':
        return '#f59e0b';
      case 'High':
        return '#ef4444';
      default:
        return '#0ea5e9';
    }
  };

  const getRiskBackground = (level) => {
    switch (level) {
      case 'Low':
        return 'rgba(16, 185, 129, 0.1)';
      case 'Medium':
        return 'rgba(245, 158, 11, 0.1)';
      case 'High':
        return 'rgba(239, 68, 68, 0.1)';
      default:
        return 'rgba(14, 165, 233, 0.1)';
    }
  };

  const getRecommendation = () => {
    if (selectedPath.riskScore < 25) return '✅ Recommended - Low risk, high confidence';
    if (selectedPath.riskScore < 50) return '⚠️ Proceed with caution - Moderate risk';
    return '🚨 High risk - Consider alternatives';
  };

  return (
    <div className={`reasoning-evaluator ${animateLoad ? 'loaded' : ''}`}>
      {/* Header */}
      <div className="evaluator-header">
        <div className="header-content">
          <h1 className="evaluator-title">
            <span className="header-icon">🧠</span>
            Intelligent Reasoning Evaluator
          </h1>
          <p className="header-subtitle">Multi-path decision analysis & risk assessment</p>
        </div>
      </div>

      {/* Approaches Grid */}
      <div className="approaches-grid">
        {reasoningPaths.map((approach, idx) => (
          <button
            key={approach.id}
            className={`approach-card ${selectedApproach === idx ? 'active' : ''}`}
            onClick={() => setSelectedApproach(idx)}
          >
            <div className="card-header">
              <span className="approach-icon">{approach.icon}</span>
              <h3>{approach.name}</h3>
            </div>

            <div className="card-metrics">
              <div className="metric">
                <span className="metric-label">Confidence</span>
                <span className="metric-value">{(approach.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="metric">
                <span className="metric-label">Risk</span>
                <span
                  className="metric-value risk"
                  style={{ color: getRiskColor(approach.riskLevel) }}
                >
                  {approach.riskLevel}
                </span>
              </div>
            </div>

            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${approach.confidence * 100}%` }}
              ></div>
            </div>
          </button>
        ))}
      </div>

      {/* Main Analysis Panel */}
      <div className="analysis-panel">
        <div className="panel-header">
          <div>
            <h2>{selectedPath.name}</h2>
            <p>{selectedPath.reasoning}</p>
          </div>
          <div className="recommendation-badge">
            {getRecommendation()}
          </div>
        </div>

        {/* Decision Path Visualization */}
        <div className="decision-path-section">
          <h3>Decision Path ({completedSteps}/{totalSteps})</h3>

          <div className="path-visualization">
            {selectedPath.steps.map((step, idx) => (
              <div key={step.step} className="path-step">
                <div className="step-node">
                  <span className="step-number">{step.step}</span>
                  <div className="step-status">
                    {step.status === 'completed' && <span className="checkmark">✓</span>}
                  </div>
                </div>

                <div className="step-content">
                  <div className="step-action">{step.action}</div>
                  <div className="step-duration">{step.duration.toFixed(2)}s</div>
                </div>

                {idx < selectedPath.steps.length - 1 && <div className="step-connector"></div>}
              </div>
            ))}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-card-header">
              <span className="metric-icon">📊</span>
              <span>Success Rate</span>
            </div>
            <div className="metric-card-value">{selectedPath.successRate}%</div>
            <div className="metric-bar">
              <div
                className="metric-fill"
                style={{ width: `${selectedPath.successRate}%` }}
              ></div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-card-header">
              <span className="metric-icon">🎯</span>
              <span>Confidence Level</span>
            </div>
            <div className="metric-card-value">{(selectedPath.confidence * 100).toFixed(0)}%</div>
            <div className="metric-bar">
              <div
                className="metric-fill"
                style={{
                  width: `${selectedPath.confidence * 100}%`,
                  background: selectedPath.confidence > 0.9
                    ? '#10b981'
                    : selectedPath.confidence > 0.75
                    ? '#f59e0b'
                    : '#ef4444'
                }}
              ></div>
            </div>
          </div>

          <div
            className="metric-card"
            style={{ background: getRiskBackground(selectedPath.riskLevel) }}
          >
            <div className="metric-card-header">
              <span className="metric-icon">⚠️</span>
              <span>Risk Assessment</span>
            </div>
            <div
              className="metric-card-value"
              style={{ color: getRiskColor(selectedPath.riskLevel) }}
            >
              {selectedPath.riskScore}%
            </div>
            <div className="metric-bar">
              <div
                className="metric-fill"
                style={{
                  width: `${selectedPath.riskScore}%`,
                  background: getRiskColor(selectedPath.riskLevel)
                }}
              ></div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-card-header">
              <span className="metric-icon">📈</span>
              <span>Usage Frequency</span>
            </div>
            <div className="metric-card-value">{selectedPath.usageFrequency}</div>
            <div className="usage-indicator">
              {['Critical', 'High', 'Medium', 'Low'].map(freq => (
                <div
                  key={freq}
                  className={`indicator ${selectedPath.usageFrequency === freq ? 'active' : ''}`}
                  title={freq}
                ></div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="comparison-section">
        <div className="section-header">
          <h3>Quick Comparison</h3>
          <button
            className="detail-toggle"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? '📉 Hide' : '📈 Show'} Details
          </button>
        </div>

        <div className="comparison-table">
          <div className="table-header">
            <div className="col col-name">Approach</div>
            <div className="col col-confidence">Confidence</div>
            <div className="col col-risk">Risk</div>
            <div className="col col-success">Success Rate</div>
            <div className="col col-usage">Usage</div>
          </div>

          {reasoningPaths.map((approach, idx) => (
            <div
              key={approach.id}
              className={`table-row ${selectedApproach === idx ? 'selected' : ''}`}
              onClick={() => setSelectedApproach(idx)}
            >
              <div className="col col-name">
                <span className="row-icon">{approach.icon}</span>
                {approach.name}
              </div>
              <div className="col col-confidence">
                <div className="inline-bar">
                  <div
                    className="bar-fill"
                    style={{ width: `${approach.confidence * 100}%` }}
                  ></div>
                </div>
                {(approach.confidence * 100).toFixed(0)}%
              </div>
              <div className="col col-risk">
                <span
                  className="risk-badge"
                  style={{
                    background: getRiskBackground(approach.riskLevel),
                    color: getRiskColor(approach.riskLevel),
                    borderColor: getRiskColor(approach.riskLevel)
                  }}
                >
                  {approach.riskLevel}
                </span>
              </div>
              <div className="col col-success">
                <div className="inline-bar success">
                  <div
                    className="bar-fill"
                    style={{ width: `${approach.successRate}%` }}
                  ></div>
                </div>
                {approach.successRate}%
              </div>
              <div className="col col-usage">
                <span className="usage-badge">{approach.usageFrequency}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Reasoning Insights */}
      <div className="insights-section">
        <h3>📌 Analysis Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <span className="insight-icon">🔍</span>
            <div>
              <h4>Dominant Path</h4>
              <p>{reasoningPaths[0].name} - {reasoningPaths[0].successRate}% success rate</p>
            </div>
          </div>
          <div className="insight-card">
            <span className="insight-icon">⚡</span>
            <div>
              <h4>Fastest Route</h4>
              <p>
                {reasoningPaths[0].name} at{' '}
                {reasoningPaths[0].steps.reduce((sum, s) => sum + s.duration, 0).toFixed(2)}s total
              </p>
            </div>
          </div>
          <div className="insight-card">
            <span className="insight-icon">🛡️</span>
            <div>
              <h4>Safest Option</h4>
              <p>{reasoningPaths[3].name} - Fallback for edge cases</p>
            </div>
          </div>
          <div className="insight-card">
            <span className="insight-icon">🎓</span>
            <div>
              <h4>Learning Potential</h4>
              <p>{reasoningPaths[2].name} - Best for model improvement</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReasoningEvaluator;
