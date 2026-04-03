#!/usr/bin/env python3
"""
Atlas-Style Workflow Engine for SIGMA-OS
Execute multi-step workflows with AI-powered task execution
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class StepStatus(Enum):
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
        action: str,
        tool: str,
        params: Dict[str, Any] = None,
        condition: Optional[str] = None,
        retry_count: int = 3
    ):
        self.step_id = step_id
        self.action = action
        self.tool = tool
        self.params = params or {}
        self.condition = condition
        self.retry_count = retry_count
        self.status = StepStatus.PENDING
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.attempts = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_id": self.step_id,
            "action": self.action,
            "tool": self.tool,
            "params": self.params,
            "condition": self.condition,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts
        }

class Workflow:
    """Represents a complete workflow"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        steps: List[WorkflowStep] = None
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps or []
        self.status = WorkflowStatus.PENDING
        self.context = {}  # Shared context between steps
        self.start_time = None
        self.end_time = None
        self.current_step_index = 0
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "context": self.context,
            "current_step": self.current_step_index,
            "total_steps": len(self.steps)
        }

class AtlasWorkflowEngine:
    """
    Atlas-style workflow engine
    - Executes multi-step workflows
    - Passes output from one step to next
    - Handles branching and conditions
    - Supports retries and error recovery
    """
    
    def __init__(self, agents: Dict[str, Any] = None):
        self.agents = agents or {}
        self.workflows = {}
        self.tool_registry = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tool functions"""
        
        # Web tools
        self.tool_registry["web_navigate"] = self._web_navigate
        self.tool_registry["web_search"] = self._web_search
        self.tool_registry["web_extract"] = self._web_extract
        self.tool_registry["web_click"] = self._web_click
        self.tool_registry["web_type"] = self._web_type
        self.tool_registry["web_screenshot"] = self._web_screenshot
        
        # Email tools
        self.tool_registry["email_send"] = self._email_send
        self.tool_registry["email_read"] = self._email_read
        
        # System tools
        self.tool_registry["system_command"] = self._system_command
        self.tool_registry["file_read"] = self._file_read
        self.tool_registry["file_write"] = self._file_write
        
        # Data tools
        self.tool_registry["extract_data"] = self._extract_data
        self.tool_registry["transform_data"] = self._transform_data
        self.tool_registry["llm_analyze"] = self._llm_analyze
    
    def register_tool(self, tool_name: str, tool_function: Callable):
        """Register a custom tool function"""
        self.tool_registry[tool_name] = tool_function
        logger.info(f"Registered tool: {tool_name}")
    
    def create_workflow_from_task(self, task: str, context: Dict[str, Any] = None) -> Workflow:
        """
        Create a workflow from a natural language task using AI
        This is the Atlas magic - AI breaks down complex tasks into steps
        """
        from .model_manager import model_manager
        
        prompt = f"""Break down this task into a workflow with specific steps:

Task: {task}
Context: {json.dumps(context or {}, indent=2)}

Create a workflow with these details:
- workflow_id: unique identifier
- name: short name
- description: what the workflow does
- steps: array of steps, each with:
  - step_id: unique step identifier (step_1, step_2, etc)
  - action: what to do
  - tool: which tool to use (web_navigate, web_search, web_extract, email_send, system_command, llm_analyze, etc)
  - params: parameters for the tool (use {{prev_result}} to reference previous step output)
  - condition: optional condition to execute (e.g., "if prev_result.success")

Available tools:
- web_navigate: Navigate to URL (params: url)
- web_search: Search on Google (params: query)
- web_extract: Extract data from page (params: selector or description)
- web_click: Click element (params: selector)
- web_type: Type text (params: selector, text)
- web_screenshot: Take screenshot (params: filename)
- email_send: Send email (params: to, subject, body)
- email_read: Read emails (params: query)
- system_command: Run system command (params: command)
- file_read: Read file (params: path)
- file_write: Write file (params: path, content)
- llm_analyze: Analyze data with AI (params: data, question)
- extract_data: Extract specific data (params: source, pattern)
- transform_data: Transform data (params: data, transformation)

