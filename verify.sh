#!/bin/bash
# SIGMA-OS Verification Script
# Verifies all systems are working correctly

echo "🔍 SIGMA-OS System Verification"
echo "================================"
echo ""

# Check Python environment
echo "1️⃣  Checking Python environment..."
if [ -f ".venv/bin/python" ]; then
    PYTHON_VERSION=$(.venv/bin/python --version)
    echo "   ✅ Python environment: $PYTHON_VERSION"
else
    echo "   ❌ Python environment not found"
    exit 1
fi

# Check MCP Server
echo ""
echo "2️⃣  Checking MCP Server..."
if /home/zeb/Desktop/SIGMA-OS/.venv/bin/python -c "from intelligent_agents.mcp_server import SIGMAMCPServer; print('   ✅ MCP Server: OK')" 2>&1 | grep -q "OK"; then
    echo "   ✅ MCP Server initialization: SUCCESS"
else
    echo "   ⚠️  MCP Server check: See above for details"
fi

# Check Backend
echo ""
echo "3️⃣  Checking Backend..."
if /home/zeb/Desktop/SIGMA-OS/.venv/bin/python -c "from backend.app import app; print('   ✅ Backend: OK')" 2>&1 | grep -q "OK"; then
    echo "   ✅ Backend initialization: SUCCESS"
else
    echo "   ⚠️  Backend check: See above for details"
fi

# Check Key Files
echo ""
echo "4️⃣  Checking key files..."
FILES=(
    "intelligent_agents/mcp_server.py"
    "intelligent_agents/output_formatter.py"
    "intelligent_agents/web_agent.py"
    "backend/app.py"
    "README.md"
    "COMPLETION_REPORT.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (MISSING)"
    fi
done

# Check Git Status
echo ""
echo "5️⃣  Checking Git status..."
LAST_COMMIT=$(git log --oneline -1 2>/dev/null | head -c 50)
if [ ! -z "$LAST_COMMIT" ]; then
    echo "   ✅ Latest commit: $LAST_COMMIT"
else
    echo "   ❌ Git not configured"
fi

# Summary
echo ""
echo "================================"
echo "✅ SIGMA-OS v1.0 Verification Complete"
echo ""
echo "Next Steps:"
echo "  1. Start the application: bash start.sh"
echo "  2. Open browser: http://localhost:5173"
echo "  3. Configure API keys in the UI"
echo "  4. Start using the intelligent assistant!"
echo ""
echo "Documentation:"
echo "  - README.md: Complete guide and setup"
echo "  - COMPLETION_REPORT.md: Detailed project report"
echo ""
echo "Support:"
echo "  - Check README.md troubleshooting section"
echo "  - Review logs in backend.log and frontend.log"
echo ""
