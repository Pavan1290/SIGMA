import React, { useState, useEffect } from 'react';
import './AdvancedModelSelector.css';

/**
 * Advanced AI Model Selector - Professional Enterprise Model Management
 * Features: Filter, Sort, Dual-selection, Real-time sync
 */
const AdvancedModelSelector = ({ isOpen, onClose, onModelSelect, currentModels = {} }) => {
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [loading, setLoading] = useState(true);
  const [selectedModels, setSelectedModels] = useState({
    thinking: currentModels.thinking || null,
    execution: currentModels.execution || null
  });
  const [error, setError] = useState(null);

  const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

  // Provider configuration - NO EMOJIS
  const providerConfig = {
    google: { name: 'Google Gemini', color: '#4285F4', models: [] },
    groq: { name: 'Groq', color: '#FF6B35', models: [] },
    openai: { name: 'OpenAI', color: '#10A37F', models: [] },
    anthropic: { name: 'Anthropic Claude', color: '#8B5CF6', models: [] },
    ollama: { name: 'Ollama (Local)', color: '#00D084', models: [] }
  };

  useEffect(() => {
    if (isOpen) {
      fetchModels();
    }
  }, [isOpen]);

  useEffect(() => {
    filterAndSortModels();
  }, [models, searchTerm, selectedProvider, sortBy]);

  const fetchModels = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${BACKEND_HTTP}/models`);
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data.models || []);
    } catch (err) {
      setError('Failed to load models. Please try again.');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortModels = () => {
    let filtered = [...models];

    // Filter by provider
    if (selectedProvider !== 'all') {
      filtered = filtered.filter(m => m.provider === selectedProvider);
    }

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(m =>
        m.name.toLowerCase().includes(term) ||
        (m.description && m.description.toLowerCase().includes(term))
      );
    }

    // Sort models
    filtered.sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (sortBy === 'provider') {
        return a.provider.localeCompare(b.provider);
      }
      return 0;
    });

    setFilteredModels(filtered);
  };

  const handleModelSelect = (modelId, type) => {
    setSelectedModels(prev => {
      const updated = { ...prev };
      updated[type] = updated[type] === modelId ? null : modelId;
      return updated;
    });
  };

  const handleConfirmSelection = async () => {
    try {
      const updates = [];

      if (selectedModels.thinking) {
        updates.push(
          fetch(`${BACKEND_HTTP}/models/thinking`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_id: selectedModels.thinking })
          })
        );
      }

      if (selectedModels.execution) {
        updates.push(
          fetch(`${BACKEND_HTTP}/models/execution`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_id: selectedModels.execution })
          })
        );
      }

      await Promise.all(updates);
      onModelSelect?.(selectedModels);
      onClose();
    } catch (err) {
      setError('Failed to update models');
      console.error('Update error:', err);
    }
  };

  const getProviderLabel = (provider) => {
    return providerConfig[provider]?.name || provider;
  };

  const getSelectedModelName = (modelId, type) => {
    if (!modelId) return type === 'thinking' ? 'Select Thinking Model' : 'Select Execution Model';
    const model = models.find(m => m.id === modelId);
    return model?.name || 'Unknown';
  };

  if (!isOpen) return null;

  return (
    <div className="model-selector-overlay" onClick={onClose}>
      <div className="model-selector-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="header-content">
            <h2 className="modal-title">AI Model Selection</h2>
            <p className="modal-subtitle">Select your thinking and execution models for intelligent processing</p>
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6L18 18"/>
            </svg>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-banner">
            <span className="error-text">{error}</span>
            <button className="error-dismiss" onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="modal-content">
          {/* Controls Section */}
          <div className="controls-section">
            <div className="search-box">
              <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
              </svg>
              <input
                type="text"
                placeholder="Search models by name..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="filters-row">
              <div className="filter-group">
                <label className="filter-label">Provider</label>
                <select 
                  value={selectedProvider}
                  onChange={e => setSelectedProvider(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">All Providers</option>
                  {Object.entries(providerConfig).map(([key, val]) => (
                    <option key={key} value={key}>{val.name}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label className="filter-label">Sort</label>
                <select 
                  value={sortBy}
                  onChange={e => setSortBy(e.target.value)}
                  className="filter-select"
                >
                  <option value="name">By Name</option>
                  <option value="provider">By Provider</option>
                </select>
              </div>
            </div>
          </div>

          {/* Selection Display */}
          <div className="selection-display">
            <div className="selection-card">
              <h3 className="selection-title">Thinking Model</h3>
              <p className="selection-description">For planning and reasoning tasks</p>
              <div className="selection-preview">
                <div className="preview-badge">
                  {selectedModels.thinking ? (
                    <>
                      <span className="provider-label">{getProviderLabel(models.find(m => m.id === selectedModels.thinking)?.provider)}</span>
                      <span className="model-name">{getSelectedModelName(selectedModels.thinking, 'thinking')}</span>
                    </>
                  ) : (
                    <span className="no-selection">Not Selected</span>
                  )}
                </div>
              </div>
            </div>

            <div className="selection-card">
              <h3 className="selection-title">Execution Model</h3>
              <p className="selection-description">For fast responses and task execution</p>
              <div className="selection-preview">
                <div className="preview-badge">
                  {selectedModels.execution ? (
                    <>
                      <span className="provider-label">{getProviderLabel(models.find(m => m.id === selectedModels.execution)?.provider)}</span>
                      <span className="model-name">{getSelectedModelName(selectedModels.execution, 'execution')}</span>
                    </>
                  ) : (
                    <span className="no-selection">Not Selected</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Models List */}
          <div className="models-section">
            <h3 className="section-title">Available Models ({filteredModels.length})</h3>
            
            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Loading models...</p>
              </div>
            ) : filteredModels.length === 0 ? (
              <div className="empty-state">
                <p>No models found matching your criteria</p>
              </div>
            ) : (
              <div className="models-list">
                {filteredModels.map(model => (
                  <div key={model.id} className="model-item">
                    <div className="model-main">
                      <div className="model-info">
                        <h4 className="model-name">{model.name}</h4>
                        <p className="model-provider">{getProviderLabel(model.provider)}</p>
                        {model.description && (
                          <p className="model-description">{model.description}</p>
                        )}
                      </div>
                      <div className="model-specs">
                        {model.power && (
                          <div className="spec">
                            <span className="spec-label">Power:</span>
                            <span className="spec-value">{model.power}%</span>
                          </div>
                        )}
                        {model.rate_limit && (
                          <div className="spec">
                            <span className="spec-label">Rate Limit:</span>
                            <span className="spec-value">{model.rate_limit.toLocaleString()}/day</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="model-actions">
                      <button 
                        className={`action-btn thinking-btn ${selectedModels.thinking === model.id ? 'selected' : ''}`}
                        onClick={() => handleModelSelect(model.id, 'thinking')}
                        title="Select as thinking model"
                      >
                        {selectedModels.thinking === model.id ? 'Thinking ✓' : 'Use for Thinking'}
                      </button>
                      <button 
                        className={`action-btn execution-btn ${selectedModels.execution === model.id ? 'selected' : ''}`}
                        onClick={() => handleModelSelect(model.id, 'execution')}
                        title="Select as execution model"
                      >
                        {selectedModels.execution === model.id ? 'Execution ✓' : 'Use for Execution'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button 
            className="btn-primary" 
            onClick={handleConfirmSelection}
            disabled={!selectedModels.thinking || !selectedModels.execution}
          >
            Apply Selection
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdvancedModelSelector;
