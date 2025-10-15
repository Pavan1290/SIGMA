#!/bin/bash

echo "🚀 Setting up SIGMA-OS Intelligent Agent System..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📥 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Optional: Check for tkinter (needed by pyautogui's MouseInfo on Linux)
if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
try:
    import tkinter  # noqa: F401
    print("✅ tkinter detected")
except Exception:
    print("⚠️  tkinter not found. On Debian/Ubuntu: sudo apt-get install -y python3-tk python3-dev")
PY
fi

echo ""
echo "📎 Note: If Playwright fails due to missing system libraries on Linux, run:"
echo "    npx playwright install --with-deps chromium"
echo "(This may prompt for sudo to install apt packages.)"

# Install frontend dependencies
echo "🎨 Installing frontend dependencies..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your .env file has GOOGLE_API_KEY"
echo "2. (Optional) For Gmail: Download credentials.json from Google Cloud Console"
echo "3. Run: ./start.sh"
echo ""
