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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
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
    try:
        # Recheck availability each time to catch newly saved API keys
        model_manager._check_availability()
        return {
            "models": model_manager.get_available_models(),
            "current_thinking": model_manager.current_thinking_model,
            "current_execution": model_manager.current_execution_model,
            "status": "ready"
        }
    except Exception as e:
        print(f"Error getting models: {e}")
        return {
            "models": [],
            "current_thinking": None,
            "current_execution": None,
            "status": "error",
            "error": str(e)
        }

@app.post("/models/thinking")
async def set_thinking_model(request: dict):
    """Set the thinking model"""
    try:
        model_id = request.get("model_id")
        if not model_id:
            return {"success": False, "error": "model_id is required"}
            
        success = model_manager.set_thinking_model(model_id)
        
        if success:
            print(f"\n✅ Thinking model changed to: {model_id}")
            if model_id in model_manager.available_models:
                model = model_manager.available_models[model_id]
                print(f"   Provider: {model.provider}")
                print(f"   Model: {model.model_name}\n")
            return {"success": True, "model": model_id, "message": f"Thinking model set to {model_id}"}
        return {"success": False, "error": f"Model {model_id} not available"}
    except Exception as e:
        print(f"Error setting thinking model: {e}")
        return {"success": False, "error": str(e)}

@app.post("/models/execution")
async def set_execution_model(request: dict):
    """Set the execution model"""
    try:
        model_id = request.get("model_id")
        if not model_id:
            return {"success": False, "error": "model_id is required"}
            
        success = model_manager.set_execution_model(model_id)
        
        if success:
            print(f"\n✅ Execution model changed to: {model_id}")
            if model_id in model_manager.available_models:
                model = model_manager.available_models[model_id]
                print(f"   Provider: {model.provider}")
                print(f"   Model: {model.model_name}\n")
            return {"success": True, "model": model_id, "message": f"Execution model set to {model_id}"}
        return {"success": False, "error": f"Model {model_id} not available"}
    except Exception as e:
        print(f"Error setting execution model: {e}")
        return {"success": False, "error": str(e)}

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

# API Key Management Storage (in-memory for now, should use encrypted DB in production)
api_keys = {
    "google": {"key": os.getenv("GOOGLE_API_KEY"), "verified": False, "usage": {"requests": 0, "tokens": 0}},
    "groq": {"key": os.getenv("GROQ_API_KEY"), "verified": False, "usage": {"requests": 0, "tokens": 0}},
    "openai": {"key": os.getenv("OPENAI_API_KEY"), "verified": False, "usage": {"requests": 0, "tokens": 0}},
    "anthropic": {"key": os.getenv("ANTHROPIC_API_KEY"), "verified": False, "usage": {"requests": 0, "tokens": 0}}
}

@app.get("/api-keys/status")
async def get_api_keys_status():
    """Get the status of all API keys (without exposing the actual keys)"""
    status = {}
    for provider, data in api_keys.items():
        status[provider] = {
            "configured": bool(data["key"]),
            "verified": data.get("verified", False),
            "masked_key": f"{'*' * 20}{data['key'][-4:]}" if data["key"] and len(data["key"]) > 4 else None
        }
    return {"status": status}

@app.post("/api-keys/verify")
async def verify_api_key(request: Request):
    """Verify an API key by making a test request to the provider"""
    data = await request.json()
    provider = data.get("provider")
    api_key = data.get("api_key")
    
    if not provider or not api_key:
        return {"success": False, "error": "Provider and API key are required"}
    
    if provider not in api_keys:
        return {"success": False, "error": f"Unknown provider: {provider}"}
    
    try:
        verified = False
        error_msg = None
        
        # Verify the key by making a test request
        if provider == "google":
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                # Test with a simple request
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content("Say 'verified'")
                verified = "verified" in response.text.lower()
            except Exception as e:
                error_msg = f"Google API error: {str(e)}"
            
        elif provider == "groq":
            try:
                from groq import Groq
                client = Groq(api_key=api_key)
                # Test with a simple request
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": "Say 'verified'"}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=10
                )
                verified = "verified" in response.choices[0].message.content.lower()
            except Exception as e:
                error_msg = f"Groq API error: {str(e)}"
            
        elif provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                # Test with a simple request
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": "Say 'verified'"}],
                    model="gpt-4o-mini",
                    max_tokens=10
                )
                verified = "verified" in response.choices[0].message.content.lower()
            except Exception as e:
                error_msg = f"OpenAI API error: {str(e)}"
            
        elif provider == "anthropic":
            try:
                from anthropic import Anthropic
                client = Anthropic(api_key=api_key)
                # Test with a simple request
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Say 'verified'"}]
                )
                verified = "verified" in response.content[0].text.lower()
            except Exception as e:
                error_msg = f"Anthropic API error: {str(e)}"
        else:
            return {"success": False, "error": "Unknown provider"}
        
        if verified:
            # Store the verified key
            api_keys[provider] = {
                "key": api_key,
                "verified": True,
                "usage": api_keys.get(provider, {}).get("usage", {"requests": 0, "tokens": 0})
            }
            
            # Update environment variable
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
            
            # Update .env file
            env_path = Path(__file__).parent.parent / ".env"
            if env_path.exists():
                try:
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    env_key = f"{provider.upper()}_API_KEY"
                    updated = False
                    for i, line in enumerate(lines):
                        if line.startswith(f"{env_key}="):
                            lines[i] = f"{env_key}={api_key}\n"
                            updated = True
                            break
                    
                    if not updated:
                        lines.append(f"{env_key}={api_key}\n")
                    
                    with open(env_path, 'w') as f:
                        f.writelines(lines)
                except Exception as e:
                    print(f"Warning: Could not update .env file: {e}")
            
            print(f"✅ {provider.capitalize()} API key verified successfully")
            
            return {
                "success": True,
                "provider": provider,
                "verified": True,
                "message": f"{provider.capitalize()} API key verified successfully"
            }
        else:
            error_detail = error_msg or "API key verification returned false"
            return {"success": False, "error": error_detail}
            
    except Exception as e:
        error_detail = str(e)
        print(f"❌ Verification error for {provider}: {error_detail}")
        return {"success": False, "error": f"Verification failed: {error_detail}"}