Respond with ONLY valid JSON matching this structure."""

        try:
            model = model_manager.get_best_model()
            response = model.generate_content(prompt)
            workflow_data = response.text.strip()
            
            # Clean up JSON
            if "```json" in workflow_data:
                workflow_data = workflow_data.split("```json")[1].split("```")[0].strip()
            elif "```" in workflow_data:
                workflow_data = workflow_data.split("```")[1].split("```")[0].strip()
            
            data = json.loads(workflow_data)
            
            # Create workflow
            workflow = Workflow(
                workflow_id=data.get("workflow_id", f"wf_{int(time.time())}"),
                name=data.get("name", "Custom Workflow"),
                description=data.get("description", "")
            )
            
            # Add steps
            for step_data in data.get("steps", []):
                step = WorkflowStep(
                    step_id=step_data.get("step_id", f"step_{len(workflow.steps) + 1}"),
                    action=step_data.get("action", ""),
                    tool=step_data.get("tool", ""),
                    params=step_data.get("params", {}),
                    condition=step_data.get("condition")
                )
                workflow.add_step(step)
            
            self.workflows[workflow.workflow_id] = workflow
            logger.info(f"Created workflow: {workflow.name} with {len(workflow.steps)} steps")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            # Fallback: create simple workflow
            workflow = Workflow(
                workflow_id=f"wf_{int(time.time())}",
                name="Simple Task",
                description=task
            )
            workflow.add_step(WorkflowStep(
                step_id="step_1",
                action=task,
                tool="system_command",
                params={"task": task}
            ))
            return workflow
    
    def execute_workflow(self, workflow: Workflow, update_callback: Callable = None) -> Dict[str, Any]:
        """
        Execute a workflow step by step
        """
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now()
        
        logger.info(f"🚀 Starting workflow: {workflow.name}")
        
        try:
            for i, step in enumerate(workflow.steps):
                workflow.current_step_index = i
                
                # Check condition
                if step.condition and not self._evaluate_condition(step.condition, workflow.context):
                    step.status = StepStatus.SKIPPED
                    logger.info(f"⏭️  Skipped step {step.step_id}: condition not met")
                    continue
                
                # Execute step with retries
                step.status = StepStatus.RUNNING
                step.start_time = datetime.now()
                
                if update_callback:
                    update_callback(f"Executing step {i+1}/{len(workflow.steps)}: {step.action}")
                
                logger.info(f"▶️  Step {i+1}/{len(workflow.steps)}: {step.action}")
                
                success = False
                for attempt in range(step.retry_count):
                    step.attempts = attempt + 1
                    
                    try:
                        result = self._execute_step(step, workflow.context)
                        
                        if result and result.get("success", False):
                            step.result = result
                            step.status = StepStatus.SUCCESS
                            step.end_time = datetime.now()
                            
                            # Store result in context for next steps
                            workflow.context[step.step_id] = result
                            workflow.context["prev_result"] = result
                            workflow.context["last_success"] = result
                            
                            logger.info(f"✅ Step {step.step_id} completed successfully")
                            success = True
                            break
                        else:
                            error = result.get("error", "Unknown error") if result else "No result"
                            raise Exception(error)
                            
                    except Exception as e:
                        step.error = str(e)
                        logger.warning(f"⚠️  Step {step.step_id} attempt {attempt+1} failed: {str(e)}")
                        
                        if attempt < step.retry_count - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            step.status = StepStatus.FAILED
                            step.end_time = datetime.now()
                
                if not success:
                    workflow.status = WorkflowStatus.FAILED
                    logger.error(f"❌ Workflow failed at step: {step.step_id}")
                    break
            
            # Workflow completed
            if workflow.status != WorkflowStatus.FAILED:
                workflow.status = WorkflowStatus.COMPLETED
                logger.info(f"🎉 Workflow completed successfully: {workflow.name}")
            
            workflow.end_time = datetime.now()
            
            return {
                "success": workflow.status == WorkflowStatus.COMPLETED,
                "workflow": workflow.to_dict(),
                "final_result": workflow.context.get("last_success"),
                "execution_time": (workflow.end_time - workflow.start_time).total_seconds()
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now()
            logger.error(f"💥 Workflow execution error: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "workflow": workflow.to_dict()
            }
    
    def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        # Resolve parameters with context
        params = self._resolve_params(step.params, context)
        
        # Get tool function
        tool_func = self.tool_registry.get(step.tool)
        if not tool_func:
            raise Exception(f"Unknown tool: {step.tool}")
        
        # Execute tool
        return tool_func(params, context)
    
    def _resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter values from context"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Replace {{prev_result}} or {{step_id.field}}
                if "{{" in value and "}}" in value:
                    # Extract variable name
                    import re
                    matches = re.findall(r'\{\{([^}]+)\}\}', value)
                    for match in matches:
                        if '.' in match:
                            # Reference to specific field
                            parts = match.split('.')
                            val = context
                            for part in parts:
                                val = val.get(part, {}) if isinstance(val, dict) else None
                            value = value.replace(f"{{{{{match}}}}}", str(val) if val is not None else "")
                        else:
                            # Reference to whole object
                            val = context.get(match, "")
                            value = value.replace(f"{{{{{match}}}}}", str(val))
                
                resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string"""
        try:
            # Simple condition evaluation
            # Support: "if prev_result.success", "if step_1.data.count > 5", etc.
            condition = condition.replace("if ", "").strip()
            
            # Resolve variables
            for key, value in context.items():
                if key in condition:
                    condition = condition.replace(key, f"context['{key}']")
            
            # Safely evaluate
            return eval(condition, {"context": context})
        except:
            return True  # Default to true if condition can't be evaluated
    
    # ========== TOOL IMPLEMENTATIONS ==========
    
    def _web_navigate(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        if "web" in self.agents:
            url = params.get("url", "")
            return self.agents["web"].run(f"go to {url}")
        return {"success": False, "error": "Web agent not available"}
    
    def _web_search(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Search on Google"""
        if "web" in self.agents:
            query = params.get("query", "")
            return self.agents["web"].run(f"search for {query}")
        return {"success": False, "error": "Web agent not available"}
    
    def _web_extract(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from current page"""
        if "web" in self.agents:
            description = params.get("description", params.get("selector", ""))
            return self.agents["web"].run(f"extract {description}")
        return {"success": False, "error": "Web agent not available"}
    
    def _web_click(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element"""
        if "web" in self.agents:
            selector = params.get("selector", "")
            return self.agents["web"].run(f"click {selector}")
        return {"success": False, "error": "Web agent not available"}
    
    def _web_type(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element"""
        if "web" in self.agents:
            selector = params.get("selector", "")
            text = params.get("text", "")
            return self.agents["web"].run(f"type '{text}' in {selector}")
        return {"success": False, "error": "Web agent not available"}
    
    def _web_screenshot(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot"""
        if "web" in self.agents:
            filename = params.get("filename", "screenshot.png")
            return self.agents["web"].run(f"take screenshot as {filename}")
        return {"success": False, "error": "Web agent not available"}
    
    def _email_send(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email"""
        if "email" in self.agents:
            to = params.get("to", "")
            subject = params.get("subject", "")
            body = params.get("body", "")
            return self.agents["email"].run(f"send email to {to} with subject '{subject}' and body: {body}")
        return {"success": False, "error": "Email agent not available"}
    
    def _email_read(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Read emails"""
        if "email" in self.agents:
            query = params.get("query", "latest emails")
            return self.agents["email"].run(f"show {query}")
        return {"success": False, "error": "Email agent not available"}
    
    def _system_command(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system command"""
        if "system" in self.agents:
            task = params.get("task", params.get("command", ""))
            return self.agents["system"].run(task)
        return {"success": False, "error": "System agent not available"}
    
    def _file_read(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file"""
        try:
            path = params.get("path", "")
            with open(path, 'r') as f:
                content = f.read()
            return {"success": True, "content": content, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _file_write(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file"""
        try:
            path = params.get("path", "")
            content = params.get("content", "")
            with open(path, 'w') as f:
                f.write(content)
            return {"success": True, "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_data(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data using pattern"""
        import re
        try:
            source = params.get("source", "")
            pattern = params.get("pattern", "")
            matches = re.findall(pattern, source)
            return {"success": True, "matches": matches, "count": len(matches)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _transform_data(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data"""
        try:
            data = params.get("data", "")
            transformation = params.get("transformation", "")
            # Simple transformations
            if transformation == "uppercase":
                result = str(data).upper()
            elif transformation == "lowercase":
                result = str(data).lower()
            elif transformation == "json_parse":
                result = json.loads(data)
            else:
                result = data
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _llm_analyze(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data with AI"""
        try:
            from .model_manager import model_manager
            
            data = params.get("data", "")
            question = params.get("question", "Analyze this data")
            
            prompt = f"{question}\n\nData:\n{data}"
            
            model = model_manager.get_best_model()
            response = model.generate_content(prompt)
            
            return {
                "success": True,
                "analysis": response.text,
                "model": str(model)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
