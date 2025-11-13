import { useState, useEffect } from 'react';
import './APIKeyManager.css';

const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

// Provider configurations with futuristic themes
const PROVIDER_CONFIGS = {
  google: {
    name: 'Google Gemini',
    icon: '🤖',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    glowColor: '#667eea',
    models: [
      { id: 'gemini-2.0-flash-thinking', name: 'Gemini 2.0 Flash Thinking', description: 'Advanced reasoning with thinking process', type: 'thinking', power: 95 },
      { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash Experimental', description: 'Cutting-edge experimental model', type: 'both', power: 98 },
      { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', description: 'Lightning-fast responses', type: 'execution', power: 85 },
      { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', description: 'Professional-grade performance', type: 'execution', power: 90 }
    ],
    keyFormat: 'AIza...',
    getKeyUrl: 'https://aistudio.google.com/app/apikey'
  },
  groq: {
    name: 'Groq',
    icon: '⚡',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    glowColor: '#f5576c',
    models: [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile', description: 'Most powerful open-source model', type: 'thinking', power: 92 },
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant', description: 'Ultra-fast instant responses', type: 'execution', power: 75 },
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', description: 'Mixture of experts architecture', type: 'execution', power: 88 }
    ],
    keyFormat: 'gsk_...',
    getKeyUrl: 'https://console.groq.com/keys'
  },
  openai: {
    name: 'OpenAI',
    icon: '🧠',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    glowColor: '#00f2fe',
    models: [
      { id: 'gpt-4o', name: 'GPT-4o', description: 'Omni-modal intelligence', type: 'thinking', power: 97 },
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Efficient & affordable', type: 'execution', power: 82 },
      { id: 'o1-preview', name: 'O1 Preview', description: 'Advanced reasoning model', type: 'thinking', power: 99 }
    ],
    keyFormat: 'sk-...',
    getKeyUrl: 'https://platform.openai.com/api-keys'
  },
  anthropic: {
    name: 'Anthropic Claude',
    icon: '🎭',
    gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    glowColor: '#fa709a',
    models: [
      { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', description: 'Supreme intelligence & reasoning', type: 'thinking', power: 96 },
      { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', description: 'Fast & efficient responses', type: 'execution', power: 84 },
      { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', description: 'Maximum capability model', type: 'thinking', power: 94 }
    ],
    keyFormat: 'sk-ant-...',
    getKeyUrl: 'https://console.anthropic.com/settings/keys'
  }
};

const APIKeyManager = ({ onClose, onModelUpdate }) => {
  const [providers, setProviders] = useState(
    Object.keys(PROVIDER_CONFIGS).map(id => ({
      id,
      ...PROVIDER_CONFIGS[id],
      key: '',
      verified: false,
      usage: null
    }))
  );
  
  const [activeTab, setActiveTab] = useState('keys');
  const [verifying, setVerifying] = useState({});
  const [showKey, setShowKey] = useState({});
  const [statusMessage, setStatusMessage] = useState(null);
  const [showPreview, setShowPreview] = useState(null);
  const [selectedModels, setSelectedModels] = useState({});
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    loadAPIKeys();
    loadUsageStats();
    // Create floating particles
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 20 + 10,
      delay: Math.random() * 5
    }));
    setParticles(newParticles);
  }, []);

  const loadAPIKeys = async () => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/status`);
      const data = await response.json();
      
      if (data.status) {
        setProviders(prev => prev.map(p => ({
          ...p,
          verified: data.status[p.id]?.verified || false,
          key: data.status[p.id]?.masked_key || p.key
        })));
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
      setStatusMessage({ type: 'error', text: 'Failed to connect to backend' });
    }
  };

  const loadUsageStats = async () => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/usage`);
      const data = await response.json();
      
      if (data.providers) {
        setProviders(prev => prev.map(p => ({
          ...p,
          usage: data.providers[p.id] || null
        })));
      }
    } catch (error) {
      console.error('Failed to load usage stats:', error);
    }
  };

  const handleKeyChange = (providerId, value) => {
    setProviders(prev => prev.map(p => 
      p.id === providerId ? { ...p, key: value, verified: false } : p
    ));
  };

  const handleVerifyClick = (provider) => {
    if (!provider.key || provider.key.includes('*')) {
      setStatusMessage({ type: 'error', text: 'Enter a valid API key' });
      return;
    }

    setShowPreview(provider);
    const thinkingModel = provider.models.find(m => m.type === 'thinking' || m.type === 'both');
    const executionModel = provider.models.find(m => m.type === 'execution' || m.type === 'both');
    setSelectedModels({
      thinking: thinkingModel?.id || provider.models[0]?.id,
      execution: executionModel?.id || provider.models[0]?.id
    });
  };

  const handleConfirmVerify = async () => {
    const provider = showPreview;
    setVerifying({ ...verifying, [provider.id]: true });
    setStatusMessage(null);

    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: provider.id,
          apiKey: provider.key
        })
      });

      const data = await response.json();

      if (data.success) {
        // Update provider state
        setProviders(prev => prev.map(p => 
          p.id === provider.id ? { ...p, verified: true, key: provider.key } : p
        ));
        
        // Create success particles effect
        createSuccessParticles();
        
        setStatusMessage({ 
          type: 'success', 
          text: `🎉 ${provider.name} activated!` 
        });

        // Auto-update models
        if (onModelUpdate) {
          try {
            // First set the thinking model
            const thinkingResponse = await fetch(`${BACKEND_HTTP}/models/thinking`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ model_id: selectedModels.thinking })
            });
            
            if (!thinkingResponse.ok) throw new Error('Failed to set thinking model');
            
            // Then set the execution model
            const executionResponse = await fetch(`${BACKEND_HTTP}/models/execution`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ model_id: selectedModels.execution })
            });
            
            if (!executionResponse.ok) throw new Error('Failed to set execution model');
            
            // Notify parent to refresh UI
            onModelUpdate({
              thinking: selectedModels.thinking,
              execution: selectedModels.execution,
              provider: provider.id
            });
            
            setStatusMessage({ 
              type: 'success', 
              text: `✨ Models activated and saved!` 
            });
          } catch (modelError) {
            console.error('Model update error:', modelError);
            setStatusMessage({ 
              type: 'error', 
              text: `API verified but model update failed: ${modelError.message}` 
            });
          }
        }

        setShowPreview(null);
        setTimeout(() => {
          loadAPIKeys();
          loadUsageStats();
        }, 800);
      } else {
        setStatusMessage({ 
          type: 'error', 
          text: `Verification failed: ${data.error}` 
        });
      }
    } catch (error) {
      console.error('Verification error:', error);
      setStatusMessage({ 
        type: 'error', 
        text: `Error: ${error.message}` 
      });
    } finally {
      setVerifying({ ...verifying, [provider.id]: false });
    }
  };

  const handleDelete = async (providerId) => {
    if (!confirm(`Delete API key for ${providers.find(p => p.id === providerId)?.name}?`)) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/${providerId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (data.success) {
        setProviders(prev => prev.map(p => 
          p.id === providerId ? { ...p, key: '', verified: false } : p
        ));
        setStatusMessage({ type: 'success', text: 'API key deleted' });
      }
    } catch (error) {
      setStatusMessage({ type: 'error', text: `Delete failed: ${error.message}` });
    }
  };

  const createSuccessParticles = () => {
    // Trigger particle explosion animation
    const element = document.querySelector('.manager-content');
    if (element) {
      element.classList.add('success-explosion');
      setTimeout(() => element.classList.remove('success-explosion'), 1000);
    }
  };

  const totalUsage = providers.reduce((acc, p) => ({
    requests: acc.requests + (p.usage?.requests || 0),
    tokens: acc.tokens + (p.usage?.tokens || 0),
    cost: acc.cost + (p.usage?.estimated_cost || 0)
  }), { requests: 0, tokens: 0, cost: 0 });

  return (
    <div className="api-key-manager-overlay" onClick={onClose}>
      {/* Floating particles background */}
      <div className="particles-container">
        {particles.map(particle => (
          <div
            key={particle.id}
            className="particle"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDuration: `${particle.duration}s`,
              animationDelay: `${particle.delay}s`
            }}
          />
        ))}
      </div>

      <div className="api-key-manager futuristic" onClick={(e) => e.stopPropagation()}>
        {/* Holographic Header */}
        <div className="manager-header holographic">
          <div className="header-content">
            <div className="header-icon-wrapper">
              <div className="icon-glow"></div>
              <svg className="header-icon" width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="8" cy="8" r="4" stroke="currentColor" strokeWidth="2" />
                <path d="M12 11l8 8M17 16l-1 1M20 19l-1 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </div>
            <div className="header-text">
              <h2>API Key Nexus</h2>
              <p className="header-subtitle">Neural Network Integration</p>
            </div>
          </div>
          <button className="close-button futuristic" onClick={onClose}>
            <span className="close-icon"></span>
            <span className="close-icon cross"></span>
          </button>
        </div>

        {/* Futuristic Tabs */}
        <div className="manager-tabs futuristic">
          <button 
            className={`tab futuristic ${activeTab === 'keys' ? 'active' : ''}`}
            onClick={() => setActiveTab('keys')}
          >
            <span className="tab-icon">🔑</span>
            <span className="tab-text">Neural Keys</span>
            <div className="tab-glow"></div>
          </button>
          <button 
            className={`tab futuristic ${activeTab === 'usage' ? 'active' : ''}`}
            onClick={() => setActiveTab('usage')}
          >
            <span className="tab-icon">📊</span>
            <span className="tab-text">Analytics</span>
            <div className="tab-glow"></div>
          </button>
          <div className="tab-indicator" style={{ transform: activeTab === 'usage' ? 'translateX(100%)' : 'translateX(0)' }}></div>
        </div>

        {/* Status Message */}
        {statusMessage && (
          <div className={`status-message futuristic ${statusMessage.type}`}>
            <div className="status-pulse"></div>
            <span>{statusMessage.text}</span>
          </div>
        )}

        {/* Content */}
        <div className="manager-content futuristic">
          {activeTab === 'keys' ? (
            <>
              <p className="section-description neon">
                Connect your AI providers to unlock neural capabilities
              </p>

              <div className="providers-grid">
                {providers.map(provider => (
                  <div 
                    key={provider.id} 
                    className="provider-card holographic"
                    style={{ '--card-gradient': provider.gradient, '--glow-color': provider.glowColor }}
                  >
                    <div className="card-glow"></div>
                    <div className="card-content">
                      <div className="provider-header">
                        <div className="provider-icon-wrapper">
                          <span className="provider-icon-large">{provider.icon}</span>
                          <div className="icon-pulse"></div>
                        </div>
                        <div className="provider-info">
                          <h3>{provider.name}</h3>
                          <a href={provider.getKeyUrl} target="_blank" rel="noopener" className="get-key-link">
                            Get Key →
                          </a>
                        </div>
                        {provider.verified && (
                          <div className="verified-badge futuristic">
                            <div className="badge-glow"></div>
                            <span>✓ ACTIVE</span>
                          </div>
                        )}
                      </div>

                      <div className="key-input-wrapper">
                        <input
                          type={showKey[provider.id] ? 'text' : 'password'}
                          className="key-input futuristic"
                          placeholder={`${provider.keyFormat} • Enter ${provider.name} key`}
                          value={provider.key}
                          onChange={(e) => handleKeyChange(provider.id, e.target.value)}
                          disabled={verifying[provider.id]}
                        />
                        <button
                          className="toggle-visibility futuristic"
                          onClick={() => setShowKey({ ...showKey, [provider.id]: !showKey[provider.id] })}
                        >
                          {showKey[provider.id] ? '👁️' : '👁️‍🗨️'}
                        </button>
                      </div>

                      <div className="action-buttons">
                        <button
                          className="verify-button futuristic"
                          onClick={() => handleVerifyClick(provider)}
                          disabled={verifying[provider.id] || !provider.key || provider.key.includes('*')}
                        >
                          <div className="button-glow"></div>
                          {verifying[provider.id] ? (
                            <>
                              <div className="spinner futuristic"></div>
                              <span>Verifying...</span>
                            </>
                          ) : (
                            <>
                              <span>⚡ Activate Neural Link</span>
                            </>
                          )}
                        </button>
                        {provider.verified && (
                          <button
                            className="delete-button futuristic"
                            onClick={() => handleDelete(provider.id)}
                          >
                            <span>🗑️</span>
                          </button>
                        )}
                      </div>

                      {provider.usage && (
                        <div className="usage-display">
                          <div className="usage-item">
                            <span className="usage-label">Requests</span>
                            <span className="usage-value">{provider.usage.requests || 0}</span>
                          </div>
                          <div className="usage-item">
                            <span className="usage-label">Tokens</span>
                            <span className="usage-value">{(provider.usage.tokens || 0).toLocaleString()}</span>
                          </div>
                          <div className="usage-item">
                            <span className="usage-label">Cost</span>
                            <span className="usage-value cost">${(provider.usage.estimated_cost || 0).toFixed(4)}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="analytics-dashboard">
                <h3 className="dashboard-title">System Analytics</h3>
                <div className="stats-grid">
                  <div className="stat-card holographic">
                    <div className="stat-icon">📡</div>
                    <div className="stat-value">{totalUsage.requests}</div>
                    <div className="stat-label">Total Requests</div>
                    <div className="stat-glow"></div>
                  </div>
                  <div className="stat-card holographic">
                    <div className="stat-icon">🔢</div>
                    <div className="stat-value">{totalUsage.tokens.toLocaleString()}</div>
                    <div className="stat-label">Tokens Processed</div>
                    <div className="stat-glow"></div>
                  </div>
                  <div className="stat-card holographic">
                    <div className="stat-icon">💎</div>
                    <div className="stat-value">${totalUsage.cost.toFixed(4)}</div>
                    <div className="stat-label">Total Cost</div>
                    <div className="stat-glow"></div>
                  </div>
                </div>

                <div className="provider-analytics">
                  {providers.filter(p => p.usage).map(provider => (
                    <div key={provider.id} className="provider-stat-card holographic">
                      <div className="provider-stat-header">
                        <span className="provider-icon">{provider.icon}</span>
                        <h4>{provider.name}</h4>
                      </div>
                      <div className="stat-bars">
                        <div className="stat-bar-item">
                          <span className="bar-label">Requests</span>
                          <div className="bar-wrapper">
                            <div 
                              className="bar-fill" 
                              style={{ 
                                width: `${Math.min((provider.usage?.requests || 0) / Math.max(totalUsage.requests, 1) * 100, 100)}%`,
                                background: provider.gradient
                              }}
                            ></div>
                          </div>
                          <span className="bar-value">{provider.usage?.requests || 0}</span>
                        </div>
                        <div className="stat-bar-item">
                          <span className="bar-label">Tokens</span>
                          <div className="bar-wrapper">
                            <div 
                              className="bar-fill" 
                              style={{ 
                                width: `${Math.min((provider.usage?.tokens || 0) / Math.max(totalUsage.tokens, 1) * 100, 100)}%`,
                                background: provider.gradient
                              }}
                            ></div>
                          </div>
                          <span className="bar-value">{(provider.usage?.tokens || 0).toLocaleString()}</span>
                        </div>
                        <div className="stat-bar-item">
                          <span className="bar-label">Cost</span>
                          <div className="bar-wrapper">
                            <div 
                              className="bar-fill" 
                              style={{ 
                                width: `${Math.min((provider.usage?.estimated_cost || 0) / Math.max(totalUsage.cost, 0.0001) * 100, 100)}%`,
                                background: provider.gradient
                              }}
                            ></div>
                          </div>
                          <span className="bar-value cost">${(provider.usage?.estimated_cost || 0).toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Preview Modal */}
        {showPreview && (
          <div className="preview-overlay futuristic" onClick={() => setShowPreview(null)}>
            <div className="preview-modal futuristic" onClick={(e) => e.stopPropagation()}>
              <div className="preview-glow"></div>
              <div className="preview-header">
                <h3>
                  <span className="preview-icon">{showPreview.icon}</span>
                  Configure {showPreview.name}
                </h3>
                <p className="preview-subtitle">Select your neural network models</p>
              </div>

              <div className="model-selectors">
                <div className="model-selector-group">
                  <label className="selector-label">
                    <span className="label-icon">🧠</span>
                    Thinking Model
                  </label>
                  <select 
                    className="model-select futuristic"
                    value={selectedModels.thinking}
                    onChange={(e) => setSelectedModels({ ...selectedModels, thinking: e.target.value })}
                  >
                    {showPreview.models.filter(m => m.type === 'thinking' || m.type === 'both').map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name} • Power: {model.power}%
                      </option>
                    ))}
                  </select>
                </div>

                <div className="model-selector-group">
                  <label className="selector-label">
                    <span className="label-icon">⚡</span>
                    Execution Model
                  </label>
                  <select 
                    className="model-select futuristic"
                    value={selectedModels.execution}
                    onChange={(e) => setSelectedModels({ ...selectedModels, execution: e.target.value })}
                  >
                    {showPreview.models.filter(m => m.type === 'execution' || m.type === 'both').map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name} • Power: {model.power}%
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="models-showcase">
                <h4>Available Neural Networks</h4>
                <div className="models-grid">
                  {showPreview.models.map(model => (
                    <div key={model.id} className="model-card holographic">
                      <div className="model-card-header">
                        <span className="model-name">{model.name}</span>
                        <span className={`model-type-badge ${model.type}`}>
                          {model.type === 'thinking' ? '🧠' : model.type === 'execution' ? '⚡' : '🔄'}
                        </span>
                      </div>
                      <p className="model-description">{model.description}</p>
                      <div className="power-meter">
                        <div className="power-label">Power Level</div>
                        <div className="power-bar">
                          <div 
                            className="power-fill" 
                            style={{ 
                              width: `${model.power}%`,
                              background: `linear-gradient(90deg, ${showPreview.glowColor}44, ${showPreview.glowColor})`
                            }}
                          >
                            <span className="power-text">{model.power}%</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="preview-actions">
                <button className="cancel-button futuristic" onClick={() => setShowPreview(null)}>
                  <span>Cancel</span>
                </button>
                <button 
                  className="confirm-button futuristic" 
                  onClick={handleConfirmVerify}
                  disabled={verifying[showPreview.id]}
                >
                  <div className="button-glow-intense"></div>
                  {verifying[showPreview.id] ? (
                    <>
                      <div className="spinner futuristic"></div>
                      <span>Activating...</span>
                    </>
                  ) : (
                    <span>⚡ Activate & Deploy</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="manager-footer futuristic">
          <div className="footer-pulse"></div>
          <p>🔒 Quantum-encrypted storage • Neural network secured</p>
        </div>
      </div>
    </div>
  );
};

export default APIKeyManager;
