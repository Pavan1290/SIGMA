#!/usr/bin/env python3
"""
SIGMA-OS Backend - Ultra-optimized Intelligent Agent Router
Minimal latency, maximum performance
"""

import os
import sys
import asyncio
from pathlib import Path
import json
from typing import Dict, Any, List, Optional

# Unbuffer stdout for real-time logging
sys.stdout.reconfigure(line_buffering=True)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

print("🚀 SIGMA-OS Backend Starting...", flush=True)

# Try to import automation features (optional - won't break if missing)
try:
    from backend.db import engine, Base
    from backend.models import AutomationWorkflow, AutomationTask
    AUTOMATION_AVAILABLE = True
    print("✅ Automation features enabled", flush=True)
except ImportError:
    AUTOMATION_AVAILABLE = False
    print("⚠️  Running without automation (install SQLAlchemy to enable)", flush=True)

# Import the unified system agent
from intelligent_agents import SystemAgent, EmailAgent, WebAgent, AgentStatus, AgentUpdate
from intelligent_agents.model_manager import model_manager
from intelligent_agents.output_formatter import format_output

print("✅ All imports loaded successfully (using unified system agent)", flush=True)

# FastAPI setup
app = FastAPI(title="SIGMA-OS v2 - Ultra Fast")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
agents = {}
active_websockets: List[WebSocket] = []

# Models
class CommandRequest(BaseModel):
    command: str
    mode: str = "agent"

class CommandResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    agent_used: Optional[str] = None
    thinking_process: Optional[str] = None

# Initialize agents
def init_agents():
    """Initialize all agents"""
    print("\n" + "="*80, flush=True)
    print("🤖 INITIALIZING INTELLIGENT AGENTS", flush=True)
    print("="*80, flush=True)
    
    def broadcast_update(update: AgentUpdate):
        message = json.dumps(update.to_dict())
        for ws in active_websockets:
            try:
                asyncio.create_task(ws.send_text(message))
            except:
                pass
    
    print("   Creating System Agent...", flush=True)
    agents['system'] = SystemAgent(update_callback=broadcast_update)
    print("   ✅ System Agent ready", flush=True)
    
    print("   Creating Email Agent...", flush=True)
    agents['email'] = EmailAgent(update_callback=broadcast_update)
    print("   ✅ Email Agent ready", flush=True)
    
    print("   Creating Web Agent...", flush=True)
    agents['web'] = WebAgent(update_callback=broadcast_update)
    print("   ✅ Web Agent ready", flush=True)
    
    print("\n✅ All agents initialized successfully!", flush=True)
    print("="*80 + "\n", flush=True)

@app.on_event("startup")
async def on_startup():
    """Initialize agents on startup - keep it fast!"""
    
    # Initialize agents first (core functionality)
    init_agents()
    
    # Create DB tables if automation is available (optional, non-blocking)
    if AUTOMATION_AVAILABLE:
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Automation features enabled")
        except Exception as e:
            print(f"⚠️  Automation disabled: {e}")
    
    print("✅ SIGMA-OS ready!")

init_agents()

# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0",
        "automation": AUTOMATION_AVAILABLE,
        "agents": list(agents.keys()),
        "models": {
            "thinking": model_manager.current_thinking_model,
            "execution": model_manager.current_execution_model
        }
    }

# Get models
@app.get("/models")
async def get_models():
    try:
        model_manager._check_availability()
        return {
            "models": model_manager.get_available_models(),
            "current_thinking": model_manager.current_thinking_model,
            "current_execution": model_manager.current_execution_model,
            "status": "ready"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Set thinking model
@app.post("/models/thinking")
async def set_thinking_model(request: dict):
    try:
        model_id = request.get("model_id")
        if not model_id:
            return {"success": False, "error": "model_id required"}
        
        success = model_manager.set_thinking_model(model_id)
        return {
            "success": success,
            "model": model_id if success else None,
            "message": f"Model set to {model_id}" if success else "Failed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Set execution model
@app.post("/models/execution")
async def set_execution_model(request: dict):
    try:
        model_id = request.get("model_id")
        if not model_id:
            return {"success": False, "error": "model_id required"}
        
        success = model_manager.set_execution_model(model_id)
        return {
            "success": success,
            "model": model_id if success else None,
            "message": f"Model set to {model_id}" if success else "Failed"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Main command endpoint - ULTRA OPTIMIZED
@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Execute command with minimal overhead"""
    
    command = request.command.strip()
    
    print(f"\n{'='*80}", flush=True)
    print(f"📝 NEW COMMAND: {command}", flush=True)
    print(f"{'='*80}", flush=True)
    
    try:
        # Route to best agent (99% of time it's system agent)
        if any(word in command.lower() for word in ['email', 'mail', 'send email']):
            agent_name = 'email'
        elif any(word in command.lower() for word in ['web', 'browser', 'search', 'website']):
            agent_name = 'web'
        else:
            agent_name = 'system'  # Default to system for 99% of tasks
        
        agent = agents.get(agent_name, agents['system'])
        
        print(f"🎯 Using Agent: {agent_name.upper()}", flush=True)
        print(f"⚡ Executing...", flush=True)
        
        # Execute
        result = agent.run(
            task=command,
            context={"mode": request.mode, "command": command}
        )
        
        print(f"✅ Execution complete!", flush=True)
        print(f"   Success: {result.get('success', False)}", flush=True)
        
        # Extract output
        output_text = ""
        if isinstance(result.get('results'), list) and result['results']:
            first_result = result['results'][0]
            if isinstance(first_result, dict):
                output_text = first_result.get('output', '')
            else:
                output_text = str(first_result)
        else:
            output_text = str(result)
        
        # Format output
        formatted = format_output(output_text, command, result.get('success', True))
        
        # Make JSON-safe
        def to_json_safe(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [to_json_safe(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: to_json_safe(v) for k, v in obj.items()}
            else:
                return str(obj)
        
        result = to_json_safe(result)
        formatted = to_json_safe(formatted)
        
        print(f"✅ Success: {result.get('success')}\n")
        
        return CommandResponse(
            success=result.get('success', False),
            result={
                **result,
                "formatted_output": formatted
            },
            agent_used=agent_name,
            thinking_process="Executed quickly"
        )
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        error_output = {
            "type": "error",
            "success": False,
            "error_type": "execution_error",
            "message": str(e),
            "details": str(e),
            "suggestions": ["Check command", "Verify backend", "Check API keys"],
            "raw_output": str(e)
        }
        
        return CommandResponse(
            success=False,
            result={
                "error": str(e),
                "formatted_output": error_output
            },
            agent_used=None,
            thinking_process=f"Error: {str(e)}"
        )

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time agent updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to SIGMA-OS",
            "agents": list(agents.keys())
        })
        
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# Startup message
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 SIGMA-OS Backend v2 - Starting...")
    print("   HTTP: http://localhost:5000")
    print("   WebSocket: ws://localhost:5000/ws\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
