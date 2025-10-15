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

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
router_model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Initialize agents
agents = {}
active_websockets: List[WebSocket] = []

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
print("   - SystemAgent: Execute commands, manage files")
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
        "model": "gemini-2.0-flash-thinking-exp"
    }

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
1. SystemAgent: Execute shell commands, file operations (create/read/update/delete files), process management, screenshots
2. EmailAgent: Send emails, read emails, search emails via Gmail API
3. WebAgent: Browse websites, extract information, automate web tasks

User command: "{command}"

Which agent should handle this? Consider:
- Email-related tasks → EmailAgent
- Web browsing/scraping → WebAgent
- File operations, system commands → SystemAgent

Respond in JSON:
{{
    "agent": "system|email|web",
    "reasoning": "why this agent is best suited",
    "confidence": 0.0-1.0
}}"""

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
