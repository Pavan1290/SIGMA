import React, { useState } from 'react';
import './AvailablePromptsModal.css';

// SVG Icons for categories
const categoryIcons = {
  system: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5"/>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5"/>
    </svg>
  ),
  files: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="13 2 13 9 20 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  network: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="1" fill="currentColor"/>
      <circle cx="19" cy="12" r="1" fill="currentColor"/>
      <circle cx="5" cy="12" r="1" fill="currentColor"/>
      <path d="M15 12h4M5 12h4M12 12v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  development: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polyline points="16 18 22 12 16 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="8 6 2 12 8 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  security: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L2 6v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-10-4z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  automation: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="7.5 4.21 12 6.81 16.5 4.21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  productivity: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="9" y1="9" x2="15" y2="9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="9" y1="15" x2="15" y2="15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
};

const AvailablePromptsModal = ({ isOpen, onClose, onSelectCommand, theme }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');

  // Comprehensive command list organized by category
  const commandCategories = {
    system: {
      name: 'System Information',
      icon: categoryIcons.system,
      commands: [
        { name: 'system info', description: 'Get complete system information' },
        { name: 'cpu usage', description: 'Monitor CPU usage and processes' },
        { name: 'memory usage', description: 'Check RAM and memory allocation' },
        { name: 'disk space', description: 'View disk storage information' },
        { name: 'running processes', description: 'List all active processes' },
        { name: 'installed software', description: 'Show all installed applications' },
        { name: 'system performance', description: 'Get detailed performance metrics' },
        { name: 'network info', description: 'Display network configuration' },
      ]
    },
    files: {
      name: 'File Management',
      icon: categoryIcons.files,
      commands: [
        { name: 'list files', description: 'Show all files in current directory' },
        { name: 'create file', description: 'Create a new file' },
        { name: 'delete file', description: 'Remove a file' },
        { name: 'rename file', description: 'Change file name' },
        { name: 'find files', description: 'Search for specific files' },
        { name: 'recent files', description: 'Show recently modified files' },
        { name: 'backup files', description: 'Create backup of important files' },
        { name: 'file permissions', description: 'Manage file access permissions' },
      ]
    },
    network: {
      name: 'Network & Connectivity',
      icon: categoryIcons.network,
      commands: [
        { name: 'ping server', description: 'Check network connectivity' },
        { name: 'check internet', description: 'Test internet connection' },
        { name: 'dns lookup', description: 'Resolve domain names' },
        { name: 'download file', description: 'Fetch files from the internet' },
        { name: 'port scanner', description: 'Scan for open network ports' },
        { name: 'ip address', description: 'Show current IP address' },
        { name: 'network speed', description: 'Test network bandwidth' },
        { name: 'wifi status', description: 'Check WiFi connection details' },
      ]
    },
    development: {
      name: 'Development & Code',
      icon: categoryIcons.development,
      commands: [
        { name: 'git status', description: 'Check git repository status' },
        { name: 'compile code', description: 'Compile source code' },
        { name: 'run tests', description: 'Execute unit tests' },
        { name: 'deploy app', description: 'Deploy application' },
        { name: 'build project', description: 'Build project distribution' },
        { name: 'debug code', description: 'Start debugging session' },
        { name: 'npm install', description: 'Install project dependencies' },
        { name: 'version check', description: 'Display software versions' },
      ]
    },
    security: {
      name: 'Security & Monitoring',
      icon: categoryIcons.security,
      commands: [
        { name: 'scan security', description: 'Run security scan' },
        { name: 'check updates', description: 'Look for security updates' },
        { name: 'firewall status', description: 'Check firewall settings' },
        { name: 'ssl certificate', description: 'Verify SSL certificates' },
        { name: 'password strength', description: 'Analyze password security' },
        { name: 'audit logs', description: 'Review system audit logs' },
        { name: 'backup verification', description: 'Verify backup integrity' },
        { name: 'antivirus scan', description: 'Run malware scan' },
      ]
    },
    automation: {
      name: 'Automation & Tasks',
      icon: categoryIcons.automation,
      commands: [
        { name: 'schedule task', description: 'Create scheduled task' },
        { name: 'batch process', description: 'Process multiple files' },
        { name: 'sync folders', description: 'Synchronize directories' },
        { name: 'cleanup temporary files', description: 'Remove temp files' },
        { name: 'generate report', description: 'Create automated report' },
        { name: 'send notification', description: 'Send system notification' },
        { name: 'monitor service', description: 'Track service health' },
        { name: 'auto update', description: 'Configure auto-updates' },
      ]
    },
    productivity: {
      name: 'Productivity Tools',
      icon: categoryIcons.productivity,
      commands: [
        { name: 'todo list', description: 'Manage tasks and todos' },
        { name: 'calendar events', description: 'View upcoming events' },
        { name: 'note taking', description: 'Create and organize notes' },
        { name: 'time tracking', description: 'Track time spent on tasks' },
        { name: 'reminder set', description: 'Set reminders' },
        { name: 'clipboard history', description: 'View recent clipboard items' },
        { name: 'document convert', description: 'Convert documents' },
        { name: 'email check', description: 'Check email notifications' },
      ]
    },
  };

  // Flatten all commands for search
  const allCommands = Object.entries(commandCategories).flatMap(([key, category]) =>
    category.commands.map(cmd => ({ ...cmd, category: key, categoryName: category.name }))
  );

  // Filter commands based on search query and active category
  const filteredCommands = allCommands.filter(cmd => {
    const matchesSearch = cmd.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         cmd.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = activeCategory === 'all' || cmd.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  if (!isOpen) return null;

  return (
    <div className="prompts-modal-overlay" onClick={onClose}>
      <div className={`prompts-modal prompts-modal-${theme}`} onClick={e => e.stopPropagation()}>
        {/* Header Section */}
        <div className="prompts-modal-header">
          <div className="prompts-header-content">
            <h1 className="prompts-title">More Prompts</h1>
            <p className="prompts-subtitle">SIGMA-OS can perform many more tasks - these are just some of them</p>
          </div>
          <button 
            className="prompts-modal-close" 
            onClick={onClose}
            title="Close"
            aria-label="Close modal"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        {/* Search and Filter Section */}
        <div className="search-filter-section">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search commands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
              <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>

          <div className="category-filters">
            <button
              className={`filter-btn ${activeCategory === 'all' ? 'active' : ''}`}
              onClick={() => setActiveCategory('all')}
            >
              All Commands
            </button>
            {Object.entries(commandCategories).map(([key, category]) => (
              <button
                key={key}
                className={`filter-btn ${activeCategory === key ? 'active' : ''}`}
                onClick={() => setActiveCategory(key)}
              >
                <span>{category.icon}</span> {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* Commands List Section */}
        <div className="commands-list-section">
          {filteredCommands.length === 0 ? (
            <div className="no-results">
              <p>No commands found matching your search.</p>
            </div>
          ) : (
            <div className="commands-grid">
              {filteredCommands.map((cmd, idx) => (
                <div 
                  key={idx}
                  className="command-card"
                  onClick={() => {
                    onSelectCommand(cmd.name);
                    onClose();
                  }}
                >
                  <div className="command-header">
                    <code className="command-name">"{cmd.name}"</code>
                    <span className="command-category">{commandCategories[cmd.category].icon}</span>
                  </div>
                  <p className="command-description">{cmd.description}</p>
                  <div className="command-footer">
                    <span className="command-category-label">{cmd.categoryName}</span>
                    <span className="command-usage">Click to use</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AvailablePromptsModal;
