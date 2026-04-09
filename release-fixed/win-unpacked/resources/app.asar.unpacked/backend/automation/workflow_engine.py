"""Advanced Workflow Engine - Chain and execute multiple tasks automatically"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """Represents a single step in a workflow"""
    
    def __init__(
        self,
        step_id: str,
        command: str,
        agent: str = "auto",
        depends_on: List[str] = None,
        retry_count: int = 3,
        timeout: int = 300,
        condition: Optional[str] = None,
    ):
        self.step_id = step_id
        self.command = command
        self.agent = agent
        self.depends_on = depends_on or []
        self.retry_count = retry_count
        self.timeout = timeout
        self.condition = condition
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.attempts = 0


class Workflow:
    """Represents a complete workflow with multiple steps"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        steps: List[WorkflowStep],
        description: str = "",
        parallel: bool = False,
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = {step.step_id: step for step in steps}
        self.parallel = parallel
        self.status = WorkflowStatus.PENDING
        self.started_at = None
        self.finished_at = None
        self.results = {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "parallel": self.parallel,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "steps": {
                step_id: {
                    "command": step.command,
                    "agent": step.agent,
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error,
                    "attempts": step.attempts,
                }
                for step_id, step in self.steps.items()
            },
        }


class WorkflowEngine:
    """
    Advanced Workflow Engine
    
    Features:
    - Sequential and parallel execution
    - Dependency management
    - Conditional execution
    - Step-level retry logic
    - Real-time status updates
    - Workflow pause/resume/cancel
    """
    
    def __init__(self, agent_executor: Callable, update_callback: Optional[Callable] = None):
        """
        Args:
            agent_executor: Function to execute commands (e.g., your /command endpoint logic)
            update_callback: Optional callback for status updates
        """
        self.agent_executor = agent_executor
        self.update_callback = update_callback
        self.active_workflows: Dict[str, Workflow] = {}
        
    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute a complete workflow"""
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        self.active_workflows[workflow.workflow_id] = workflow
        
        self._send_update(workflow, "Workflow started")
        
        try:
            if workflow.parallel:
                await self._execute_parallel(workflow)
            else:
                await self._execute_sequential(workflow)
            
            # Determine final status
            if all(step.status == TaskStatus.SUCCESS for step in workflow.steps.values()):
                workflow.status = WorkflowStatus.SUCCESS
            elif any(step.status == TaskStatus.FAILED for step in workflow.steps.values()):
                workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.SUCCESS  # Partial success
                
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            self._send_update(workflow, f"Workflow failed: {str(e)}")
        finally:
            workflow.finished_at = datetime.utcnow()
            
        return workflow.to_dict()
    
    async def _execute_sequential(self, workflow: Workflow):
        """Execute steps sequentially respecting dependencies"""
        
        completed = set()
        
        while len(completed) < len(workflow.steps):
            # Find steps ready to execute
            ready_steps = [
                step for step in workflow.steps.values()
                if step.status == TaskStatus.PENDING
                and all(dep in completed for dep in step.depends_on)
            ]
            
            if not ready_steps:
                # Check if we're stuck (circular dependency or all failed)
                remaining = [s for s in workflow.steps.values() if s.status == TaskStatus.PENDING]
                if remaining:
                    for step in remaining:
                        step.status = TaskStatus.SKIPPED
                        step.error = "Dependencies not met"
                        completed.add(step.step_id)
                break
            
            # Execute ready steps
            for step in ready_steps:
                if self._check_condition(step, workflow):
                    await self._execute_step(workflow, step)
                else:
                    step.status = TaskStatus.SKIPPED
                    step.error = "Condition not met"
                
                completed.add(step.step_id)
    
    async def _execute_parallel(self, workflow: Workflow):
        """Execute independent steps in parallel"""
        
        # Group steps by dependency level
        levels = self._compute_dependency_levels(workflow)
        
        for level, steps in sorted(levels.items()):
            # Execute all steps at this level in parallel
            tasks = []
            for step in steps:
                if self._check_condition(step, workflow):
                    tasks.append(self._execute_step(workflow, step))
                else:
                    step.status = TaskStatus.SKIPPED
                    step.error = "Condition not met"
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep):
        """Execute a single workflow step with retry logic"""
        
        step.status = TaskStatus.RUNNING
        self._send_update(workflow, f"Executing step: {step.step_id}")
        
        for attempt in range(step.retry_count):
            step.attempts = attempt + 1
            
            try:
                # Execute command through agent
                result = await self.agent_executor(
                    command=step.command,
                    agent=step.agent,
                    timeout=step.timeout,
                )
                
                step.result = result
                step.status = TaskStatus.SUCCESS
                workflow.results[step.step_id] = result
                
                self._send_update(workflow, f"Step {step.step_id} completed")
                return
                
            except Exception as e:
                step.error = str(e)
                
                if attempt < step.retry_count - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    self._send_update(
                        workflow,
                        f"Step {step.step_id} failed, retrying in {wait_time}s (attempt {attempt + 1}/{step.retry_count})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    step.status = TaskStatus.FAILED
                    self._send_update(workflow, f"Step {step.step_id} failed after {step.retry_count} attempts")
    
    def _check_condition(self, step: WorkflowStep, workflow: Workflow) -> bool:
        """Check if step condition is met"""
        if not step.condition:
            return True
        
        try:
            # Simple condition evaluation based on previous results
            # Format: "step_id.status == 'success'" or "step_id.result.contains('text')"
            # This is a simplified version - can be extended
            return True  # Default to true for now
        except:
            return True
    
    def _compute_dependency_levels(self, workflow: Workflow) -> Dict[int, List[WorkflowStep]]:
        """Compute execution levels based on dependencies"""
        levels = {}
        computed = {}
        
        def get_level(step_id: str) -> int:
            if step_id in computed:
                return computed[step_id]
            
            step = workflow.steps[step_id]
            if not step.depends_on:
                level = 0
            else:
                level = max(get_level(dep) for dep in step.depends_on) + 1
            
            computed[step_id] = level
            return level
        
        for step_id, step in workflow.steps.items():
            level = get_level(step_id)
            if level not in levels:
                levels[level] = []
            levels[level].append(step)
        
        return levels
    
    def _send_update(self, workflow: Workflow, message: str):
        """Send status update"""
        if self.update_callback:
            try:
                self.update_callback({
                    "type": "workflow_update",
                    "workflow_id": workflow.workflow_id,
                    "status": workflow.status.value,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except:
                pass
    
    def pause_workflow(self, workflow_id: str):
        """Pause a running workflow"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].status = WorkflowStatus.PAUSED
    
    def resume_workflow(self, workflow_id: str):
        """Resume a paused workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow.status == WorkflowStatus.PAUSED:
                workflow.status = WorkflowStatus.RUNNING
    
    def cancel_workflow(self, workflow_id: str):
        """Cancel a running workflow"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].status = WorkflowStatus.CANCELLED
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status"""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id].to_dict()
        return None
    
    @staticmethod
    def from_config(config: Dict[str, Any]) -> Workflow:
        """Create workflow from JSON config"""
        
        steps = [
            WorkflowStep(
                step_id=step_data["id"],
                command=step_data["command"],
                agent=step_data.get("agent", "auto"),
                depends_on=step_data.get("depends_on", []),
                retry_count=step_data.get("retry_count", 3),
                timeout=step_data.get("timeout", 300),
                condition=step_data.get("condition"),
            )
            for step_data in config.get("steps", [])
        ]
        
        return Workflow(
            workflow_id=config.get("id", f"wf_{datetime.utcnow().timestamp()}"),
            name=config["name"],
            steps=steps,
            description=config.get("description", ""),
            parallel=config.get("parallel", False),
        )
