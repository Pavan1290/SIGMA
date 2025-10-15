import { useState, useEffect } from 'react';
import './ModelSelector.css';

function ModelSelector({ isOpen, onClose }) {
  const [models, setModels] = useState([]);
  const [thinkingModel, setThinkingModel] = useState(null);
  const [executionModel, setExecutionModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [draggedModel, setDraggedModel] = useState(null);

  const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

  useEffect(() => {
    if (isOpen) {
      fetchModels();
    }
  }, [isOpen]);

  const fetchModels = async () => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/models`);
      const data = await response.json();
      setModels(data.models);
      setThinkingModel(data.current_thinking);
      setExecutionModel(data.current_execution);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const handleSetThinkingModel = async (modelId) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_HTTP}/models/thinking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      });
      const data = await response.json();
      if (data.success) {
        setThinkingModel(modelId);
      }
    } catch (error) {
      console.error('Failed to set thinking model:', error);
    }
    setLoading(false);
  };

  const handleSetExecutionModel = async (modelId) => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_HTTP}/models/execution`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      });
      const data = await response.json();
      if (data.success) {
        setExecutionModel(modelId);
      }
    } catch (error) {
      console.error('Failed to set execution model:', error);
    }
    setLoading(false);
  };

  const handleDragStart = (e, model) => {
    setDraggedModel(model);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDropThinking = (e) => {
    e.preventDefault();
    if (draggedModel && draggedModel.available) {
      handleSetThinkingModel(draggedModel.id);
    }
    setDraggedModel(null);
  };

  const handleDropExecution = (e) => {
    e.preventDefault();
    if (draggedModel && draggedModel.available) {
      handleSetExecutionModel(draggedModel.id);
    }
    setDraggedModel(null);
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'google': return '🔵';
      case 'openai': return '🟢';
      case 'anthropic': return '🟣';
      case 'groq': return '🟠';
      case 'ollama': return '🏠';
      default: return '🤖';
    }
  };

  const getCapabilityIcon = (capability) => {
    switch (capability) {
      case 'reasoning': return '🧠';
      case 'code': return '💻';
      case 'vision': return '👁️';
      case 'chat': return '💬';
      case 'long-context': return '📜';
      default: return '✨';
    }
  };

  if (!isOpen) return null;

  const availableModels = models.filter(m => m.available);
  const unavailableModels = models.filter(m => !m.available);

  return (
    <div className="model-selector-overlay" onClick={onClose}>
      <div className="model-selector-panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <h2>🎯 AI Model Selector</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="panel-info">
          <p>Drag models to set them as <strong>Thinking</strong> or <strong>Execution</strong> models</p>
          <p className="hint">💡 Thinking models are best for planning, Execution models for quick tasks</p>
        </div>

        {/* Drop Zones */}
        <div className="drop-zones">
          <div 
            className={`drop-zone thinking-zone ${draggedModel ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDropThinking}
          >
            <div className="zone-header">
              <h3>🧠 Thinking Model</h3>
              <span className="zone-hint">For planning & reasoning</span>
            </div>
            {thinkingModel && (
              <div className="current-model">
                {models.find(m => m.id === thinkingModel) && (
                  <ModelCard 
                    model={models.find(m => m.id === thinkingModel)} 
                    getProviderIcon={getProviderIcon}
                    getCapabilityIcon={getCapabilityIcon}
                    compact
                  />
                )}
              </div>
            )}
          </div>

          <div 
            className={`drop-zone execution-zone ${draggedModel ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDropExecution}
          >
            <div className="zone-header">
              <h3>⚡ Execution Model</h3>
              <span className="zone-hint">For quick responses</span>
            </div>
            {executionModel && (
              <div className="current-model">
                {models.find(m => m.id === executionModel) && (
                  <ModelCard 
                    model={models.find(m => m.id === executionModel)} 
                    getProviderIcon={getProviderIcon}
                    getCapabilityIcon={getCapabilityIcon}
                    compact
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Available Models */}
        <div className="models-section">
          <h3>🎨 Available Models</h3>
          <div className="models-grid">
            {availableModels.map(model => (
              <div
                key={model.id}
                draggable
                onDragStart={(e) => handleDragStart(e, model)}
                className="draggable-model"
              >
                <ModelCard 
                  model={model}
                  getProviderIcon={getProviderIcon}
                  getCapabilityIcon={getCapabilityIcon}
                  onClick={() => {
                    if (loading) return;
                    // Quick click to set as thinking model
                    handleSetThinkingModel(model.id);
                  }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Unavailable Models */}
        {unavailableModels.length > 0 && (
          <div className="models-section unavailable-section">
            <h3>🔒 Unavailable (Missing API Keys)</h3>
            <div className="models-grid">
              {unavailableModels.map(model => (
                <ModelCard 
                  key={model.id}
                  model={model}
                  getProviderIcon={getProviderIcon}
                  getCapabilityIcon={getCapabilityIcon}
                  disabled
                />
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="spinner">⏳ Switching model...</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ModelCard({ model, getProviderIcon, getCapabilityIcon, compact = false, disabled = false, onClick }) {
  // Format rate limit display with detailed information
  const formatRateLimit = (limit, provider) => {
    if (!limit) {
      if (provider === 'ollama') {
        return '♾️ Unlimited (Local)';
      }
      return '♾️ Unlimited';
    }
    
    // Gemini: 50 RPD (Experimental), 10 RPM
    if (provider === 'google') {
      return `⏱️ ${limit.toLocaleString()} req/day (10/min)`;
    }
    
    // Groq: 1,000 RPD, 30 RPM
    if (provider === 'groq') {
      return `⏱️ ${limit.toLocaleString()} req/day (30/min)`;
    }
    
    // Others: show per-day limits
    return `⏱️ ${limit.toLocaleString()}/day`;
  };

  return (
    <div className={`model-card ${compact ? 'compact' : ''} ${disabled ? 'disabled' : ''}`} onClick={onClick}>
      <div className="model-header">
        <span className="provider-icon">{getProviderIcon(model.provider)}</span>
        <span className="model-name">{model.name}</span>
      </div>
      {!compact && (
        <>
          <p className="model-description">{model.description}</p>
          <div className="model-capabilities">
            {model.capabilities.map(cap => (
              <span key={cap} className="capability-tag">
                {getCapabilityIcon(cap)} {cap}
              </span>
            ))}
          </div>
          <div className="model-stats">
            <span className="stat">
              💰 FREE
            </span>
            <span className="stat">
              {formatRateLimit(model.rate_limit, model.provider)}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

export default ModelSelector;
