#!/bin/bash

echo "🛑 Stopping SIGMA-OS..."

# Kill all processes
pkill -9 -f "backend/app.py"
pkill -9 -f "vite"
pkill -9 -f "npm"

echo "✅ All services stopped"
