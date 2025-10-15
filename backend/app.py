#!/usr/bin/env python3
"""
SIGMA-OS Backend - Intelligent Agent Router
Uses Gemini 2.0 Flash Thinking for agentic AI tasks
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path so we can import intelligent_agents
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Import intelligent agents
from intelligent_agents import (
    SystemAgent,
    EmailAgent,
    WebAgent,
    AgentStatus,
    AgentUpdate
)
from intelligent_agents.model_manager import model_manager

load_dotenv()

app = FastAPI(title="SIGMA-OS Intelligent Agent System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
agents = {}
active_websockets: List[WebSocket] = []

def get_router_model():
    """Get the current thinking model for routing"""
    return model_manager.get_thinking_model()

def broadcast_update(update: AgentUpdate):
    """Broadcast agent updates to all connected websockets"""
    message = json.dumps(update.to_dict())
    for ws in active_websockets:
        try:
            asyncio.create_task(ws.send_text(message))
        except:
            pass

# Initialize agents with update callback
agents['system'] = SystemAgent(update_callback=broadcast_update)
agents['email'] = EmailAgent(update_callback=broadcast_update)
agents['web'] = WebAgent(update_callback=broadcast_update)

print("✅ Intelligent agents initialized:")
print("   - SystemAgent: Execute commands, manage files, take screenshots")
print("   - EmailAgent: Send/read emails via Gmail API")
print("   - WebAgent: Browse web, extract data")

class CommandRequest(BaseModel):
    command: str
    mode: str = "agent"  # agent mode for intelligent execution

class CommandResponse(BaseModel):
    success: bool
    result: Any
    agent_used: Optional[str] = None
    thinking_process: Optional[str] = None

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": list(agents.keys()),
        "current_thinking_model": model_manager.current_thinking_model,
        "current_execution_model": model_manager.current_execution_model
    }

@app.get("/models")
async def get_models():
    """Get all available AI models"""
    return {
        "models": model_manager.get_available_models(),
        "current_thinking": model_manager.current_thinking_model,
        "current_execution": model_manager.current_execution_model
    }

@app.post("/models/thinking")
async def set_thinking_model(request: dict):
    """Set the thinking model"""
    model_id = request.get("model_id")
    success = model_manager.set_thinking_model(model_id)
    
    if success:
        print(f"\n🔄 Thinking model changed to: {model_id}")
        print(f"   Provider: {model_manager.available_models[model_id].provider}")
        print(f"   Model: {model_manager.available_models[model_id].model_name}\n")
        return {"success": True, "model": model_id}
    return {"success": False, "error": "Model not available"}

@app.post("/models/execution")
async def set_execution_model(request: dict):
    """Set the execution model"""
    model_id = request.get("model_id")
    success = model_manager.set_execution_model(model_id)
    
    if success:
        print(f"\n🔄 Execution model changed to: {model_id}")
        print(f"   Provider: {model_manager.available_models[model_id].provider}")
        print(f"   Model: {model_manager.available_models[model_id].model_name}\n")
        return {"success": True, "model": model_id}
    return {"success": False, "error": "Model not available"}

@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    Execute a natural language command using intelligent agents
    """
    
    command = request.command.strip()
    
    print("\n" + "="*70)
    print(f"📝 User Command: {command}")
    print(f"🤖 Mode: {request.mode}")
    print("="*70)
    
    try:
        # Step 1: Use AI to route to the right agent
        routing_prompt = f"""You are an intelligent task router for SIGMA-OS.

Available agents and their capabilities:
1. SystemAgent: Execute shell commands, file operations (create/read/update/delete files), process management, **SCREENSHOTS** (any screen capture)
2. EmailAgent: Send emails, read emails, search emails via Gmail API
3. WebAgent: Browse websites, extract information, automate web tasks

User command: "{command}"

Which agent should handle this? Consider:
- Screenshots, screen capture → SystemAgent (ALWAYS)
- Email-related tasks → EmailAgent
- Web browsing/scraping → WebAgent
- File operations, system commands, process management → SystemAgent

CRITICAL: Any mention of "screenshot", "capture screen", "take picture of screen" → MUST route to SystemAgent

Respond in JSON:
{{
    "agent": "system|email|web",
    "reasoning": "why this agent is best suited",
    "confidence": 0.0-1.0
}}"""

        router_model = get_router_model()
        routing_response = router_model.generate_content(routing_prompt)
        routing_text = routing_response.text.strip()
        
        if "```json" in routing_text:
            routing_text = routing_text.split("```json")[1].split("```")[0].strip()
        elif "```" in routing_text:
            routing_text = routing_text.split("```")[1].split("```")[0].strip()
        
        routing = json.loads(routing_text)
        
        selected_agent_name = routing['agent']
        selected_agent = agents.get(selected_agent_name)
        
        if not selected_agent:
            # Fallback to system agent
            selected_agent_name = 'system'
            selected_agent = agents['system']
        
        print(f"🎯 Selected Agent: {selected_agent_name}")
        print(f"💭 Reasoning: {routing['reasoning']}")
        print(f"📊 Confidence: {routing['confidence']}")
        print()
        
        # Step 2: Execute the command with the selected agent
        result = selected_agent.run(
            task=command,
            context={
                "mode": request.mode,
                "original_command": command
            }
        )
        
        print("\n✅ Execution Complete!")
        print(f"Success: {result.get('success')}")
        print("="*70 + "\n")
        
        return CommandResponse(
            success=result.get('success', False),
            result=result,
            agent_used=selected_agent_name,
            thinking_process=routing.get('reasoning')
        )
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("="*70 + "\n")
        
        return CommandResponse(
            success=False,
            result={"error": str(e)},
            agent_used=None,
            thinking_process=f"Error occurred: {str(e)}"
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent updates
    """
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to SIGMA-OS Agent System",
            "agents": list(agents.keys())
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting SIGMA-OS Intelligent Agent System...")
    print("   Backend: http://localhost:5000")
    print("   WebSocket: ws://localhost:5000/ws")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
