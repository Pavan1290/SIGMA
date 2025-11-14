import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Disable StrictMode to prevent double-mounting WebSocket connections in dev
createRoot(document.getElementById('root')).render(
  <App />
)
