#!/bin/bash

echo "🚀 Starting SIGMA-OS Intelligent Agent System..."
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kill any existing processes on ports 5000, 5173, and 3001
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "backend/app.py" 2>/dev/null
pkill -9 -f "vite" 2>/dev/null
pkill -9 -f "puppeteer_server" 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
lsof -ti:3001 | xargs kill -9 2>/dev/null

sleep 1

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "📦 Please run ./setup.sh first"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found! Creating from template..."
    cp .env.example .env 2>/dev/null || touch .env
    echo "📝 Please add your API keys to .env file"
fi

# Start Puppeteer service for web automation
echo "🌐 Starting Puppeteer web automation service..."
if [ -f "puppeteer_service/puppeteer_server.cjs" ]; then
    node puppeteer_service/puppeteer_server.cjs 2>&1 | tee puppeteer.log &
    PUPPETEER_PID=$!
    echo "   Puppeteer PID: $PUPPETEER_PID"
    sleep 2
    
    # Check if Puppeteer started successfully
    if ! ps -p $PUPPETEER_PID > /dev/null; then
        echo "⚠️  Puppeteer service failed to start (optional feature)"
        echo "   Web automation may not be available"
        PUPPETEER_PID=""
    else
        echo "   ✅ Puppeteer service running on port 3001"
    fi
else
    echo "   ⚠️  Puppeteer service not found (optional)"
    PUPPETEER_PID=""
fi

# Start backend
echo "🔧 Starting backend server..."
source .venv/bin/activate

# Start backend with output to both terminal and log file
python -u backend/app.py 2>&1 | tee backend.log &
BACKEND_PID=$!

echo "   Backend PID: $BACKEND_PID"
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start! Check backend.log for errors"
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
npm run dev 2>&1 | tee frontend.log &
FRONTEND_PID=$!

echo "   Frontend PID: $FRONTEND_PID"
sleep 2

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Frontend failed to start! Check frontend.log for errors"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Trap Ctrl+C to cleanup
trap "echo ''; echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID $PUPPETEER_PID 2>/dev/null; pkill -9 -f 'backend/app.py' 2>/dev/null; pkill -9 -f 'vite' 2>/dev/null; pkill -9 -f 'puppeteer_server' 2>/dev/null; echo '✅ All services stopped'; exit 0" INT

echo ""
echo "✅ SIGMA-OS is running successfully!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:5000"
echo "📍 WebSocket: ws://localhost:5000/ws"
if [ -n "$PUPPETEER_PID" ]; then
    echo "📍 Puppeteer: http://localhost:3001"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "� BACKEND OUTPUT (Real-time):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Follow backend log in real-time (frontend runs silently in background)
tail -f backend.log
