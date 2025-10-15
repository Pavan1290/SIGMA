#!/usr/bin/env python3
"""
SIGMA-OS Intelligent Agent Core
Supports multiple AI models with hot-swapping
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# Import model manager
from .model_manager import model_manager

class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"
    RETRYING = "retrying"

@dataclass
class AgentUpdate:
    """Real-time update from agent to UI"""
    agent_name: str
    status: AgentStatus
    message: str
    thinking_process: Optional[str] = None
    action_taken: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    timestamp: float = time.time()
    
    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value,
            'timestamp': self.timestamp
        }

class IntelligentAgent:
    """
    Base class for intelligent agents that can:
    - Think and reason about tasks
    - Plan multi-step actions
    - Execute with error handling
    - Learn from failures
    - Provide real-time updates
    """
    
    def __init__(self, name: str, capabilities: List[str], update_callback=None):
        self.name = name
        self.capabilities = capabilities
        self.update_callback = update_callback
        
        # Store reference to model manager (don't cache models!)
        self.model_manager = model_manager
        
        self.conversation_history = []
        self.error_memory = []  # Learn from past failures
    
    def _get_thinking_model(self):
        """Get current thinking model dynamically"""
        return self.model_manager.get_thinking_model()
    
    def _get_execution_model(self):
        """Get current execution model dynamically"""
        return self.model_manager.get_execution_model()
        
    def _send_update(self, status: AgentStatus, message: str, **kwargs):
        """Send real-time update to UI"""
        update = AgentUpdate(
            agent_name=self.name,
            status=status,
            message=message,
            **kwargs
        )
        
        if self.update_callback:
            self.update_callback(update)
        
        print(f"[{self.name}] {status.value.upper()}: {message}")
        return update
    
    def think(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Deep thinking about the task using Gemini's reasoning capabilities
        Returns a structured plan
        """
        self._send_update(
            AgentStatus.THINKING,
            f"Analyzing task: {task}",
            thinking_process="Breaking down the task into steps..."
        )
        
        # Build context-aware prompt
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        error_context = ""
        if self.error_memory:
            error_context = f"\nPrevious failures to avoid:\n{json.dumps(self.error_memory[-3:], indent=2)}"
        
        prompt = f"""You are {self.name}, an intelligent AI agent with these capabilities:
{', '.join(self.capabilities)}

Task: {task}
{context_str}
{error_context}

Think deeply about this task. Provide a detailed execution plan in JSON format:
{{
    "understanding": "What the user wants to achieve",
    "approach": "Your strategy to accomplish this",
    "steps": [
        {{"step": 1, "action": "description", "tool": "tool_name", "expected_outcome": "what should happen"}},
        ...
    ],
    "potential_issues": ["issue1", "issue2"],
    "fallback_plan": "What to do if primary approach fails"
}}

Be specific and actionable. Consider edge cases and error scenarios."""

        try:
            response = self._get_thinking_model().generate_content(prompt)
            thinking_text = response.text
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in thinking_text:
                thinking_text = thinking_text.split("```json")[1].split("```")[0].strip()
            elif "```" in thinking_text:
                thinking_text = thinking_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(thinking_text)
            
            self._send_update(
                AgentStatus.THINKING,
                f"Plan created with {len(plan.get('steps', []))} steps",
                thinking_process=plan.get('understanding', ''),
                progress=20
            )
            
            return plan
            
        except Exception as e:
            self._send_update(
                AgentStatus.ERROR,
                f"Thinking failed: {str(e)}",
                thinking_process=f"Error during planning: {str(e)}"
            )
            # Fallback to simple plan
            return {
                "understanding": task,
                "approach": "Direct execution with error handling",
                "steps": [{"step": 1, "action": task, "tool": "auto", "expected_outcome": "Task completed"}],
                "potential_issues": ["Unknown"],
                "fallback_plan": "Retry with different approach"
            }
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a single step with error handling
        Subclasses should override this with actual implementation
        """
        raise NotImplementedError("Subclasses must implement execute_step")
    
    def self_heal(self, error: Exception, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent error recovery using AI
        """
        self._send_update(
            AgentStatus.RETRYING,
            f"Attempting to recover from error: {str(error)}",
            thinking_process="Analyzing error and finding solution..."
        )
        
        # Store error for learning
        self.error_memory.append({
            "error": str(error),
            "step": step,
            "context": context,
            "timestamp": time.time()
        })
        
        prompt = f"""An error occurred while executing this step:
Step: {json.dumps(step, indent=2)}
Error: {str(error)}
Context: {json.dumps(context, indent=2)}

As an intelligent agent, analyze this error and provide:
1. Root cause analysis
2. Alternative approach to achieve the same goal
3. Specific fix or workaround

Respond in JSON:
{{
    "root_cause": "why this happened",
    "alternative_approach": "different way to do it",
    "new_step": {{"step": 1, "action": "...", "tool": "...", "expected_outcome": "..."}},
    "confidence": 0.0-1.0
}}"""

        try:
            response = self._get_execution_model().generate_content(prompt)
            recovery_text = response.text
            
            if "```json" in recovery_text:
                recovery_text = recovery_text.split("```json")[1].split("```")[0].strip()
            elif "```" in recovery_text:
                recovery_text = recovery_text.split("```")[1].split("```")[0].strip()
            
            recovery_plan = json.loads(recovery_text)
            
            self._send_update(
                AgentStatus.RETRYING,
                f"Found alternative approach: {recovery_plan.get('alternative_approach', 'Retrying...')}",
                action_taken=recovery_plan.get('root_cause', '')
            )
            
            # Try the alternative approach
            return self.execute_step(recovery_plan['new_step'], context)
            
        except Exception as heal_error:
            self._send_update(
                AgentStatus.ERROR,
                f"Self-healing failed: {str(heal_error)}",
                thinking_process="Unable to recover automatically"
            )
            raise heal_error
    
    def run(self, task: str, context: Dict[str, Any] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Main execution loop with intelligent planning and error recovery
        """
        self._send_update(
            AgentStatus.THINKING,
            f"Starting task: {task}",
            progress=0
        )
        
        try:
            # Step 1: Think and plan
            plan = self.think(task, context)
            steps = plan.get('steps', [])
            total_steps = len(steps)
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Executing plan with {total_steps} steps",
                progress=25
            )
            
            # Step 2: Execute each step with error handling
            results = []
            for idx, step in enumerate(steps, 1):
                step_progress = 25 + int((idx / total_steps) * 65)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"Step {idx}/{total_steps}: {step.get('action', 'Processing...')}",
                    action_taken=step.get('action', ''),
                    progress=step_progress
                )
                
                retry_count = 0
                step_result = None
                
                while retry_count < max_retries:
                    try:
                        step_result = self.execute_step(step, context or {})
                        results.append(step_result)
                        break  # Success!
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise  # Give up after max retries
                        
                        # Try self-healing
                        try:
                            step_result = self.self_heal(e, step, context or {})
                            results.append(step_result)
                            break  # Self-healing worked!
                        except:
                            continue  # Try again
            
            # Step 3: Success!
            self._send_update(
                AgentStatus.SUCCESS,
                f"Task completed successfully!",
                progress=100
            )
            
            return {
                "success": True,
                "task": task,
                "plan": plan,
                "results": results,
                "agent": self.name
            }
            
        except Exception as e:
            self._send_update(
                AgentStatus.ERROR,
                f"Task failed: {str(e)}",
                progress=0
            )
            
            return {
                "success": False,
                "task": task,
                "error": str(e),
                "agent": self.name
            }
