"""Agent Orchestrator - Coordinate and manage multiple agents"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict
import json


class AgentMessage:
    """Message passed between agents"""
    
    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        message_id: str = None,
    ):
        self.message_id = message_id or f"msg_{datetime.utcnow().timestamp()}"
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.message_type = message_type
        self.payload = payload
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentCapability:
    """Represents what an agent can do"""
    
    def __init__(self, name: str, description: str, parameters: List[str] = None):
        self.name = name
        self.description = description
        self.parameters = parameters or []


class AgentOrchestrator:
    """
    Agent Orchestrator - Coordinate multiple agents
    
    Features:
    - Agent registration and discovery
    - Inter-agent communication
    - Task routing and delegation
    - Load balancing across agents
    - Agent capability matching
    - Message queuing and delivery
    - Agent collaboration on complex tasks
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_name -> agent instance
        self.capabilities: Dict[str, List[AgentCapability]] = {}  # agent_name -> capabilities
        self.message_queues: Dict[str, asyncio.Queue] = {}  # agent_name -> message queue
        self.message_history: List[AgentMessage] = []
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "avg_response_time": 0.0,
        })
    
    def register_agent(
        self,
        name: str,
        agent_instance: Any,
        capabilities: List[AgentCapability] = None
    ):
        """Register an agent with the orchestrator"""
        
        self.agents[name] = agent_instance
        self.capabilities[name] = capabilities or []
        self.message_queues[name] = asyncio.Queue()
        
        print(f"✅ Agent registered: {name} with {len(capabilities or [])} capabilities")
    
    def unregister_agent(self, name: str):
        """Unregister an agent"""
        
        if name in self.agents:
            del self.agents[name]
            del self.capabilities[name]
            del self.message_queues[name]
            print(f"🗑️  Agent unregistered: {name}")
    
    def find_capable_agents(self, required_capability: str) -> List[str]:
        """Find agents that have a specific capability"""
        
        capable_agents = []
        
        for agent_name, caps in self.capabilities.items():
            for cap in caps:
                if cap.name == required_capability or required_capability in cap.name.lower():
                    capable_agents.append(agent_name)
                    break
        
        return capable_agents
    
    def select_best_agent(self, task: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Select the best agent for a task based on:
        - Capability matching
        - Current load
        - Past performance
        - Context hints
        """
        
        task_lower = task.lower()
        context = context or {}
        
        # Check for explicit agent preference in context
        if "preferred_agent" in context:
            agent_name = context["preferred_agent"]
            if agent_name in self.agents:
                return agent_name
        
        # Keyword-based routing (fast path)
        if any(word in task_lower for word in ['email', 'mail', 'send message']):
            return "email" if "email" in self.agents else None
        
        if any(word in task_lower for word in ['web', 'browser', 'search', 'scrape', 'website']):
            return "web" if "web" in self.agents else None
        
        if any(word in task_lower for word in ['file', 'folder', 'directory', 'screenshot', 'system', 'terminal']):
            return "system" if "system" in self.agents else None
        
        # Fallback: use least loaded agent with general capability
        if self.agents:
            # Simple load balancing: use agent stats
            agent_loads = {
                name: stats["tasks_completed"] + stats["tasks_failed"]
                for name, stats in self.agent_stats.items()
                if name in self.agents
            }
            
            if agent_loads:
                return min(agent_loads, key=agent_loads.get)
            
            # Return first available agent
            return list(self.agents.keys())[0]
        
        return None
    
    async def execute_task(
        self,
        task: str,
        context: Dict[str, Any] = None,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using the best available agent
        
        Args:
            task: Task description/command
            context: Additional context
            agent_name: Specific agent to use (optional)
        
        Returns:
            Task result with metadata
        """
        
        context = context or {}
        
        # Select agent if not specified
        if not agent_name:
            agent_name = self.select_best_agent(task, context)
        
        if not agent_name or agent_name not in self.agents:
            return {
                "success": False,
                "error": "No capable agent available",
                "task": task,
            }
        
        agent = self.agents[agent_name]
        stats = self.agent_stats[agent_name]
        
        print(f"🎯 Routing task to agent: {agent_name}")
        
        start_time = datetime.utcnow()
        
        try:
            # Execute task
            if hasattr(agent, 'run'):
                result = agent.run(task=task, context=context)
            elif callable(agent):
                result = agent(task, context)
            else:
                result = {"success": False, "error": "Agent not callable"}
            
            # Update stats
            stats["tasks_completed"] += 1
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_avg_response_time(agent_name, response_time)
            
            return {
                "success": True,
                "agent": agent_name,
                "result": result,
                "response_time": response_time,
            }
            
        except Exception as e:
            stats["tasks_failed"] += 1
            return {
                "success": False,
                "agent": agent_name,
                "error": str(e),
                "task": task,
            }
    
    async def send_message(self, message: AgentMessage):
        """Send message from one agent to another"""
        
        if message.to_agent not in self.message_queues:
            print(f"⚠️  Unknown agent: {message.to_agent}")
            return
        
        await self.message_queues[message.to_agent].put(message)
        self.message_history.append(message)
        
        self.agent_stats[message.from_agent]["messages_sent"] += 1
        self.agent_stats[message.to_agent]["messages_received"] += 1
        
        print(f"📨 Message sent: {message.from_agent} -> {message.to_agent} ({message.message_type})")
    
    async def receive_message(self, agent_name: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        """Receive message for an agent (non-blocking with timeout)"""
        
        if agent_name not in self.message_queues:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.message_queues[agent_name].get(),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def broadcast_message(
        self,
        from_agent: str,
        message_type: str,
        payload: Dict[str, Any]
    ):
        """Broadcast message to all agents"""
        
        for agent_name in self.agents.keys():
            if agent_name != from_agent:
                message = AgentMessage(
                    from_agent=from_agent,
                    to_agent=agent_name,
                    message_type=message_type,
                    payload=payload,
                )
                await self.send_message(message)
    
    async def coordinate_agents(
        self,
        task: str,
        agents_needed: List[str],
        coordination_strategy: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents to complete a complex task
        
        Args:
            task: Overall task description
            agents_needed: List of agent names to coordinate
            coordination_strategy: "sequential", "parallel", or "pipeline"
        
        Returns:
            Combined results from all agents
        """
        
        results = {}
        
        if coordination_strategy == "sequential":
            # Execute agents one after another
            context = {}
            for agent_name in agents_needed:
                result = await self.execute_task(task, context, agent_name)
                results[agent_name] = result
                # Pass result as context to next agent
                context["previous_result"] = result
        
        elif coordination_strategy == "parallel":
            # Execute all agents simultaneously
            tasks = [
                self.execute_task(task, {}, agent_name)
                for agent_name in agents_needed
            ]
            agent_results = await asyncio.gather(*tasks)
            results = dict(zip(agents_needed, agent_results))
        
        elif coordination_strategy == "pipeline":
            # Each agent processes output of previous agent
            current_data = {"task": task}
            for agent_name in agents_needed:
                result = await self.execute_task(
                    json.dumps(current_data),
                    {"pipeline_mode": True},
                    agent_name
                )
                results[agent_name] = result
                current_data = result.get("result", {})
        
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "strategy": coordination_strategy,
            "agents": agents_needed,
            "results": results,
        }
    
    def _update_avg_response_time(self, agent_name: str, new_time: float):
        """Update average response time for an agent"""
        
        stats = self.agent_stats[agent_name]
        
        if stats["tasks_completed"] == 1:
            stats["avg_response_time"] = new_time
        else:
            # Exponential moving average
            alpha = 0.2
            stats["avg_response_time"] = (
                alpha * new_time + (1 - alpha) * stats["avg_response_time"]
            )
    
    def get_agent_stats(self, agent_name: str = None) -> Dict[str, Any]:
        """Get statistics for agent(s)"""
        
        if agent_name:
            return {
                "agent": agent_name,
                "registered": agent_name in self.agents,
                "capabilities": [cap.name for cap in self.capabilities.get(agent_name, [])],
                "stats": self.agent_stats.get(agent_name, {}),
            }
        
        return {
            name: self.get_agent_stats(name)
            for name in self.agents.keys()
        }
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return [msg.to_dict() for msg in self.message_history[-limit:]]
