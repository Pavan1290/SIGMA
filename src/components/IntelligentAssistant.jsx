import { useState, useEffect, useRef } from 'react';
import './IntelligentAssistant.css';
import AdvancedModelSelector from './AdvancedModelSelector';
import VoiceListeningModal from './VoiceListeningModal';
import AvailablePromptsModal from './AvailablePromptsModal';
import AdvancedAPIKeyManager from './AdvancedAPIKeyManager';
import SystemStatusModal from './SystemStatusModal';
import OutputRenderer from './OutputRenderer';

// Backend URL config: allow override via Vite env, fallback to localhost:5000
const BACKEND_HTTP = (import.meta?.env?.VITE_BACKEND_URL || 'http://localhost:5000').replace(/\/$/, '');
const BACKEND_WS = BACKEND_HTTP.replace(/^http/, 'ws') + '/ws';

const icons = {
  user: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M6 20c0-3.5 3-6 6-6s6 2.5 6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  assistant: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="5" y="7" width="14" height="10" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 17.5v0a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="10" cy="12" r="1.2" fill="currentColor" />
      <circle cx="14" cy="12" r="1.2" fill="currentColor" />
      <path d="M5 12H3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M21 12h-2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M12 5V3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  agent: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="5" cy="7" r="1.8" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="19" cy="7" r="1.8" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="5" cy="17" r="1.8" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="19" cy="17" r="1.8" stroke="currentColor" strokeWidth="1.4" />
      <path d="M10.5 9.5 6.7 7.6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M13.5 9.5 17.3 7.6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M10.5 14.5 6.7 16.4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M13.5 14.5 17.3 16.4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  ),
  system: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="8" r="0.8" fill="currentColor" />
      <path d="M12 11v6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  error: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8.5 8.5 15.5 15.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M15.5 8.5 8.5 15.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  success: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 12.5l3 3 5-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  thinking: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 4a5 5 0 0 1 5 5c0 2-1.2 3.7-3 4.5V15a2 2 0 0 1-2 2h0a2 2 0 0 1-2-2v-1.5C8.2 12.7 7 11 7 9a5 5 0 0 1 5-5z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10 19h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M10.5 21h3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  bolt: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M13 2 6 13h5l-1 9 7-11h-5Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  ),
  robot: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="6" y="6" width="12" height="12" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M9 6V4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M15 6V4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="10" cy="12" r="1.2" fill="currentColor" />
      <circle cx="14" cy="12" r="1.2" fill="currentColor" />
      <path d="M8 16h8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  key: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 11l8 8M17 16l-1 1M20 19l-1 1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  network: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4.5 10a12.6 12.6 0 0 1 15 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M7 13.5a7.5 7.5 0 0 1 10 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M9.5 17a3 3 0 0 1 5 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="12" cy="20" r="1" fill="currentColor" />
    </svg>
  ),
  realtime: (size = 20) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 5.5a6.5 6.5 0 1 1-6.2 8.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M12 3v2.5L9.5 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 9v4l2.5 1.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  folder: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M3 7h6l2 3h10v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  storage: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <ellipse cx="12" cy="7" rx="7" ry="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M5 7v10c0 1.66 3.13 3 7 3s7-1.34 7-3V7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M5 12c0 1.66 3.13 3 7 3s7-1.34 7-3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  document: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M7 3h7l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 3v6h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  camera: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7h3l1.5-2.5h7L17 7h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="13" r="3" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  ),
  clock: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  spark: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3l1.5 5h5l-4 3 1.5 5-4-3-4 3 1.5-5-4-3h5L12 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chevronDown: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chevronRight: (size = 14) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  target: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6" />
      <path d="M12 4v2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M12 18v2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M4 12h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M18 12h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  clipboard: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M16 4h1a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="8" y="2" width="8" height="4" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M9 10h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M9 14h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  wrench: (size = 16) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M21 3a4 4 0 0 0-5.66 5.66L6 17.99 3 21l3.01-3 9.33-9.34A4 4 0 0 0 21 3Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="7.5" cy="18.5" r="0.8" fill="currentColor" />
    </svg>
  ),
  alert: (size = 18) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 4 3 20h18L12 4Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M12 10v4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.8" fill="currentColor" />
    </svg>
  ),
};

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
  const [currentModels, setCurrentModels] = useState(() => {
    // Load from localStorage on mount
    try {
      const saved = localStorage.getItem('selectedModels');
      return saved ? JSON.parse(saved) : { thinking: null, execution: null };
    } catch (err) {
      return { thinking: null, execution: null };
    }
  }); // NEW: Track selected models - persistent
  const [currentTheme, setCurrentTheme] = useState('teal'); // NEW: Theme system
  const [showThemeSelector, setShowThemeSelector] = useState(false); // NEW: Theme selector visibility
  const [showPromptsModal, setShowPromptsModal] = useState(false); // NEW: Prompts modal state
  const [showAPIKeyManager, setShowAPIKeyManager] = useState(false); // NEW: API Key Manager state
  const [showSystemStatus, setShowSystemStatus] = useState(false); // System Status modal
  const [isVoiceSupported] = useState(typeof (window.SpeechRecognition || window.webkitSpeechRecognition) !== 'undefined');
  const [isVoiceListening, setIsVoiceListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceIsFinal, setVoiceIsFinal] = useState(false);
  // Saved chats / UI controls
  const [archivedChats, setArchivedChats] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [headerHidden, setHeaderHidden] = useState(false); // Track navbar visibility
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const recognitionRef = useRef(null);
  const voiceTimeoutRef = useRef(null);
  const voiceTranscriptRef = useRef('');
  const scrollTimeoutRef = useRef(null); // NEW: Timeout for auto-show navbar
  const messagesContainerRef = useRef(null); // NEW: Reference to scrollable container
  const lastScrollTimeRef = useRef(0); // NEW: Track last scroll time

  // Save models to localStorage whenever they change
  useEffect(() => {
    if (currentModels.thinking || currentModels.execution) {
      localStorage.setItem('selectedModels', JSON.stringify(currentModels));
      console.log('✅ Models saved:', currentModels);
    }
  }, [currentModels]);

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
      voiceTranscriptRef.current = '';
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

      // Build full transcript: accumulated final results + current interim
      const accumulatedFinal = voiceTranscriptRef.current;
      const displayTranscript = accumulatedFinal + (final ? final : interim);
      
      setVoiceTranscript(displayTranscript.trim());
      setVoiceIsFinal(!!final);

      // Only update ref with FINAL results
      if (final) {
        voiceTranscriptRef.current = accumulatedFinal + final;
      }

      // Clear previous timeout
      if (voiceTimeoutRef.current) clearTimeout(voiceTimeoutRef.current);

      // Auto-close after 3 seconds of silence (only if we have final text)
      if (final) {
        voiceTimeoutRef.current = setTimeout(() => {
          handleVoiceEnd();
        }, 3000);
      }
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
    
    // Check if already connecting or connected
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    try {
      const ws = new WebSocket(BACKEND_WS);
      
      ws.onopen = () => {
        console.log('✅ Connected to SIGMA-OS Agent System');
        setBackendOnline(true);
        reconnectAttemptsRef.current = 0; // reset backoff
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connection') {
            console.log('🔗 Connection confirmed:', data.message);
          } else if (data.agent_name) {
            // Agent update
            handleAgentUpdate(data);
          }
        } catch (parseError) {
          console.error('Failed to parse WebSocket message:', parseError);
        }
      };
      
      ws.onerror = (error) => {
        // Only log real errors, not React StrictMode test disconnects
        if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
          console.warn('WebSocket error (may be normal in dev mode)');
        }
        setBackendOnline(false);
      };
      
      ws.onclose = (event) => {
        // Only log if it's not a React StrictMode cleanup (code 1006 on first mount)
        if (event.code !== 1000 && reconnectAttemptsRef.current > 0) {
          console.log('⚠️  WebSocket disconnected, reconnecting...');
        }
        setBackendOnline(false);
        // Only reconnect if not a normal closure
        if (event.code !== 1000) {
          scheduleReconnect();
        }
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      scheduleReconnect();
    }
  };

  const scheduleReconnect = () => {
    // Exponential backoff with jitter
    const base = 1000; // 1s
    const max = 30000; // 30s
    const attempt = Math.min(reconnectAttemptsRef.current + 1, 10);
    reconnectAttemptsRef.current = attempt;
    const delay = Math.min(base * Math.pow(2, attempt - 1), max);
    const jitter = Math.random() * 250; // slight jitter
    const totalDelay = delay + jitter;
    
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    
    // Only log if this is a real reconnect attempt (not React StrictMode cleanup)
    if (attempt > 1) {
      console.log(`⏳ Reconnecting... (attempt ${attempt})`);
    }
    reconnectTimerRef.current = setTimeout(connectWebSocket, totalDelay);
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

    // NOTE: Don't add duplicate messages here - the main response handles it
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
    setIsVoiceListening(false);

    // Process transcript using ref (which has the current value)
    const transcript = voiceTranscriptRef.current.trim();
    
    if (transcript) {
      // Check for trigger phrases (case-insensitive)
      const normalizedTranscript = transcript.toLowerCase();
      const triggerPhrases = ['ok sigma send', 'okay sigma send', 'ok sigma', 'sigma send'];
      
      let shouldAutoExecute = false;
      let executedPhrase = '';
      
      for (const phrase of triggerPhrases) {
        if (normalizedTranscript.includes(phrase)) {
          shouldAutoExecute = true;
          executedPhrase = phrase;
          break;
        }
      }

      if (shouldAutoExecute) {
        // Auto-execute: remove trigger phrase and execute
        const command = transcript.replace(new RegExp(executedPhrase, 'i'), '').trim();
        if (command) {
          setInput(command);
          // Trigger submit after a tiny delay to ensure state updates
          setTimeout(() => {
            const formElement = document.querySelector('.input-form-modern');
            if (formElement) {
              formElement.dispatchEvent(new Event('submit', { bubbles: true }));
            }
          }, 50);
        }
      } else {
        // Just fill the input field - no auto-execute
        setInput(transcript);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    const userCommand = input.trim();
    setInput('');
    setIsProcessing(true);
    setHeaderHidden(true); // Hide navbar during task execution
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

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Extract formatted output from response
        const formattedOutput = data.result?.formatted_output || {
          type: 'text',
          success: true,
          content: 'Task completed successfully!',
          explanation: 'The task has been executed.'
        };

        // Create rich metadata for the task
        const metadata = {
          agent: data.agent_used || data.result?.agent_used || 'unknown',
          reasoning: data.thinking_process || data.result?.reasoning,
          plan: data.result?.plan || { understanding: 'Completed', approach: 'Using intelligent agents' },
          results: [{
            command: userCommand,
            output: formattedOutput.raw_output || formattedOutput.content || '',
            formatted_response: formattedOutput,
            success: data.success,
            exit_code: 0
          }],
          task: userCommand,
          success: true
        };

        // Add single comprehensive message with formatting
        addMessage('assistant', formattedOutput.explanation || 'Task completed successfully!', metadata);
      } else {
        const errorOutput = data.result?.formatted_output || {
          type: 'error',
          success: false,
          error_type: 'execution_error',
          message: data.result?.error || 'Unknown error occurred',
          details: data.result?.error,
          suggestions: ['Check command syntax', 'Verify backend is running'],
          raw_output: data.result?.error
        };

        const errorMetadata = {
          agent: data.agent_used || 'unknown',
          reasoning: data.thinking_process,
          results: [{
            command: userCommand,
            output: data.result?.error || '',
            formatted_response: errorOutput,
            success: false,
            exit_code: 1
          }],
          task: userCommand,
          success: false
        };

        addMessage('error', errorOutput.message, errorMetadata);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      
      const errorMetadata = {
        agent: null,
        reasoning: `Connection error: ${error.message}`,
        results: [{
          command: userCommand,
          output: error.message,
          formatted_response: {
            type: 'error',
            success: false,
            error_type: 'connection_error',
            message: `Connection error: ${error.message}`,
            details: error.message,
            suggestions: ['Check if backend is running on http://localhost:5000', 'Check your internet connection'],
            raw_output: error.message
          },
          success: false,
          exit_code: -1
        }],
        task: userCommand,
        success: false
      };

      addMessage('error', `Connection error: ${error.message}`, errorMetadata);
    } finally {
      setIsProcessing(false);
      // Keep navbar hidden after task completes
      setAgentStatus({ agent: null, status: 'idle', progress: 0 });
      setCurrentTask(null);
    }
  };

  const handleTerminate = () => {
  console.log('Terminating current task...');
    // Reset processing state - keep navbar hidden
    setIsProcessing(false);
    setAgentStatus({ agent: null, status: 'idle', progress: 0 });
    setCurrentTask(null);
  addMessage('system', 'Task terminated by user');
    
    // TODO: Send termination signal to backend via WebSocket if needed
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'terminate' }));
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Keep navbar hidden during task execution
  useEffect(() => {
    if (isProcessing) {
      setHeaderHidden(true);
    }
  }, [isProcessing]);

  // Theme definitions with professional gradients
  const themes = {
    teal: { name: 'Ocean Teal', colors: ['#0a192f', '#1a2332', '#0f1419'] },
    purple: { name: 'Cosmic Purple', colors: ['#0f0c29', '#302b63', '#24243e'] },
    rose: { name: 'Rose Gold', colors: ['#2d1b3d', '#3d2a4f', '#1f1228'] },
    forest: { name: 'Forest Green', colors: ['#0a1f1a', '#1a2f27', '#0f1914'] },
    sunset: { name: 'Sunset Orange', colors: ['#1f1108', '#2f2414', '#191008'] },
    midnight: { name: 'Midnight Blue', colors: ['#0a0e27', '#1a1e3f', '#0f1219'] },
    ember: { name: 'Ember Red', colors: ['#1a0a0a', '#2a1414', '#140808'] }
  };

  const toggleThemeSelector = () => setShowThemeSelector(!showThemeSelector);
  const selectTheme = (theme) => {
    setCurrentTheme(theme);
    setShowThemeSelector(false);
    // Apply theme to root
    document.documentElement.setAttribute('data-theme', theme);
  };

  const statusIcons = {
    thinking: icons.thinking(18),
    executing: icons.agent(18),
    success: icons.success(18),
    error: icons.error(18)
  };

  const renderMessageIcon = (type) => {
    switch (type) {
      case 'user':
        return icons.user(18);
      case 'assistant':
        return icons.assistant(18);
      case 'agent':
        return icons.agent(18);
      case 'system':
        return icons.system(18);
      case 'error':
        return icons.error(18);
      default:
        return icons.system(18);
    }
  };

  return (
    <div className={`intelligent-assistant ${showSidebar ? 'panel-open' : 'panel-closed'} ${headerHidden ? 'header-hidden' : ''}`} data-theme={currentTheme}>
      {/* Professional Sidebar Toggle Button - Top Left */}
      <button
        className={`chat-toggle-button ${showSidebar ? 'is-open' : ''}`}
        onClick={() => setShowSidebar(!showSidebar)}
        title={showSidebar ? "Close sidebar" : "Open sidebar"}
        aria-label="Toggle sidebar"
        aria-pressed={showSidebar}
      >
        <span className="hamburger-icon" aria-hidden="true">
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </span>
      </button>

      {/* Small tab on the left edge when panel closed (mirrors .chat-open-tab CSS) */}
      <button
        className="chat-open-tab"
        onClick={() => setShowSidebar(true)}
        aria-label="Open sidebar"
        title="Open sidebar"
      >
        <span className="hamburger-icon" aria-hidden="true">
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </span>
      </button>

      {/* Chat panel (left) - visible on wide screens, collapsible on mobile */}
      <aside className={`chat-panel ${showSidebar ? 'open' : ''}`}>
        <div className="chat-panel-header">
          <h3>Chats</h3>
          <div className="chat-panel-header-controls">
            <button 
              className="theme-switcher-button-sidebar"
              onClick={toggleThemeSelector}
              title="Change Theme"
              aria-label="Change theme"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2"/>
                <path d="M12 1v6M12 17v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M1 12h6M17 12h6M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
            <button className="chat-panel-close" onClick={() => setShowSidebar(false)} title="Close sidebar" aria-label="Close sidebar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div className="chat-panel-controls">
          <button className="new-chat-button" onClick={handleNewChat} title="Start New Chat (saves current)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: '8px'}}>
              <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            New Chat
          </button>
          <button className="clear-chat-button" onClick={requestClearChat} title="Clear current chat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: '8px'}}>
              <path d="M3 6h18M8 6v12a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M10 11v6M14 11v6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Clear
          </button>
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

      {/* Navbar Expand Button - Appears when navbar is hidden */}
      {headerHidden && (
        <button
          className="navbar-expand-button"
          onClick={() => setHeaderHidden(false)}
          title="Show navbar"
        >
          <span className="inline-icon" aria-hidden="true">{icons.chevronDown(16)}</span>
          <span>Show Navbar</span>
        </button>
      )}

      {/* Theme Selector Panel */}
      {showThemeSelector && (
        <div className="theme-selector-panel">
          <div className="theme-selector-header">
            <h3>Choose Your Theme</h3>
            <button className="close-theme-selector" onClick={() => setShowThemeSelector(false)} aria-label="Close theme selector">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
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
                <span
                  className="theme-swatch"
                  aria-hidden="true"
                  style={{ background: `linear-gradient(135deg, ${theme.colors[0]}, ${theme.colors[1]}, ${theme.colors[2]})` }}
                />
                <span className="theme-name">{theme.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="header">
        <div className="header-top">
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
        </div>

        <div className="header-bottom">
          {currentModels.thinking && (
            <div className="current-model-display">
              <span className="model-label-icon" aria-hidden="true">{icons.bolt(12)}</span>
              <span className="model-label-text">Active:</span>
              <span className="model-value">{currentModels.thinking}</span>
            </div>
          )}
          <button 
            className="system-status-button"
            onClick={() => setShowSystemStatus(true)}
            title="View System Status"
          >
            <span className="status-indicator">●</span>
            <span className="status-text">System</span>
          </button>
        </div>
      </div>

      {/* Floating Control Buttons - Top Right */}
      <div className="floating-controls right">
        <button 
          className="floating-button models-button"
          onClick={() => setShowModelSelector(true)}
          title="Change AI Model"
        >
          <span className="floating-icon" aria-hidden="true">{icons.robot(14)}</span>
          <span className="floating-label">Models</span>
        </button>
        <button 
          className="floating-button keys-button"
          onClick={() => setShowAPIKeyManager(true)}
          title="Manage API Keys"
        >
          <span className="floating-icon" aria-hidden="true">{icons.key(14)}</span>
          <span className="floating-label">Keys</span>
        </button>
      </div>

      {/* Advanced Model Selector Modal */}
      <AdvancedModelSelector 
        isOpen={showModelSelector} 
        onClose={() => setShowModelSelector(false)}
        onModelSelect={(models) => {
          console.log('✅ Models selected:', models);
          setCurrentModels(models);
          fetchCurrentModels();
        }}
        currentModels={currentModels}
      />

      {/* Advanced API Key Manager Modal */}
      <AdvancedAPIKeyManager 
        isOpen={showAPIKeyManager}
        onClose={() => {
          setShowAPIKeyManager(false);
          // Refresh models after closing
          fetchCurrentModels();
        }}
        onVerified={() => {
          console.log('✅ API key verified');
          fetchCurrentModels();
        }}
      />

      {/* System Status Modal */}
      <SystemStatusModal 
        isOpen={showSystemStatus}
        onClose={() => setShowSystemStatus(false)}
        selectedModels={currentModels}
        isConnected={backendOnline}
      />

      {/* Backend connectivity banner */}
      {!backendOnline && (
        <div className="agent-status error" style={{ margin: '0 1rem 1rem', borderLeft: '4px solid #ef4444' }}>
          <div className="status-header">
            <span className="agent-name">
              <span className="inline-icon" aria-hidden="true">{icons.network(16)}</span>
              Backend disconnected
            </span>
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
            <span className="compact-icon" aria-hidden="true">
              {statusIcons[agentStatus.status] || icons.system(18)}
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
      <div className="messages-container" ref={messagesContainerRef}>
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-header">
              <h2>
                <span className="inline-icon" aria-hidden="true">{icons.spark(20)}</span>
                Welcome to SIGMA-OS
              </h2>
              <p className="welcome-subtitle">Your intelligent AI agent system with multi-model support</p>
            </div>
            
            <div className="features-grid">
              <div className="feature-card">
                <span className="feature-icon" aria-hidden="true">{icons.assistant(28)}</span>
                <h3>Smart Agents</h3>
                <p>System, Email, and Web agents ready to help</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon" aria-hidden="true">{icons.network(28)}</span>
                <h3>Multi-Model AI</h3>
                <p>Switch between Gemini, Groq, and Ollama</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon" aria-hidden="true">{icons.realtime(28)}</span>
                <h3>Real-time</h3>
                <p>Live updates and intelligent task execution</p>
              </div>
              <div className="feature-card">
                <span className="feature-icon" aria-hidden="true">{icons.bolt(28)}</span>
                <h3>Lightning Fast</h3>
                <p>Instant responses and rapid task completion</p>
              </div>
            </div>

            <div className="example-commands">
              <h3>
                <span className="inline-icon" aria-hidden="true">{icons.spark(16)}</span>
                Try these commands:
              </h3>
              <ul>
                <li onClick={() => setInput("list files in my desktop")}>
                  <span className="inline-icon" aria-hidden="true">{icons.folder(18)}</span>
                  "list files in my desktop"
                </li>
                <li onClick={() => setInput("check disk space")}>
                  <span className="inline-icon" aria-hidden="true">{icons.storage(18)}</span>
                  "check disk space"
                </li>
                <li onClick={() => setInput("create a file called test.txt")}>
                  <span className="inline-icon" aria-hidden="true">{icons.document(18)}</span>
                  "create a file called test.txt"
                </li>
                <li onClick={() => setInput("take a screenshot")}>
                  <span className="inline-icon" aria-hidden="true">{icons.camera(18)}</span>
                  "take a screenshot"
                </li>
                <li onClick={() => setInput("what's the current time")}>
                  <span className="inline-icon" aria-hidden="true">{icons.clock(18)}</span>
                  "current time"
                </li>
                <li onClick={() => setInput("open file manager")}>
                  <span className="inline-icon" aria-hidden="true">{icons.folder(18)}</span>
                  "open file manager"
                </li>
                <li onClick={() => setInput("check system info")}>
                  <span className="inline-icon" aria-hidden="true">{icons.storage(18)}</span>
                  "system info"
                </li>
                <li onClick={() => setInput("search for *.txt files")}>
                  <span className="inline-icon" aria-hidden="true">{icons.document(18)}</span>
                  "search for *.txt files"
                </li>
                <li onClick={() => setInput("check network connectivity")}>
                  <span className="inline-icon" aria-hidden="true">{icons.network(18)}</span>
                  "network connectivity"
                </li>
                <li onClick={() => setInput("get CPU and memory usage")}>
                  <span className="inline-icon" aria-hidden="true">{icons.bolt(18)}</span>
                  "CPU and memory usage"
                </li>
              </ul>
              <button 
                className="available-prompts-button" 
                title="View more prompts"
                onClick={() => setShowPromptsModal(true)}
              >
                <span className="inline-icon" aria-hidden="true">{icons.spark(16)}</span>
                View More Prompts
              </button>
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
              <span className="message-icon" aria-hidden="true">{renderMessageIcon(msg.type)}</span>
              <span className="message-time">{msg.timestamp}</span>
            </div>
            <div className="message-content">
              {msg.type === 'assistant' && msg.metadata ? (
                // Rich task display with advanced output renderer
                <div className="task-result">
                  <div className="task-summary">
                    <h3>{msg.content}</h3>
                    <div className="task-meta">
                        <span className="meta-item">
                          <span className="inline-icon" aria-hidden="true">{icons.assistant(16)}</span>
                          Agent: <strong>{msg.metadata.agent}</strong>
                        </span>
                        <span className="meta-item">
                          <span className="inline-icon" aria-hidden="true">{icons.document(16)}</span>
                          Task: {msg.metadata.task}
                        </span>
                    </div>
                  </div>

                  {/* MAIN OUTPUT - Beautifully rendered with OutputRenderer */}
                  {msg.metadata.results && msg.metadata.results.length > 0 && (
                    <div className="main-output">
                      {msg.metadata.results.map((result, idx) => (
                        <div key={idx} className="output-item">
                          {/* Check if we have a formatted_response */}
                          {result.formatted_response ? (
                            <OutputRenderer response={result.formatted_response} command={result.command} />
                          ) : (
                            // Fallback to plain output
                            <>
                              {result.output && (
                                <pre className="output-text">{result.output}</pre>
                              )}
                              {result.command && !result.output && (
                                <div className="command-executed">
                                  <code>{result.command}</code>
                                  <span className={`status-indicator ${result.success ? 'success' : 'failed'}`}>
                                    <span className="inline-icon" aria-hidden="true">
                                      {result.success ? icons.success(14) : icons.error(14)}
                                    </span>
                                    {result.success ? 'Success' : 'Failed'}
                                  </span>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Expandable Details Section */}
                  <div className="task-expand-container">
                    <button 
                      className="expand-button"
                      onClick={() => toggleMessageExpanded(msg.id)}
                    >
                      <span className="inline-icon" aria-hidden="true">
                        {expandedMessages.has(msg.id) ? icons.chevronDown(12) : icons.chevronRight(12)}
                      </span>
                      {expandedMessages.has(msg.id) ? 'Hide Technical Details' : 'Show Technical Details'}
                    </button>

                    {expandedMessages.has(msg.id) && (
                      <div className="task-details">
                        {/* AI's Understanding */}
                        {msg.metadata.plan && (
                          <div className="detail-section">
                            <h4>
                              <span className="inline-icon" aria-hidden="true">{icons.thinking(16)}</span>
                              AI's Understanding
                            </h4>
                            <p>{msg.metadata.plan.understanding}</p>
                          </div>
                        )}

                        {/* Strategy */}
                        {msg.metadata.plan && (
                          <div className="detail-section">
                            <h4>
                              <span className="inline-icon" aria-hidden="true">{icons.target(16)}</span>
                              Strategy
                            </h4>
                            <p>{msg.metadata.plan.approach}</p>
                          </div>
                        )}

                        {/* Steps Executed */}
                        {msg.metadata.plan && msg.metadata.plan.steps && (
                          <div className="detail-section">
                            <h4>
                              <span className="inline-icon" aria-hidden="true">{icons.clipboard(16)}</span>
                              Steps Planned
                            </h4>
                            {msg.metadata.plan.steps.map((step, idx) => (
                              <div key={idx} className="step-item">
                                <div className="step-header">
                                  <span className="step-number">Step {step.step}</span>
                                  <span className="step-tool">
                                    <span className="inline-icon" aria-hidden="true">{icons.wrench(14)}</span>
                                    Tool: {step.tool}
                                  </span>
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
                            <h4>
                              <span className="inline-icon" aria-hidden="true">{icons.success(16)}</span>
                              What Actually Happened
                            </h4>
                            {msg.metadata.results.map((result, idx) => (
                              <div key={idx} className="execution-result">
                                <div className="result-header">
                                  <span className={`result-status ${result.success ? 'success' : 'failed'}`}>
                                    <span className="inline-icon" aria-hidden="true">
                                      {result.success ? icons.success(14) : icons.error(14)}
                                    </span>
                                    {result.success ? 'Success' : 'Failed'}
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
                            <h4>
                              <span className="inline-icon" aria-hidden="true">{icons.alert(16)}</span>
                              Potential Issues Considered
                            </h4>
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

      {/* Available Prompts Modal */}
      <AvailablePromptsModal 
        isOpen={showPromptsModal}
        onClose={() => setShowPromptsModal(false)}
        onSelectCommand={(command) => setInput(command)}
        theme={currentTheme}
      />

      {/* Clear confirmation modal */}
      {showClearConfirm && (
        <div className="confirm-modal-overlay">
          <div className="confirm-modal">
            <h3>Confirm Clear Chat</h3>
            <p>Are you sure you want to clear the current chat? This action cannot be undone.</p>
            <div className="confirm-actions">
              <button className="btn-cancel" onClick={cancelClearChat}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: '0.5rem'}}>
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Cancel
              </button>
              <button className="btn-confirm" onClick={confirmClearChat}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{marginRight: '0.5rem'}}>
                  <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Yes, Clear
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IntelligentAssistant;