@app.post("/api-keys/save")
async def save_api_key(request: Request):
    """Save an API key to .env file (after verification)"""
    data = await request.json()
    provider = data.get("provider")
    api_key = data.get("api_key")
    
    if not provider or not api_key:
        return {"success": False, "error": "Provider and API key required"}
    
    try:
        # Update environment variable
        os.environ[f"{provider.upper()}_API_KEY"] = api_key
        
        # Update .env file
        env_path = Path(__file__).parent.parent / ".env"
        lines = []
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        env_key = f"{provider.upper()}_API_KEY"
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith(f"{env_key}="):
                lines[i] = f"{env_key}={api_key}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"{env_key}={api_key}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ API key saved for {provider} in .env file")
        return {"success": True, "message": "API key saved to .env"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api-keys/list")
async def list_api_keys():
    """List all configured API keys (status only, no keys exposed)"""
    keys_status = {}
    
    for provider in ["google", "groq", "openai", "anthropic"]:
        env_key = f"{provider.upper()}_API_KEY"
        is_set = env_key in os.environ and bool(os.environ.get(env_key))
        keys_status[provider] = is_set
    
    return {"keys": keys_status}

@app.post("/api-keys/remove")
async def remove_api_key(request: Request):
    """Remove an API key from .env"""
    data = await request.json()
    provider = data.get("provider")
    
    if not provider:
        return {"success": False, "error": "Provider required"}
    
    try:
        env_key = f"{provider.upper()}_API_KEY"
        
        # Remove from environment
        if env_key in os.environ:
            del os.environ[env_key]
        
        # Remove from .env file
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            lines = [line for line in lines if not line.startswith(f"{env_key}=")]
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
        
        print(f"✅ API key removed for {provider}")
        return {"success": True, "message": f"API key removed for {provider}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api-keys/{provider}")
async def delete_api_key(provider: str):
    """Delete an API key for a provider"""
    if provider not in api_keys:
        return {"success": False, "error": "Unknown provider"}
    
    # Clear the key
    api_keys[provider] = {
        "key": None,
        "verified": False,
        "usage": {"requests": 0, "tokens": 0}
    }
    
    # Clear environment variable
    if f"{provider.upper()}_API_KEY" in os.environ:
        del os.environ[f"{provider.upper()}_API_KEY"]
    
    # Update .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        env_key = f"{provider.upper()}_API_KEY"
        lines = [line for line in lines if not line.startswith(f"{env_key}=")]
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
    
    return {"success": True, "message": f"{provider.capitalize()} API key deleted"}

@app.get("/api-keys/usage")
async def get_api_usage():
    """Get usage statistics for all API keys"""
    usage_stats = {}
    total_requests = 0
    total_tokens = 0
    total_cost = 0.0
    
    for provider, data in api_keys.items():
        if data.get("key") and data.get("verified"):
            usage = data.get("usage", {"requests": 0, "tokens": 0})
            
            # Calculate estimated cost (simplified pricing)
            cost = 0.0
            if provider == "google":
                cost = usage["tokens"] * 0.000001  # $1 per 1M tokens (rough estimate)
            elif provider == "groq":
                cost = usage["tokens"] * 0.0000005  # Groq is cheaper
            elif provider == "openai":
                cost = usage["tokens"] * 0.000002  # $2 per 1M tokens (GPT-4 estimate)
            elif provider == "anthropic":
                cost = usage["tokens"] * 0.000003  # $3 per 1M tokens (Claude estimate)
            
            usage_stats[provider] = {
                "requests": usage["requests"],
                "tokens": usage["tokens"],
                "estimated_cost": round(cost, 4)
            }
            
            total_requests += usage["requests"]
            total_tokens += usage["tokens"]
            total_cost += cost
    
    return {
        "providers": usage_stats,
        "total": {
            "requests": total_requests,
            "tokens": total_tokens,
            "estimated_cost": round(total_cost, 4)
        }
    }

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
