# 🧠 SIGMA-OS Intelligent Agent System

**A truly intelligent AI agent system powered by Google Gemini 2.0 Flash Thinking**

## What's Different?

This is a **complete rebuild** of SIGMA-OS with:

### ✨ Real Agentic AI
- **Self-planning**: Agents break down complex tasks automatically
- **Self-healing**: Agents debug and fix their own errors
- **Multi-step execution**: Handles complex workflows intelligently
- **Real-time updates**: See the AI thinking process live

### 🤖 Intelligent Agents

#### 1. **SystemAgent**
- Execute shell commands
- File operations (create, read, update, delete)
- Process management
- Screenshots
- **Uses AI to figure out HOW to execute commands**

#### 2. **EmailAgent**
- Uses **Gmail API** (official, reliable - NO Selenium!)
- AI-powered email composition
- Send/read/search emails
- Handles authentication automatically

#### 3. **WebAgent**
- Uses **Playwright** (more reliable than Selenium)
- Intelligent web browsing
- Extract information from pages
- Automate web tasks

### 🧠 Powered by Gemini 2.0 Flash Thinking
- Advanced reasoning for complex tasks
- Learns from failures
- Provides explanations for every action
- Plans multi-step solutions

## Quick Start

### 1. Setup
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Configure
Create a `.env` file (see `.env.example` for more options):
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
# Base URL for backend FastAPI server (no trailing slash). Used by the frontend for REST and WS.
VITE_BACKEND_URL=http://localhost:5000
```

### 3. Run

```bash
chmod +x start.sh
./start.sh
```

This starts both services:

- Frontend (Vite): <http://localhost:5173> (if 5173 is busy, Vite will pick the next available port and print it, e.g., 5174)
- Backend (FastAPI): <http://localhost:5000>
- WebSocket: <ws://localhost:5000/ws>

To stop everything:

```bash
./stop.sh
```

---

## How to run (step-by-step) ✅

The steps below are verified on Linux. They’ll also work on macOS; on Windows use WSL or run the commands in PowerShell with equivalent syntax.

### Prerequisites

- Python 3.10+ (check with `python3 --version`)
- Node.js 18+ and npm 9+ (check with `node -v` and `npm -v`)
- Internet connection (for Playwright browser download and npm packages)

### One-time setup

1. Create the virtualenv and install all dependencies (backend + frontend):

     ```bash
     chmod +x setup.sh
     ./setup.sh
     ```

     What this does:

     - Creates `.venv` and installs `requirements.txt`
     - Installs Playwright Chromium (`playwright install chromium`)
     - Installs frontend packages (`npm install`)

2. Add your environment file:

     ```bash
     cp .env.example .env
     # edit .env and set your real API key
     ```

     Minimum variables:

     - `GOOGLE_API_KEY=...` (required for Gemini)
     - `VITE_BACKEND_URL=http://localhost:5000` (frontend talks to backend)

### Run (two options)

Option A — scripts (recommended):

```bash
chmod +x start.sh stop.sh
./start.sh
```

You’ll get:

- Frontend: <http://localhost:5173>
- Backend:  <http://localhost:5000>
- WebSocket: <ws://localhost:5000/ws>

Stop both:

```bash
./stop.sh
```

Option B — manual:

1. Start backend in one terminal

     ```bash
     source .venv/bin/activate
     python backend/app.py
     ```

     Health check: <http://localhost:5000/health>

