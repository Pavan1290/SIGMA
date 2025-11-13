import { useState, useEffect } from 'react'
import IntelligentAssistant from './components/IntelligentAssistant'
import './App.css'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [theme, setTheme] = useState('dark')
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <div className={`app-container theme-${theme} ${!isOnline ? 'offline' : ''}`}>
      {/* Network Status Indicator */}
      {!isOnline && (
        <div className="network-status-bar">
          <div className="status-indicator offline"></div>
          <span>You are offline - some features may be unavailable</span>
        </div>
      )}

      {/* Main Application */}
      <IntelligentAssistant 
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        theme={theme}
        setTheme={setTheme}
      />
    </div>
  )
}

export default App
