import { useState } from 'react'
import IntelligentAssistant from './components/IntelligentAssistant'
import AdvancedDashboard from './components/AdvancedDashboard'
import AgentMemoryVisualizer from './components/AgentMemoryVisualizer'
import ReasoningEvaluator from './components/ReasoningEvaluator'
import RealtimeAnalytics from './components/RealtimeAnalytics'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'assistant', label: '💬 AI Assistant' },
    { id: 'dashboard', label: '📊 Dashboard' },
    { id: 'memory', label: '🧠 Memory' },
    { id: 'reasoning', label: '🧩 Reasoning' },
    { id: 'analytics', label: '📉 Analytics' },
  ]

  return (
    <div className="App">
      {/* Tab Navigation - SIMPLE AND CLEAR */}
      <nav className="app-nav">
        <div className="nav-brand">
          <span className="brand-icon">⚡</span>
          <h1>SIGMA-OS v2.0</h1>
        </div>

        <div className="nav-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          Connected
        </div>
      </nav>

      {/* Main Content - CLEAN DISPLAY */}
      <main className="app-content">
        {activeTab === 'assistant' && <IntelligentAssistant />}
        {activeTab === 'dashboard' && <AdvancedDashboard />}
        {activeTab === 'memory' && <AgentMemoryVisualizer />}
        {activeTab === 'reasoning' && <ReasoningEvaluator />}
        {activeTab === 'analytics' && <RealtimeAnalytics />}
      </main>
    </div>
  )
}

export default App
