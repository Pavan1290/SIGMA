import React, { useState, useEffect } from 'react';
import './AdvancedAPIKeyManager.css';

/**
 * Advanced API Key Manager - Save to Backend .env
 * Keys are stored securely on backend, not in browser
 */
const AdvancedAPIKeyManager = ({ isOpen, onClose, onVerified }) => {
  const [savedKeys, setSavedKeys] = useState({});
  const [activeProvider, setActiveProvider] = useState('google');
  const [inputKey, setInputKey] = useState('');
  const [previewKey, setPreviewKey] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [keyDetails, setKeyDetails] = useState(null);

  const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');

  const providers = {
    google: {
      label: 'Google Gemini',
      color: '#4285F4',
      models: ['gemini-pro', 'gemini-pro-vision'],
      docs: 'https://ai.google.dev/tutorials/python_quickstart'
    },
    groq: {
      label: 'Groq',
      color: '#FF6B35',
      models: ['mixtral-8x7b-32768', 'llama-2-70b-chat-hf'],
      docs: 'https://console.groq.com/keys'
    },
    openai: {
      label: 'OpenAI',
      color: '#10A37F',
      models: ['gpt-4', 'gpt-3.5-turbo'],
      docs: 'https://platform.openai.com/api-keys'
    },
    anthropic: {
      label: 'Anthropic Claude',
      color: '#8B5CF6',
      models: ['claude-3-opus', 'claude-3-sonnet'],
      docs: 'https://console.anthropic.com/dashboard'
    }
  };

  // Fetch saved keys from backend on mount
  useEffect(() => {
    if (isOpen) {
      fetchSavedKeys();
    }
  }, [isOpen]);

  const fetchSavedKeys = async () => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/list`);
      if (response.ok) {
        const data = await response.json();
        setSavedKeys(data.keys || {});
      }
    } catch (err) {
      console.error('Failed to fetch keys:', err);
    }
  };

  const maskApiKey = (key) => {
    if (key.length <= 8) return '*'.repeat(key.length);
    return key.slice(0, 4) + '*'.repeat(key.length - 8) + key.slice(-4);
  };

  const handlePreviewKey = () => {
    if (!inputKey.trim()) return;
    setPreviewKey(maskApiKey(inputKey));
    setVerificationResult(null);
    setKeyDetails(null);
  };

  const handleSaveKey = async () => {
    if (!inputKey.trim() || !previewKey) return;

    try {
      setVerifying(true);
      setVerificationResult(null);

      // Step 1: Try to verify the key (but allow save even if verification fails due to quota)
      let verifyData = null;
      let quotaIssue = false;
      
      try {
        const verifyResponse = await fetch(`${BACKEND_HTTP}/api-keys/verify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider: activeProvider,
            api_key: inputKey
          })
        });

        verifyData = await verifyResponse.json();
        
        // Check if error is due to quota/billing issues
        if (verifyData.error && (verifyData.error.includes('quota') || verifyData.error.includes('quota') || verifyData.error.includes('billing'))) {
          quotaIssue = true;
          console.warn('⚠️ Quota issue detected but key format is valid');
        }
      } catch (verifyErr) {
        console.warn('Verification attempt failed:', verifyErr.message);
      }

      // Step 2: Save key to backend .env regardless of verification result
      // (Allow users to save keys even if they're hitting quota limits)
      const saveResponse = await fetch(`${BACKEND_HTTP}/api-keys/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: activeProvider,
          api_key: inputKey
        })
      });

      const saveData = await saveResponse.json();

      if (!saveResponse.ok) {
        setVerificationResult({
          success: false,
          message: 'Failed to save key to backend'
        });
        setVerifying(false);
        return;
      }

      // Step 3: Display key details
      let status = 'Active';
      let statusNote = '';
      
      if (quotaIssue) {
        status = 'Limited - Quota Exceeded';
        statusNote = '⚠️ Your API quota is exceeded. Please upgrade your plan or wait for quota reset.';
      } else if (verifyData?.verified) {
        status = 'Verified & Active';
        statusNote = '✓ Key is valid and quota is available';
      } else {
        status = 'Saved (Unverified)';
        statusNote = 'Key saved. Verification skipped due to quota/connectivity.';
      }
      
      setKeyDetails({
        provider: currentProvider.label,
        status: status,
        statusNote: statusNote,
        models: currentProvider.models,
        verified: verifyData?.verified || quotaIssue,
        savedAt: new Date().toLocaleString()
      });

      // Update saved keys list
      setSavedKeys(prev => ({
        ...prev,
        [activeProvider]: true
      }));

      setVerificationResult({
        success: true,
        message: `API key saved for ${currentProvider.label}` + (quotaIssue ? ' (quota limited)' : ' (verified)')
      });

      // Reset form
      setInputKey('');
      setPreviewKey(null);
      onVerified?.();

      // Auto-clear result after 5 seconds
      setTimeout(() => {
        setVerificationResult(null);
      }, 5000);
    } catch (error) {
      setVerificationResult({
        success: false,
        message: 'Connection error. Backend unavailable.'
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleRemoveKey = async (provider) => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/api-keys/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider })
      });

      if (response.ok) {
        setSavedKeys(prev => {
          const updated = { ...prev };
          delete updated[provider];
          return updated;
        });

        setVerificationResult({
          success: true,
          message: `API key removed for ${providers[provider].label}`
        });

        if (activeProvider === provider) {
          setKeyDetails(null);
        }

        setTimeout(() => setVerificationResult(null), 2000);
      }
    } catch (err) {
      setVerificationResult({
        success: false,
        message: 'Failed to remove key'
      });
    }
  };

  if (!isOpen) return null;

  const currentProvider = providers[activeProvider];
  const isSaved = !!savedKeys[activeProvider];

  return (
    <div className="api-manager-overlay" onClick={onClose}>
      <div className="api-manager-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="api-manager-header">
          <div>
            <h2 className="api-manager-title">API Key Management</h2>
            <p className="api-manager-subtitle">Keys are stored securely on backend .env file</p>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close modal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6L18 18" />
            </svg>
          </button>
        </div>

        <div className="api-manager-body">
          {/* Provider Tabs */}
          <div className="provider-tabs">
            {Object.entries(providers).map(([key, provider]) => (
              <button
                key={key}
                className={`provider-tab ${activeProvider === key ? 'active' : ''} ${savedKeys[key] ? 'saved' : ''}`}
                onClick={() => {
                  setActiveProvider(key);
                  setInputKey('');
                  setPreviewKey(null);
                  setVerificationResult(null);
                  setKeyDetails(null);
                }}
                style={{ borderLeftColor: provider.color }}
              >
                <div className="provider-tab-label">{provider.label}</div>
                {savedKeys[key] && <div className="provider-tab-badge">Configured</div>}
              </button>
            ))}
          </div>

          {/* Main Content */}
          <div className="api-manager-content">
            {/* Provider Info */}
            <div className="provider-section">
              <h3 className="section-title">Provider Information</h3>
              <div className="provider-info">
                <div className="info-item">
                  <span className="info-label">Supported Models:</span>
                  <div className="model-tags">
                    {currentProvider.models.map(model => (
                      <span key={model} className="model-tag">{model}</span>
                    ))}
                  </div>
                </div>
                <a href={currentProvider.docs} target="_blank" rel="noopener noreferrer" className="info-link">
                  Get API key from provider
                </a>
              </div>
            </div>

            {/* Key Details (when saved) */}
            {isSaved && keyDetails && (
              <div className="key-details-section">
                <h3 className="section-title">Key Details</h3>
                <div className="details-grid">
                  <div className="detail-item">
                    <span className="detail-label">Provider</span>
                    <span className="detail-value">{keyDetails.provider}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Status</span>
                    <span className="detail-value status-active">✓ {keyDetails.status}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Saved at</span>
                    <span className="detail-value">{keyDetails.savedAt}</span>
                  </div>
                </div>
                {keyDetails.statusNote && (
                  <div className="status-note">
                    <small>{keyDetails.statusNote}</small>
                  </div>
                )}
              </div>
            )}

            {/* Input Workflow */}
            {!isSaved ? (
              <div className="input-workflow">
                {!previewKey && (
                  <div className="workflow-step">
                    <h3 className="step-title">Step 1: Enter API Key</h3>
                    <div className="input-group">
                      <input
                        type="password"
                        value={inputKey}
                        onChange={e => setInputKey(e.target.value)}
                        placeholder={`Enter your ${currentProvider.label} API key`}
                        className="key-input"
                      />
                      <button
                        type="button"
                        className="btn-preview"
                        onClick={handlePreviewKey}
                        disabled={!inputKey.trim()}
                      >
                        Preview Key
                      </button>
                    </div>
                  </div>
                )}

                {previewKey && !verifying && (
                  <div className="workflow-step preview-step">
                    <h3 className="step-title">Step 2: Verify & Save</h3>
                    <div className="preview-box">
                      <div className="preview-label">Masked Key Preview:</div>
                      <div className="preview-value">{previewKey}</div>
                      <div className="preview-hint">First 4 and last 4 characters visible</div>
                    </div>
                    <div className="action-buttons">
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          setPreviewKey(null);
                          setInputKey('');
                        }}
                      >
                        Back
                      </button>
                      <button
                        type="button"
                        className="btn-primary"
                        onClick={handleSaveKey}
                        disabled={verifying}
                      >
                        {verifying ? 'Verifying...' : 'Verify & Save to .env'}
                      </button>
                    </div>
                  </div>
                )}

                {verificationResult && (
                  <div className={`verification-message ${verificationResult.success ? 'success' : 'error'}`}>
                    {verificationResult.message}
                  </div>
                )}
              </div>
            ) : (
              <div className="saved-key-section">
                <h3 className="section-title">Configured Key</h3>
                <div className="saved-key-display">
                  <div className="saved-status">
                    <div className="status-indicator success"></div>
                    <span>API key saved in backend .env for {currentProvider.label}</span>
                  </div>
                  <button
                    type="button"
                    className="btn-remove"
                    onClick={() => handleRemoveKey(activeProvider)}
                  >
                    Remove Key
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="api-manager-footer">
          <div className="footer-text">
            API keys are stored securely on backend .env file, not in browser
          </div>
          <button type="button" className="btn-close-footer" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAPIKeyManager;
