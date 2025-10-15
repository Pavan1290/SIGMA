#!/bin/bash

echo "🚀 Starting SIGMA-OS Intelligent Agent System..."
echo ""

# Kill any existing processes
pkill -9 -f "app.py"
pkill -9 -f "vite"

# Start backend
echo "🔧 Starting backend..."
source .venv/bin/activate
python backend/app.py &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "🎨 Starting frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ SIGMA-OS is running!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend: http://localhost:5000"
echo "📍 WebSocket: ws://localhost:5000/ws"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; pkill -9 -f 'app.py'; pkill -9 -f 'vite'; echo '✅ All services stopped'; exit 0" INT

wait