2. Start frontend in another terminal

     ```bash
     npm run dev
     ```

     Vite will print the local URL (usually <http://localhost:5173>). If 5173 is busy, it will auto-pick the next port (e.g., 5174). The frontend will use `VITE_BACKEND_URL` from `.env` to call the backend.

### Using the app

Open the frontend in your browser and type natural language commands like:

- "Send an email to test@example.com about the project update"
- "Create a file called meeting_notes.txt with today’s agenda"
- "Go to <https://news.ycombinator.com> and get the top 5 stories"

### Troubleshooting

- npm dev was killed (exit code 137): Usually means the process was killed (OOM or previous `pkill` from `start.sh`). Try:
    - Close any previous Vite instances
    - Run `./stop.sh` then `./start.sh` again
    - Ensure your machine has enough free RAM

- Playwright missing system deps on Linux:

    ```bash
    npx playwright install --with-deps chromium
    ```

    This may prompt for `sudo` to install apt packages.

- Backend health check fails:
    - Confirm `.venv` is active (you see `(.venv)` in your shell)
    - Ensure `GOOGLE_API_KEY` is set in `.env`
    - Look at the terminal running `backend/app.py` for stack traces

- Gmail API isn’t working:
    - Follow the "Gmail Setup" section below
    - Place `credentials.json` in the project root (it is gitignored)
    - The first run will open a browser window to authorize

---

### 4. Use

Open <http://localhost:5173> and give natural language commands:

**Examples:**
- 📧 "Send an email to test@example.com about the project update"
- 📁 "Create a file called meeting_notes.txt with today's agenda"
- 🌐 "Go to news.ycombinator.com and get the top 5 stories"
- 📊 "List all Python files in this directory"
- 🖼️ "Take a screenshot"

## Architecture

```text
User Command
    ↓
AI Router (Gemini) - Decides which agent to use
    ↓
Selected Agent
    ↓
AI Planning - Breaks down into steps
    ↓
Execution - With error handling
    ↓
Self-Healing - If errors occur
    ↓
Real-time Updates - To UI via WebSocket
```

## Features

### 🎯 Smart Routing
The system uses AI to automatically route commands to the right agent based on intent.

### 🔄 Self-Healing
If an agent encounters an error, it uses AI to:

1. Analyze the root cause
2. Find an alternative approach
3. Retry with the fix
4. Learn from the failure

### 📊 Real-time Visibility

See exactly what the AI is thinking and doing:

- Planning process
- Execution steps
- Progress updates
- Error recovery

### 💡 Natural Language

No complex syntax - just tell it what you want in plain English.

## Gmail Setup (Optional)

For email functionality:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials.json to project root
6. First run will open browser for authentication

## Technical Stack

- **Backend**: FastAPI + WebSocket
- **Frontend**: React + Vite
- **AI**: Google Gemini 2.0 Flash Thinking
- **Email**: Gmail API (official)
- **Web**: Playwright
- **Language**: Python 3.8+

## Why This is Better

### Old System Problems

- ❌ Manual agents with hardcoded logic
- ❌ Selenium (unreliable, breaks often)
- ❌ No error recovery
- ❌ No visibility into what's happening

### New System Solutions

- ✅ AI-powered agents that adapt
- ✅ Gmail API + Playwright (reliable)
- ✅ Automatic error recovery
- ✅ Real-time updates and thinking process

## Comparison

| Feature | Old SIGMA-OS | New Intelligent System |
|---------|-------------|----------------------|
| Email | Selenium (broken) | Gmail API (works) |
| Error Handling | Crashes | Self-healing |
| Planning | Manual | AI-powered |
| Visibility | None | Real-time updates |
| Flexibility | Rigid | Adaptive |
| Reliability | Low | High |

## Development

### Project Structure

```text
intelligent_agents/
  ├── agent_core.py       # Base intelligent agent class
  ├── system_agent.py     # System operations
  ├── email_agent.py      # Email via Gmail API
  └── web_agent.py        # Web automation
  
backend/
  └── intelligent_app.py  # FastAPI server with AI routing

src/
  └── components/
      └── IntelligentAssistant.jsx  # React UI with real-time updates
```

### Adding New Agents

```python
from intelligent_agents import IntelligentAgent, AgentStatus

class MyAgent(IntelligentAgent):
    def __init__(self, update_callback=None):
        super().__init__(
            name="MyAgent",
            capabilities=["capability1", "capability2"],
            update_callback=update_callback
        )
    
    def execute_step(self, step, context):
        # Implement your agent logic
        return {"success": True, "result": "done"}
```

## License

MIT

## Credits

Built with ❤️ using Google Gemini AI

---

**This is what real agentic AI looks like.** 🚀
