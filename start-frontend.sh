#!/usr/bin/env bash

# SIGMA-OS Frontend Enhancement - Quick Start Script
# This script helps you get started with the enhanced frontend

echo "🌟 SIGMA-OS Frontend Enhancement - Quick Start"
echo "=============================================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
fi

echo "✅ npm found: $(npm --version)"
echo ""

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Starting development server..."
echo "   → Application will open at http://localhost:5173"
echo ""
echo "📋 What to do:"
echo "   1. Wait for the server to start"
echo "   2. Open browser to http://localhost:5173"
echo "   3. Click through the 5 tabs in the navigation"
echo "   4. Explore each advanced component"
echo ""
echo "📚 Documentation:"
echo "   • FRONTEND_SUMMARY.md - Overview of new features"
echo "   • FRONTEND_ENHANCEMENT_GUIDE.md - Detailed integration guide"
echo ""

# Start the development server
npm run dev
