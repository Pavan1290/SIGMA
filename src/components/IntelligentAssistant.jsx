import { useState, useEffect, useRef } from 'react';
import './IntelligentAssistant.css';
import ModelSelector from './ModelSelector';
import VoiceListeningModal from './VoiceListeningModal';

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
  const [currentTheme, setCurrentTheme] = useState('teal'); // NEW: Theme system
  const [showThemeSelector, setShowThemeSelector] = useState(false); // NEW: Theme selector visibility
  const [isVoiceSupported] = useState(typeof (window.SpeechRecognition || window.webkitSpeechRecognition) !== 'undefined');
  const [isVoiceListening, setIsVoiceListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceIsFinal, setVoiceIsFinal] = useState(false);
  // Saved chats / UI controls
  const [archivedChats, setArchivedChats] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const recognitionRef = useRef(null);
  const voiceTimeoutRef = useRef(null);

  // Fetch current models on mount and when selector closes
  useEffect(() => {
    fetchCurrentModels();
  }, [showModelSelector]);

  // Voice recognition initialization
  useEffect(() => {
    if (!isVoiceSupported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsVoiceListening(true);
      setVoiceTranscript('');
      // Clear any existing timeout
      if (voiceTimeoutRef.current) clearTimeout(voiceTimeoutRef.current);
    };

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }

      const fullTranscript = final || interim;
      setVoiceTranscript(fullTranscript.trim());
      setVoiceIsFinal(!!final);

      // Reset timeout on new speech
      if (voiceTimeoutRef.current) clearTimeout(voiceTimeoutRef.current);

      // Auto-close after 3 seconds of silence
      voiceTimeoutRef.current = setTimeout(() => {
        handleVoiceEnd();
      }, 3000);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
    };

    recognition.onend = () => {
      setIsVoiceListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (voiceTimeoutRef.current) {
        clearTimeout(voiceTimeoutRef.current);
      }
    };
  }, [isVoiceSupported]);

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

  // --- Chat management: new chat, clear with confirmation, archive restore/delete ---
  const handleNewChat = () => {
    // Save old chat if there's content
    if (messages.length > 0) {
      const title = `Chat - ${new Date().toLocaleString()}`;
      const id = Date.now() + Math.random();
      setArchivedChats(prev => [{ id, title, messages: messages.slice(), timestamp: Date.now() }, ...prev]);
      setShowSidebar(true);
    }
    // Reset UI state for a fresh chat
    setMessages([]);
    setIsProcessing(false);
    setAgentStatus({ agent: null, status: 'idle', progress: 0 });
    setCurrentTask(null);
  };

  const requestClearChat = () => {
    // show confirmation modal to avoid accidental clear
    setShowClearConfirm(true);
  };

  const confirmClearChat = () => {
    setMessages([]);
    setIsProcessing(false);
    setAgentStatus({ agent: null, status: 'idle', progress: 0 });
    setCurrentTask(null);
    setShowClearConfirm(false);
  };

  const cancelClearChat = () => {
    setShowClearConfirm(false);
  };

  const handleRestoreChat = (chatId) => {
    const chat = archivedChats.find(c => c.id === chatId);
    if (!chat) return;
    setMessages(chat.messages.slice());
    // remove from archive after restoring
    setArchivedChats(prev => prev.filter(c => c.id !== chatId));
    setShowSidebar(false);
  };

  const handleDeleteArchived = (chatId) => {
    setArchivedChats(prev => prev.filter(c => c.id !== chatId));
  };

  const handleVoiceStart = () => {
    if (!recognitionRef.current) return;
    setVoiceTranscript('');
    setVoiceIsFinal(false);
    recognitionRef.current.start();
  };

  const handleVoiceEnd = () => {
    if (!recognitionRef.current) return;
    recognitionRef.current.stop();

    // Process transcript
    if (voiceTranscript.trim()) {
      const triggerPhrase = 'ok sigma send';
      const normalizedTranscript = voiceTranscript.toLowerCase();

      if (normalizedTranscript.includes(triggerPhrase)) {
        // Auto-execute: remove trigger phrase and execute
        const command = normalizedTranscript.replace(triggerPhrase, '').trim();
        if (command) {
          setInput(command);
          // We'll need to trigger submit after setting input
          setTimeout(() => {
            const formElement = document.querySelector('.input-form-modern');
            if (formElement) formElement.dispatchEvent(new Event('submit', { bubbles: true }));
          }, 0);
        }
      } else {
        // Just fill the input field
        setInput(voiceTranscript);
      }
    }

    setIsVoiceListening(false);
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

  const handleTerminate = () => {
    console.log('🛑 Terminating current task...');
    // Reset processing state
    setIsProcessing(false);
    setAgentStatus({ agent: null, status: 'idle', progress: 0 });
    setCurrentTask(null);
    addMessage('system', '🛑 Task terminated by user');
    
    // TODO: Send termination signal to backend via WebSocket if needed
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'terminate' }));
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Theme definitions with professional gradients
  const themes = {
    teal: { name: '🌊 Ocean Teal', emoji: '🌊', colors: ['#0a192f', '#1a2332', '#0f1419'] },
    purple: { name: '🌌 Cosmic Purple', emoji: '🌌', colors: ['#0f0c29', '#302b63', '#24243e'] },
    rose: { name: '🌹 Rose Gold', emoji: '🌹', colors: ['#2d1b3d', '#3d2a4f', '#1f1228'] },
    forest: { name: '🌲 Forest Green', emoji: '🌲', colors: ['#0a1f1a', '#1a2f27', '#0f1914'] },
    sunset: { name: '🌅 Sunset Orange', emoji: '🌅', colors: ['#1f1108', '#2f2414', '#191008'] },
    midnight: { name: '🌙 Midnight Blue', emoji: '🌙', colors: ['#0a0e27', '#1a1e3f', '#0f1219'] },
    ember: { name: '🔥 Ember Red', emoji: '🔥', colors: ['#1a0a0a', '#2a1414', '#140808'] }
  };

  const toggleThemeSelector = () => setShowThemeSelector(!showThemeSelector);
  const selectTheme = (theme) => {
    setCurrentTheme(theme);
    setShowThemeSelector(false);
    // Apply theme to root
    document.documentElement.setAttribute('data-theme', theme);
  };

  return (
    <div className={`intelligent-assistant ${showSidebar ? 'panel-open' : 'panel-closed'}`} data-theme={currentTheme}>
      {/* Theme Switcher Button - Top Right Corner */}
      <button 
        className="theme-switcher-button"
        onClick={toggleThemeSelector}
        title="Change Theme"
      >
        {themes[currentTheme].emoji}
      </button>

      {/* Chat panel toggle for mobile */}
      <button
        className="chat-toggle-button"
        onClick={() => setShowSidebar(true)}
        title="Open chats"
      >
        💬
      </button>

      {/* Small open-tab shown when panel is closed (desktop/tablet) */}
      <button
        className="chat-open-tab"
        onClick={() => setShowSidebar(true)}
        title="Open chats"
        aria-label="Open chats"
      >
        💬
      </button>

      {/* Chat panel (left) - visible on wide screens, collapsible on mobile */}
      <aside className={`chat-panel ${showSidebar ? 'open' : ''}`}>
        <div className="chat-panel-header">
          <h3>Chats</h3>
          <button className="chat-panel-close" onClick={() => setShowSidebar(false)}>✕</button>
        </div>

        <div className="chat-panel-controls">
          <button className="new-chat-button" onClick={handleNewChat} title="Start New Chat (saves current)">➕ New Chat</button>
          <button className="clear-chat-button" onClick={requestClearChat} title="Clear current chat">🗑️ Clear</button>
        </div>

        <div className="current-chat-meta">
          <div className="current-chat-title">Current Conversation</div>
          <div className="current-chat-count">{messages.length} messages</div>
        </div>

        <div className="saved-chats-list">
          <h4>Saved Chats</h4>
          {archivedChats.length === 0 ? (
            <div className="empty-archive">No saved chats</div>
          ) : (
            <div className="archive-list">
              {archivedChats.map(chat => (
                <div key={chat.id} className="chat-card">
                  <div className="chat-card-title">{chat.title}</div>
                  <div className="chat-card-meta">{new Date(chat.timestamp).toLocaleString()}</div>
                  <div className="chat-card-actions">
                    <button onClick={() => handleRestoreChat(chat.id)}>Restore</button>
                    <button onClick={() => handleDeleteArchived(chat.id)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Theme Selector Panel */}
      {showThemeSelector && (
        <div className="theme-selector-panel">
          <div className="theme-selector-header">
            <h3>🎨 Choose Your Theme</h3>
            <button className="close-theme-selector" onClick={() => setShowThemeSelector(false)}>✕</button>
          </div>
          <div className="theme-options">
            {Object.entries(themes).map(([key, theme]) => (
              <button
                key={key}
                className={`theme-option ${currentTheme === key ? 'active' : ''}`}
                onClick={() => selectTheme(key)}
                style={{
                  background: `linear-gradient(135deg, ${theme.colors[0]}, ${theme.colors[1]}, ${theme.colors[2]})`
                }}
              >
                <span className="theme-emoji">{theme.emoji}</span>
                <span className="theme-name">{theme.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="header">
        <h1 className="logo-text">
          <span className="logo-letter">S</span>
          <span className="logo-letter">I</span>
          <span className="logo-letter">G</span>
          <span className="logo-letter">M</span>
          <span className="logo-letter">A</span>
          <span className="logo-dash">-</span>
          <span className="logo-letter">O</span>
          <span className="logo-letter">S</span>
        </h1>
        <p className="subtitle">
          <span className="subtitle-word">Intelligent</span>{' '}
          <span className="subtitle-word">AI</span>{' '}
          <span className="subtitle-word">Agent</span>{' '}
          <span className="subtitle-word">System</span>
        </p>
        <div className="header-controls">
          {currentModels.thinking && (
            <div className="current-model-display">
              <span className="model-label">⚡ Active:</span>
              <span className="model-value">{currentModels.thinking}</span>
            </div>
          )}
          <button 
            className="model-selector-button"
            onClick={() => setShowModelSelector(true)}
            title="Change AI Model"
          >
            <span className="model-button-icon">🤖</span>
            <span className="model-button-text">AI Models</span>
          </button>
        </div>
      </div>

      {/* Model Selector Modal */}
      <ModelSelector 
        isOpen={showModelSelector} 
        onClose={() => setShowModelSelector(false)} 
      />

      {/* Saved Chats Sidebar */}
      {showSidebar && (
        <aside className="chat-sidebar">
          <div className="sidebar-header">
            <h3>Saved Chats</h3>
            <button onClick={() => setShowSidebar(false)}>✕</button>
          </div>
          {archivedChats.length === 0 ? (
            <div className="empty-archive">No saved chats</div>
          ) : (
            <div className="archive-list">
              {archivedChats.map(chat => (
                <div key={chat.id} className="chat-card">
                  <div className="chat-card-title">{chat.title}</div>
                  <div className="chat-card-meta">{new Date(chat.timestamp).toLocaleString()}</div>
                  <div className="chat-card-actions">
                    <button onClick={() => handleRestoreChat(chat.id)}>Restore</button>
                    <button onClick={() => handleDeleteArchived(chat.id)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>
      )}

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

      {/* Input Form with Modern Design */}
      <form onSubmit={handleSubmit} className="input-form-modern">
        <div className="input-container">
          <div className="input-wrapper">
            <svg className="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isProcessing ? "Agent is executing your command..." : "What would you like me to do?"}
              disabled={isProcessing}
              className="command-input-modern"
            />
            {!isProcessing && isVoiceSupported && (
              <button 
                type="button" 
                onClick={handleVoiceStart}
                className={`voice-button ${isVoiceListening ? 'recording' : ''}`}
                aria-label="Voice input"
                title="Click to start voice input"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 1C6.48 1 2 5.48 2 11V23h4v-8h4v8h4v-8h4v8h4V11c0-5.52-4.48-10-10-10zm0 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z" fill="currentColor"/>
                </svg>
              </button>
            )}
            {input && !isProcessing && (
              <button 
                type="button" 
                onClick={() => setInput('')}
                className="clear-button"
                aria-label="Clear input"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            )}
          </div>
          
          {isProcessing ? (
            <button 
              type="button"
              onClick={handleTerminate}
              className="terminate-button"
              aria-label="Terminate execution"
            >
              <svg className="button-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="6" y="6" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
              </svg>
              <span className="button-text">Terminate</span>
              <span className="button-glow"></span>
            </button>
          ) : (
            <button 
              type="submit" 
              disabled={!input.trim()}
              className="execute-button"
              aria-label="Execute command"
            >
              <svg className="button-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 3L19 12L5 21V3Z" fill="currentColor"/>
              </svg>
              <span className="button-text">Execute</span>
              <span className="button-glow"></span>
            </button>
          )}
        </div>
        
        {/* Character count and status indicators */}
        <div className="input-footer">
          <div className="input-stats">
            <span className="char-count">{input.length} characters</span>
            {input.length > 500 && (
              <span className="warning-badge">Long command - consider breaking into steps</span>
            )}
          </div>
          <div className="connection-indicator">
            <span className={`status-dot ${backendOnline ? 'online' : 'offline'}`}></span>
            <span className="status-text">{backendOnline ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </form>

      {/* Voice Listening Modal */}
      <VoiceListeningModal 
        isOpen={isVoiceListening}
        transcript={voiceTranscript}
        isFinal={voiceIsFinal}
        onClose={handleVoiceEnd}
      />

      {/* Clear confirmation modal */}
      {showClearConfirm && (
        <div className="confirm-modal-overlay">
          <div className="confirm-modal">
            <h3>Confirm Clear Chat</h3>
            <p>Are you sure you want to clear the current chat? This action cannot be undone.</p>
            <div className="confirm-actions">
              <button className="btn-cancel" onClick={cancelClearChat}>Cancel</button>
              <button className="btn-confirm" onClick={confirmClearChat}>Yes, Clear</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IntelligentAssistant;


