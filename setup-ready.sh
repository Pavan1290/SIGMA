#!/bin/bash

# SIGMA-OS Complete Startup Script

echo "╔══════════════════════════════════════╗"
echo "║  SIGMA-OS - Professional UI Ready    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
  echo "❌ Error: package.json not found"
  echo "Please run this script from /home/zeb/Desktop/SIGMA-OS"
  exit 1
fi

# Display project structure
echo "✅ Project Structure:"
echo "   - Backend: Python FastAPI on port 5000"
echo "   - Frontend: React + Vite on port 5173"
echo "   - Components: Professional UI (no emojis)"
echo ""

# Check dependencies
echo "📦 Checking dependencies..."

if ! command -v node &> /dev/null; then
  echo "❌ Node.js not found. Please install Node.js"
  exit 1
fi

if ! command -v npm &> /dev/null; then
  echo "❌ npm not found. Please install npm"
  exit 1
fi

if ! command -v python3 &> /dev/null; then
  echo "❌ Python3 not found. Please install Python3"
  exit 1
fi

echo "✅ All dependencies found"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm packages..."
  npm install --silent
  echo "✅ npm packages installed"
else
  echo "✅ npm packages already installed"
fi
echo ""

# Display startup options
echo "🚀 Ready to start SIGMA-OS"
echo ""
echo "Option 1: Run both backend and frontend"
echo "   bash start.sh"
echo ""
echo "Option 2: Run only backend"
echo "   python3 backend/app.py"
echo ""
echo "Option 3: Run only frontend"
echo "   npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
echo ""
echo "📝 Before running, setup your API keys in .env file:"
echo "   - GOOGLE_API_KEY"
echo "   - OPENAI_API_KEY"
echo "   - GROQ_API_KEY"
echo "   - ANTHROPIC_API_KEY"
echo ""
echo "✅ Setup complete! Everything is ready."
