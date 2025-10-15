import { useState, useEffect, useRef } from 'react';
import './IntelligentAssistant.css';

// Backend URL config: allow override via Vite env, fallback to localhost:5000
const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');
const BACKEND_WS = BACKEND_HTTP.replace(/^http/, 'ws') + '/ws';

function IntelligentAssistant() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [agentStatus, setAgentStatus] = useState({ agent: null, status: 'idle', progress: 0 });
  const [thinkingProcess, setThinkingProcess] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

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
      addMessage('system', '🤖 Connected to SIGMA-OS Intelligent Agent System');
      setBackendOnline(true);
      reconnectAttemptsRef.current = 0; // reset backoff
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'connection') {
        addMessage('system', `✅ ${data.message}\n📦 Available agents: ${data.agents.join(', ')}`);
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

  const addMessage = (type, content) => {
    setMessages(prev => [...prev, { 
      type, 
      content, 
      timestamp: new Date().toLocaleTimeString() 
    }]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userCommand = input.trim();
    setInput('');
    setIsProcessing(true);
    setThinkingProcess([]);

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
        addMessage('assistant', `✅ Task completed successfully!\n\n📊 Agent: ${data.agent_used}\n💭 Reasoning: ${data.thinking_process}\n\n${JSON.stringify(data.result, null, 2)}`);
      } else {
        addMessage('error', `❌ Task failed: ${data.result.error || 'Unknown error'}`);
      }
    } catch (error) {
      addMessage('error', `❌ Connection error: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setAgentStatus({ agent: null, status: 'idle', progress: 0 });
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
      </div>

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

      {/* Agent Status Panel */}
      {agentStatus.agent && (
        <div className={`agent-status ${agentStatus.status}`}>
          <div className="status-header">
            <span className="agent-name">🤖 {agentStatus.agent}</span>
            <span className="status-badge">{agentStatus.status}</span>
          </div>
          {agentStatus.message && (
            <div className="status-message">{agentStatus.message}</div>
          )}
          {agentStatus.progress > 0 && (
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${agentStatus.progress}%` }}
              />
              <span className="progress-text">{agentStatus.progress}%</span>
            </div>
          )}
        </div>
      )}

      {/* Thinking Process Panel */}
      {thinkingProcess.length > 0 && (
        <div className="thinking-panel">
          <h3>🧠 Agent Thinking Process</h3>
          <div className="thinking-items">
            {thinkingProcess.map((item, idx) => (
              <div key={idx} className={`thinking-item ${item.type}`}>
                <span className="thinking-agent">{item.agent}</span>
                <span className="thinking-message">{item.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>👋 Welcome to SIGMA-OS</h2>
            <p>Your intelligent AI assistant powered by Google Gemini</p>
            <div className="example-commands">
              <h3>Try these commands:</h3>
              <ul>
                <li>📧 "Send an email to test@example.com about project update"</li>
                <li>📁 "Create a new file called notes.txt with my meeting notes"</li>
                <li>🌐 "Search Google for latest AI news"</li>
                <li>📊 "List all files in the current directory"</li>
                <li>🖼️ "Take a screenshot"</li>
              </ul>
            </div>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
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
              <pre>{msg.content}</pre>
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
