#!/usr/bin/env python3
"""
SIGMA-OS Backend - Ultra-optimized Intelligent Agent Router
Minimal latency, maximum performance
"""

import os
import sys
import asyncio
import subprocess
import platform
import socket
import shutil
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

# Import Atlas-style workflow engine
try:
    from intelligent_agents.workflow_engine import AtlasWorkflowEngine
    WORKFLOW_ENGINE_AVAILABLE = True
    print("✅ Atlas workflow engine loaded", flush=True)
except ImportError:
    WORKFLOW_ENGINE_AVAILABLE = False
    print("⚠️  Workflow engine not available", flush=True)

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
workflow_engine = None
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


SYSTEM_NETWORK_KEYWORDS = {
    "system", "network", "ip", "internet", "dns", "gateway", "route",
    "hostname", "cpu", "memory", "ram", "disk", "storage", "uptime",
    "interface", "latency", "bandwidth", "ethernet", "wifi", "port"
}


def _safe_run(command: List[str], timeout: float = 2.0) -> str:
    """Run a local read-only command safely and return output text."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output[:3000]
    except Exception:
        return ""


def _read_meminfo_mb() -> Dict[str, Optional[float]]:
    """Read Linux memory stats from /proc/meminfo in MB when available."""
    mem_total = None
    mem_available = None
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = round(int(line.split()[1]) / 1024.0, 2)
                elif line.startswith("MemAvailable:"):
                    mem_available = round(int(line.split()[1]) / 1024.0, 2)
                if mem_total is not None and mem_available is not None:
                    break
    except Exception:
        pass
    return {
        "total_mb": mem_total,
        "available_mb": mem_available,
        "used_mb": round(mem_total - mem_available, 2)
        if mem_total is not None and mem_available is not None
        else None,
    }


def _collect_system_network_snapshot() -> Dict[str, Any]:
    """Collect non-destructive local system and network facts for Ask mode."""
    hostname = socket.gethostname()

    local_ip = ""
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        pass

    # Better local interface detection fallback (no packets sent).
    if not local_ip or local_ip.startswith("127."):
        try:
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.connect(("8.8.8.8", 80))
            local_ip = udp.getsockname()[0]
            udp.close()
        except Exception:
            local_ip = local_ip or "unknown"

    uptime_seconds = None
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            uptime_seconds = int(float(f.read().split()[0]))
    except Exception:
        pass

    disk = shutil.disk_usage("/")

    dns_servers = []
    try:
        with open("/etc/resolv.conf", "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("nameserver"):
                    parts = stripped.split()
                    if len(parts) > 1:
                        dns_servers.append(parts[1])
    except Exception:
        pass

    return {
        "system": {
            "hostname": hostname,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
            "uptime_seconds": uptime_seconds,
            "memory_mb": _read_meminfo_mb(),
            "disk_root": {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
            },
        },
        "network": {
            "local_ip": local_ip,
            "interfaces": _safe_run(["ip", "-brief", "addr"]) or _safe_run(["hostname", "-I"]),
            "default_route": _safe_run(["ip", "route", "show", "default"]),
            "dns_servers": dns_servers,
        },
    }


def _is_system_network_query(command: str) -> bool:
    """Detect whether Ask mode should enrich response with local system/network data."""
    lowered = command.lower()
    return any(keyword in lowered for keyword in SYSTEM_NETWORK_KEYWORDS)


def _format_snapshot_fallback(snapshot: Dict[str, Any]) -> str:
    """Fallback plain-text response if model generation fails."""
    system = snapshot.get("system", {})
    network = snapshot.get("network", {})
    mem = system.get("memory_mb", {})
    disk = system.get("disk_root", {})
    lines = [
        "System and network snapshot:",
        f"- Hostname: {system.get('hostname', 'unknown')}",
        f"- Platform: {system.get('platform', 'unknown')}",
        f"- CPU cores: {system.get('cpu_count', 'unknown')}",
        f"- Memory (MB): total={mem.get('total_mb')} available={mem.get('available_mb')} used={mem.get('used_mb')}",
        f"- Disk / (GB): total={disk.get('total_gb')} used={disk.get('used_gb')} free={disk.get('free_gb')}",
        f"- Local IP: {network.get('local_ip', 'unknown')}",
        f"- Default route: {network.get('default_route', 'unknown')}",
        f"- DNS servers: {', '.join(network.get('dns_servers', [])) or 'unknown'}",
    ]
    if network.get("interfaces"):
        lines.append("- Interfaces:")
        lines.append(str(network.get("interfaces")))
    return "\n".join(lines)

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
    
    # Initialize workflow engine
    if WORKFLOW_ENGINE_AVAILABLE:
        global workflow_engine
        workflow_engine = AtlasWorkflowEngine(agents=agents)
        print("   Creating Atlas Workflow Engine...", flush=True)
        print("   ✅ Workflow Engine ready", flush=True)
    
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
    mode = (request.mode or "agent").strip().lower()

    if mode not in {"agent", "ask"}:
        mode = "agent"
    
    print(f"\n{'='*80}", flush=True)
    print(f"📝 NEW COMMAND: {command}", flush=True)
    print(f"🧭 MODE: {mode.upper()}", flush=True)
    print(f"{'='*80}", flush=True)
    
    try:
        # Ask mode: answer directly without executing system/web/email actions.
        if mode == "ask":
            snapshot = _collect_system_network_snapshot() if _is_system_network_query(command) else None

            ask_prompt = (
                "You are SIGMA-OS in Ask mode. "
                "Answer the user's request directly, clearly, and concisely. "
                "Do not claim to execute commands or take actions. "
                "If a request needs execution, explain what would be done.\n\n"
                f"User request: {command}"
            )

            if snapshot:
                ask_prompt += (
                    "\n\nLocal system/network snapshot (real-time, use this for accurate answers):\n"
                    f"{json.dumps(snapshot, indent=2)}\n\n"
                    "If the user asked for system or network info, answer using this data first."
                )

            ask_text = ""
            try:
                ask_response = model_manager.get_thinking_model().generate_content(ask_prompt)
                ask_text = getattr(ask_response, "text", "") or ""
            except Exception:
                ask_text = ""

            if not ask_text.strip():
                ask_text = _format_snapshot_fallback(snapshot) if snapshot else "I could not generate a response."

            formatted = format_output(ask_text, command, True)

            return CommandResponse(
                success=True,
                result={
                    "success": True,
                    "task": command,
                    "mode": mode,
                    "results": [
                        {
                            "command": command,
                            "output": ask_text,
                            "formatted_response": formatted,
                            "success": True,
                            "exit_code": 0,
                        }
                    ],
                    "formatted_output": formatted,
                    "system_network_snapshot": snapshot,
                },
                agent_used="ask",
                thinking_process="Answered directly in Ask mode"
            )

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
            context={"mode": mode, "command": command}
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
