# 🛠️ SIGMA-OS Development Guide

## Project Structure

```
intelligent_agents/     # AI Agent System
  ├── agent_core.py    # Base class with self-healing
  ├── system_agent.py  # System operations
  ├── email_agent.py   # Gmail API
  └── web_agent.py     # Playwright automation

backend/
  └── app.py           # FastAPI + WebSocket server

src/
  └── components/
      └── IntelligentAssistant.jsx  # React UI
```

## Adding New Agents

Create a new file in `intelligent_agents/`:

```python
from .agent_core import IntelligentAgent, AgentStatus

class MyAgent(IntelligentAgent):
    def __init__(self, update_callback=None):
        super().__init__(
            name="MyAgent",
            capabilities=["cap1", "cap2"],
            update_callback=update_callback
        )
    
    def execute_step(self, step, context):
        # Your logic here
        self._send_update(
            AgentStatus.EXECUTING,
            "Doing something..."
        )
        
        return {
            "success": True,
            "result": "done"
        }
```

Register in `backend/app.py`:

```python
from intelligent_agents import MyAgent

agents['my'] = MyAgent(update_callback=broadcast_update)
```

## Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: React, Vite
- **AI**: Google Gemini 2.0 Flash Thinking
- **Web**: Playwright
- **Email**: Gmail API

## Environment Variables

Required in `.env`:
```
GOOGLE_API_KEY=your_key_here
```

## Development Workflow

1. Make changes
2. Test locally with `./start.sh`
3. Check WebSocket updates in browser console
4. Monitor backend logs in terminal

## Best Practices

- Use type hints in Python
- Send real-time updates via `_send_update()`
- Let AI handle complex logic
- Implement self-healing in agents
- Document capabilities clearly

---

**Happy coding!** 🚀
