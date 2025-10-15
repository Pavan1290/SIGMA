import { useState, useEffect, useRef } from 'react';
import './IntelligentAssistant.css';
import ModelSelector from './ModelSelector';

// Backend URL config: allow override via Vite env, fallback to localhost:5000
const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');
const BACKEND_WS = BACKEND_HTTP.replace(/^http/, 'ws') + '/ws';

function IntelligentAssistant() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [agentStatus, setAgentStatus] = useState({ agent: null, status: 'idle', progress: 0 });
  const [thinkingProcess, setThinkingProcess] = useState([]);
  const [currentTask, setCurrentTask] = useState(null); // Track current task details
  const [expandedMessages, setExpandedMessages] = useState(new Set()); // Track expanded message IDs
  const [isProcessing, setIsProcessing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [showModelSelector, setShowModelSelector] = useState(false); // NEW: Model selector state
  const [currentModels, setCurrentModels] = useState({ thinking: null, execution: null }); // NEW: Track selected models
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Fetch current models on mount and when selector closes
  useEffect(() => {
    fetchCurrentModels();
  }, [showModelSelector]);

  const fetchCurrentModels = async () => {
    try {
      const response = await fetch(`${BACKEND_HTTP}/models`);
      const data = await response.json();
      const thinkingModel = data.models.find(m => m.id === data.current_thinking);
      const executionModel = data.models.find(m => m.id === data.current_execution);
      setCurrentModels({
        thinking: thinkingModel?.name || 'Unknown',
        execution: executionModel?.name || 'Unknown'
      });
    } catch (error) {
      console.error('Failed to fetch current models:', error);
    }
  };

  // WebSocket connection for real-time updates
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, []);

  const connectWebSocket = () => {
    // Clear any existing timer before attempting a new connection
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);

    const ws = new WebSocket(BACKEND_WS);
    
    ws.onopen = () => {
      console.log('✅ Connected to SIGMA-OS Agent System');
      // Don't add system message on connection - keep it clean!
      setBackendOnline(true);
      reconnectAttemptsRef.current = 0; // reset backoff
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'connection') {
        // Don't show connection messages - keep UI clean
        console.log(`✅ ${data.message}`, data.agents);
      } else if (data.agent_name) {
        // Agent update
        handleAgentUpdate(data);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setBackendOnline(false);
      scheduleReconnect();
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setBackendOnline(false);
      scheduleReconnect();
    };
    
    wsRef.current = ws;
  };

  const scheduleReconnect = () => {
    // Exponential backoff with jitter
    const base = 1000; // 1s
    const max = 30000; // 30s
    const attempt = Math.min(reconnectAttemptsRef.current + 1, 10);
    reconnectAttemptsRef.current = attempt;
    const delay = Math.min(base * 2 ** (attempt - 1), max);
    const jitter = Math.random() * 250; // slight jitter
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    reconnectTimerRef.current = setTimeout(connectWebSocket, delay + jitter);
  };

  const handleAgentUpdate = (update) => {
    // Update agent status
    setAgentStatus({
      agent: update.agent_name,
      status: update.status,
      progress: update.progress || 0,
      message: update.message
    });

    // Add to thinking process
    if (update.thinking_process || update.action_taken) {
      setThinkingProcess(prev => [...prev, {
        timestamp: update.timestamp,
        type: update.status,
        message: update.thinking_process || update.action_taken,
        agent: update.agent_name
      }]);
    }

    // Show in chat if significant
    if (update.status === 'success' || update.status === 'error') {
      const icon = update.status === 'success' ? '✅' : '❌';
      addMessage('agent', `${icon} ${update.agent_name}: ${update.message}`);
    }
  };

  const addMessage = (type, content, metadata = null) => {
    const msgId = Date.now() + Math.random();
    setMessages(prev => [...prev, { 
      id: msgId,
      type, 
      content, 
      metadata, // Store task details, plan, results
      timestamp: new Date().toLocaleTimeString() 
    }]);
    return msgId;
  };

  const toggleMessageExpanded = (msgId) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(msgId)) {
        newSet.delete(msgId);
      } else {
        newSet.add(msgId);
      }
      return newSet;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userCommand = input.trim();
    setInput('');
    setIsProcessing(true);
    setThinkingProcess([]);
    setCurrentTask({
      command: userCommand,
      steps: [],
      context: {},
      started: Date.now()
    });

    // Add user message
    addMessage('user', userCommand);

    try {
      const response = await fetch(`${BACKEND_HTTP}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: userCommand, mode: 'agent' })
      });

      const data = await response.json();

      if (data.success) {
        // Create rich metadata for the task
        const metadata = {
          agent: data.agent_used,
          reasoning: data.thinking_process,
          plan: data.result.plan,
          results: data.result.results,
          task: data.result.task,
          success: true
        };

        // Add success message with expandable details
        addMessage('assistant', 
          `✅ Task completed successfully!`,
          metadata
        );
      } else {
        addMessage('error', `❌ Task failed: ${data.result.error || 'Unknown error'}`);
      }
    } catch (error) {
      addMessage('error', `❌ Connection error: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setAgentStatus({ agent: null, status: 'idle', progress: 0 });
      setCurrentTask(null);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="intelligent-assistant">
      <div className="header">
        <h1>🧠 SIGMA-OS</h1>
        <p className="subtitle">Intelligent AI Agent System</p>
        <div className="header-controls">
          {currentModels.thinking && (
            <div className="current-model-display">
              <span className="model-label">🧠 Model:</span>
              <span className="model-value">{currentModels.thinking}</span>
            </div>
          )}
          <button 
            className="model-selector-button"
            onClick={() => setShowModelSelector(true)}
            title="Change AI Model"
          >
            🎯 AI Models
          </button>
        </div>
      </div>

      {/* Model Selector Modal */}
      <ModelSelector 
        isOpen={showModelSelector} 
        onClose={() => setShowModelSelector(false)} 
      />

      {/* Backend connectivity banner */}
      {!backendOnline && (
        <div className="agent-status error" style={{ margin: '0 1rem 1rem', borderLeft: '4px solid #ef4444' }}>
          <div className="status-header">
            <span className="agent-name">🛜 Backend disconnected</span>
            <span className="status-badge">reconnecting...</span>
          </div>
          <div className="status-message">
            Trying to reach {BACKEND_HTTP} / {BACKEND_WS}. We'll reconnect automatically.
          </div>
        </div>
      )}

      {/* Agent Status Panel - Compact version in corner */}
      {agentStatus.agent && (
        <div className={`agent-status-compact ${agentStatus.status}`}>
          <div className="compact-header">
            <span className="compact-icon">
              {agentStatus.status === 'thinking' && '🧠'}
              {agentStatus.status === 'executing' && '⚙️'}
              {agentStatus.status === 'success' && '✅'}
              {agentStatus.status === 'error' && '❌'}
            </span>
            <span className="compact-text">{agentStatus.message}</span>
          </div>
          {agentStatus.progress > 0 && agentStatus.progress < 100 && (
            <div className="compact-progress">
              <div className="compact-progress-fill" style={{ width: `${agentStatus.progress}%` }} />
            </div>
          )}
        </div>
      )}

      {/* Thinking Process Panel - Hidden by default, can be toggled */}
      {/* Removed to keep UI clean - thinking details now in expandable sections */}

      {/* Chat Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-header">
              <h2>👋 Welcome to SIGMA-OS</h2>
              <p className="welcome-subtitle">Your intelligent AI agent system with multi-model support</p>
            </div>
            
            <div className="features-grid">
              <div className="feature-card">
                <span className="feature-icon">🤖</span>
                <h3>Smart Agents</h3>
                <p>System, Email, and Web agents ready to help</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon">⚡</span>
                <h3>Multi-Model AI</h3>
                <p>Switch between Gemini, Groq, and Ollama</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon">🔄</span>
                <h3>Real-time</h3>
                <p>Live updates and intelligent task execution</p>
              </div>
            </div>

            <div className="example-commands">
              <h3>✨ Try these commands:</h3>
              <ul>
                <li onClick={() => setInput("list files in my desktop")}>
                  📁 "list files in my desktop"
                </li>
                <li onClick={() => setInput("check disk space")}>
                  💾 "check disk space"
                </li>
                <li onClick={() => setInput("create a file called test.txt with hello world")}>
                  📝 "create a file called test.txt with hello world"
                </li>
                <li onClick={() => setInput("take a screenshot")}>
                  📸 "take a screenshot"
                </li>
                <li onClick={() => setInput("what's the current time and date")}>
                  🕐 "what's the current time and date"
                </li>
              </ul>
            </div>

            {backendOnline && (
              <div className="connection-status">
                <span className="status-dot online"></span>
                <span>Connected • Ready to assist</span>
              </div>
            )}
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`message ${msg.type}`}>
            <div className="message-header">
              <span className="message-icon">
                {msg.type === 'user' && '👤'}
                {msg.type === 'assistant' && '🤖'}
                {msg.type === 'agent' && '⚙️'}
                {msg.type === 'system' && '💡'}
                {msg.type === 'error' && '❌'}
              </span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-content">
              {msg.type === 'assistant' && msg.metadata ? (
                // Rich task display - SHOW MAIN OUTPUT FIRST
                <div className="task-result">
                  <div className="task-summary">
                    <h3>{msg.content}</h3>
                    <div className="task-meta">
                      <span className="meta-item">🤖 Agent: <strong>{msg.metadata.agent}</strong></span>
                      <span className="meta-item">📝 Task: {msg.metadata.task}</span>
                    </div>
                  </div>

                  {/* MAIN OUTPUT - Show directly (not hidden) */}
                  {msg.metadata.results && msg.metadata.results.length > 0 && (
                    <div className="main-output">
                      <h4>📤 Output:</h4>
                      {msg.metadata.results.map((result, idx) => (
                        <div key={idx} className="output-item">
                          {result.output && (
                            <pre className="output-text">{result.output}</pre>
                          )}
                          {result.command && !result.output && (
                            <div className="command-executed">
                              <code>{result.command}</code>
                              <span className={`status-indicator ${result.success ? 'success' : 'failed'}`}>
                                {result.success ? '✅' : '❌'}
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Expandable Details Section - Hide technical stuff */}
                  <div className="task-expand-container">
                    <button 
                      className="expand-button"
                      onClick={() => toggleMessageExpanded(msg.id)}
                    >
                      {expandedMessages.has(msg.id) ? '▼' : '▶'} 
                      {expandedMessages.has(msg.id) ? ' Hide Technical Details' : ' Show Technical Details'}
                    </button>

                    {expandedMessages.has(msg.id) && (
                      <div className="task-details">
                        {/* AI's Understanding */}
                        {msg.metadata.plan && (
                          <div className="detail-section">
                            <h4>🧠 AI's Understanding</h4>
                            <p>{msg.metadata.plan.understanding}</p>
                          </div>
                        )}

                        {/* Strategy */}
                        {msg.metadata.plan && (
                          <div className="detail-section">
                            <h4>🎯 Strategy</h4>
                            <p>{msg.metadata.plan.approach}</p>
                          </div>
                        )}

                        {/* Steps Executed */}
                        {msg.metadata.plan && msg.metadata.plan.steps && (
                          <div className="detail-section">
                            <h4>📋 Steps Planned</h4>
                            {msg.metadata.plan.steps.map((step, idx) => (
                              <div key={idx} className="step-item">
                                <div className="step-header">
                                  <span className="step-number">Step {step.step}</span>
                                  <span className="step-tool">🔧 Tool: {step.tool}</span>
                                </div>
                                <div className="step-action">{step.action}</div>
                                <div className="step-outcome">
                                  <strong>Expected:</strong> {step.expected_outcome}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Actual Execution Results */}
                        {msg.metadata.results && msg.metadata.results.length > 0 && (
                          <div className="detail-section">
                            <h4>✅ What Actually Happened</h4>
                            {msg.metadata.results.map((result, idx) => (
                              <div key={idx} className="execution-result">
                                <div className="result-header">
                                  <span className={`result-status ${result.success ? 'success' : 'failed'}`}>
                                    {result.success ? '✅ Success' : '❌ Failed'}
                                  </span>
                                  {result.exit_code !== undefined && (
                                    <span className="exit-code">Exit Code: {result.exit_code}</span>
                                  )}
                                </div>
                                
                                {result.command && (
                                  <div className="result-command">
                                    <strong>Command:</strong>
                                    <code>{result.command}</code>
                                  </div>
                                )}

                                {result.operation && (
                                  <div className="result-operation">
                                    <strong>Operation:</strong> {result.operation}
                                  </div>
                                )}

                                {result.path && (
                                  <div className="result-path">
                                    <strong>Path:</strong> <code>{result.path}</code>
                                  </div>
                                )}

                                {result.output && (
                                  <div className="result-output">
                                    <strong>Output:</strong>
                                    <pre>{result.output}</pre>
                                  </div>
                                )}

                                {result.error && (
                                  <div className="result-error">
                                    <strong>Error:</strong>
                                    <pre>{result.error}</pre>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Context Awareness Info */}
                        {msg.metadata.plan && msg.metadata.plan.potential_issues && (
                          <div className="detail-section">
                            <h4>⚠️ Potential Issues Considered</h4>
                            <ul>
                              {msg.metadata.plan.potential_issues.map((issue, idx) => (
                                <li key={idx}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                // Simple message display
                <pre>{msg.content}</pre>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isProcessing ? "Agent is working..." : "Tell me what to do..."}
          disabled={isProcessing}
          className="command-input"
        />
        <button 
          type="submit" 
          disabled={isProcessing || !input.trim()}
          className="send-button"
        >
          {isProcessing ? '⏳' : '🚀'} {isProcessing ? 'Processing...' : 'Execute'}
        </button>
      </form>
    </div>
  );
}

export default IntelligentAssistant;


