#!/usr/bin/env python3
"""
Reasoning MCP Server
Helps agents make intelligent decisions by evaluating multiple approaches
Provides structured reasoning, confidence scoring, and decision analysis
"""

import json
from typing import Dict, Any, List, Optional
import time

from ..mcp_base import MCPServer, MCPTool, MCPResponse, ToolType


class ReasoningMCPServer(MCPServer):
    """
    MCP Server for intelligent reasoning and decision-making.
    Helps agents evaluate options, estimate risks, and make better decisions.
    """
    
    def __init__(self):
        super().__init__(
            name="reasoning",
            description="Intelligent reasoning engine - helps agents make better decisions"
        )
    
    def _register_tools(self):
        """Register reasoning tools"""
        
        self.register_tool(MCPTool(
            name="evaluate_approaches",
            description="Evaluate multiple approaches to a task and score them",
            tool_type=ToolType.ANALYZE,
            parameters={
                "task": "str - Task description",
                "approaches": "list of str - Different ways to accomplish the task",
                "constraints": "list of str - Constraints to consider"
            },
            required_params=["task", "approaches"],
            returns={
                "evaluations": "list of dicts with approach, score, pros, cons",
                "recommended": "str - Best approach",
                "confidence": "float 0.0-1.0"
            }
        ))
        
        self.register_tool(MCPTool(
            name="estimate_complexity",
            description="Estimate task complexity and required resources",
            tool_type=ToolType.ANALYZE,
            parameters={
                "task": "str - Task description",
                "context": "dict - Additional context"
            },
            required_params=["task"],
            returns={
                "complexity_score": "float 0.0-1.0",
                "estimated_steps": "int",
                "required_tools": "list of str",
                "potential_risks": "list of str"
            }
        ))
        
        self.register_tool(MCPTool(
            name="analyze_risk",
            description="Analyze risks in a proposed action",
            tool_type=ToolType.ANALYZE,
            parameters={
                "action": "str - Proposed action",
                "context": "dict - Context/situation"
            },
            required_params=["action"],
            returns={
                "risk_level": "str - low/medium/high/critical",
                "risk_score": "float 0.0-1.0",
                "potential_issues": "list of str",
                "mitigations": "list of str"
            }
        ))
        
        self.register_tool(MCPTool(
            name="should_attempt_task",
            description="Determine if agent should attempt a task given current state",
            tool_type=ToolType.ANALYZE,
            parameters={
                "task": "str - Task to evaluate",
                "capabilities": "list of str - Available tools/skills",
                "constraints": "dict - Current constraints"
            },
            required_params=["task", "capabilities"],
            returns={
                "should_attempt": "bool",
                "confidence": "float 0.0-1.0",
                "reason": "str",
                "requirements": "list of str"
            }
        ))
        
        self.register_tool(MCPTool(
            name="compare_options",
            description="Compare multiple options for a decision",
            tool_type=ToolType.ANALYZE,
            parameters={
                "decision": "str - Decision to make",
                "options": "list of str - Options to compare",
                "criteria": "list of str - Evaluation criteria"
            },
            required_params=["decision", "options", "criteria"],
            returns={
                "comparison": "dict mapping options to scores",
                "best_option": "str",
                "trade_offs": "list of str"
            }
        ))
    
    def initialize(self) -> bool:
        """Initialize reasoning server"""
        self.is_ready = True
        print("✅ Reasoning MCP Server initialized")
        return True
    
    def call_tool(self, tool_name: str, **kwargs) -> MCPResponse:
        """Execute reasoning tool"""
        try:
            if tool_name == "evaluate_approaches":
                return self._evaluate_approaches(**kwargs)
            elif tool_name == "estimate_complexity":
                return self._estimate_complexity(**kwargs)
            elif tool_name == "analyze_risk":
                return self._analyze_risk(**kwargs)
            elif tool_name == "should_attempt_task":
                return self._should_attempt_task(**kwargs)
            elif tool_name == "compare_options":
                return self._compare_options(**kwargs)
            else:
                return MCPResponse(
                    success=False,
                    data=None,
                    error=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return MCPResponse(
                success=False,
                data=None,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def _evaluate_approaches(self, **kwargs) -> MCPResponse:
        """Evaluate multiple approaches"""
        task = kwargs.get("task")
        approaches = kwargs.get("approaches", [])
        constraints = kwargs.get("constraints", [])
        
        evaluations = []
        max_score = 0
        best_approach = None
        
        for i, approach in enumerate(approaches):
            # Simple scoring heuristic
            # In production, use AI model here
            score = self._calculate_approach_score(approach, task, constraints)
            
            evaluation = {
                "approach": approach,
                "score": score,
                "pros": self._get_approach_pros(approach),
                "cons": self._get_approach_cons(approach),
                "rank": i + 1
            }
            evaluations.append(evaluation)
            
            if score > max_score:
                max_score = score
                best_approach = approach
        
        # Sort by score
        evaluations.sort(key=lambda x: x["score"], reverse=True)
        
        confidence = min(max_score, 1.0)
        
        return MCPResponse(
            success=True,
            data={
                "evaluations": evaluations,
                "recommended": best_approach,
                "recommendation_confidence": confidence,
                "task": task
            }
        )
    
    def _estimate_complexity(self, **kwargs) -> MCPResponse:
        """Estimate task complexity"""
        task = kwargs.get("task")
        context = kwargs.get("context", {})
        
        # Heuristics for complexity estimation
        task_lower = task.lower()
        
        complexity_score = 0.5
        estimated_steps = 1
        required_tools = []
        risks = []
        
        # Email tasks
        if any(word in task_lower for word in ["email", "send", "compose", "mail"]):
            complexity_score = 0.3
            estimated_steps = 2
            required_tools = ["email_api", "smtp"]
        
        # File operations
        elif any(word in task_lower for word in ["file", "write", "read", "delete", "create"]):
            complexity_score = 0.4
            estimated_steps = 2
            required_tools = ["file_system"]
            if "delete" in task_lower:
                risks.append("Permanent data loss possible")
        
        # Web operations
        elif any(word in task_lower for word in ["web", "browse", "scrape", "fetch", "http"]):
            complexity_score = 0.6
            estimated_steps = 3
            required_tools = ["web_browser", "http_client"]
            risks.append("Network timeout possible")
            risks.append("Website structure may change")
        
        # System operations
        elif any(word in task_lower for word in ["execute", "command", "shell", "system", "process"]):
            complexity_score = 0.7
            estimated_steps = 2
            required_tools = ["shell", "process_manager"]
            risks.append("May require elevated privileges")
            risks.append("Unintended side effects possible")
        
        if len(context) > 0:
            complexity_score = min(complexity_score + 0.1, 1.0)
        
        return MCPResponse(
            success=True,
            data={
                "complexity_score": complexity_score,
                "complexity_level": self._score_to_level(complexity_score),
                "estimated_steps": estimated_steps,
                "required_tools": required_tools,
                "potential_risks": risks,
                "task": task
            }
        )
    
    def _analyze_risk(self, **kwargs) -> MCPResponse:
        """Analyze risks in a proposed action"""
        action = kwargs.get("action")
        context = kwargs.get("context", {})
        
        action_lower = action.lower()
        risk_score = 0.3  # Default: low risk
        risk_level = "low"
        issues = []
        mitigations = []
        
        # Delete/destructive operations
        if any(word in action_lower for word in ["delete", "remove", "destroy", "rm -rf", "format"]):
            risk_score = 0.9
            risk_level = "critical"
            issues.append("Irreversible data loss")
            mitigations.append("Create backup first")
            mitigations.append("Confirm before execution")
        
        # System commands
        elif any(word in action_lower for word in ["sudo", "chmod", "chown", "kill", "shutdown"]):
            risk_score = 0.8
            risk_level = "high"
            issues.append("Could affect system stability")
            issues.append("May require special privileges")
            mitigations.append("Run in test environment first")
        
        # Network operations
        elif any(word in action_lower for word in ["curl", "wget", "upload", "download"]):
            risk_score = 0.4
            risk_level = "medium"
            issues.append("Network timeout possible")
            issues.append("File corruption during transfer")
            mitigations.append("Verify checksums")
        
        # Email operations
        elif any(word in action_lower for word in ["send", "email", "spam"]):
            risk_score = 0.5
            risk_level = "medium"
            issues.append("May send unwanted emails")
            mitigations.append("Review draft before sending")
        
        return MCPResponse(
            success=True,
            data={
                "risk_level": risk_level,
                "risk_score": risk_score,
                "potential_issues": issues,
                "mitigations": mitigations,
                "action": action
            }
        )
    
    def _should_attempt_task(self, **kwargs) -> MCPResponse:
        """Determine if agent should attempt a task"""
        task = kwargs.get("task")
        capabilities = kwargs.get("capabilities", [])
        constraints = kwargs.get("constraints", {})
        
        should_attempt = True
        confidence = 0.8
        reason = "Task appears achievable"
        requirements = []
        
        # Check if task is too risky
        if any(word in task.lower() for word in ["delete all", "format drive", "rm -rf /"]):
            should_attempt = False
            confidence = 0.95
            reason = "Task is too risky and destructive"
        
        # Check if capabilities are sufficient
        required_tools = self._extract_required_tools(task)
        available_tools = set(c.lower() for c in capabilities)
        
        missing_tools = []
        for tool in required_tools:
            if tool not in available_tools:
                missing_tools.append(tool)
        
        if missing_tools:
            should_attempt = False
            confidence = 0.9
            reason = f"Missing required tools: {', '.join(missing_tools)}"
            requirements = missing_tools
        
        # Check constraints
        if constraints.get("readonly", False):
            if any(word in task.lower() for word in ["write", "delete", "modify", "create"]):
                should_attempt = False
                confidence = 0.85
                reason = "Write operations not allowed (read-only mode)"
        
        return MCPResponse(
            success=True,
            data={
                "should_attempt": should_attempt,
                "confidence": confidence,
                "reason": reason,
                "requirements": requirements,
                "task": task
            }
        )
    
    def _compare_options(self, **kwargs) -> MCPResponse:
        """Compare multiple options"""
        decision = kwargs.get("decision")
        options = kwargs.get("options", [])
        criteria = kwargs.get("criteria", ["efficiency", "safety", "cost"])
        
        comparison = {}
        best_option = None
        best_score = -1
        
        for option in options:
            score = 0
            for criterion in criteria:
                # Simple heuristic scoring
                criterion_score = self._score_option_by_criterion(option, criterion)
                score += criterion_score
            
            score = score / len(criteria) if criteria else 0
            comparison[option] = {
                "overall_score": score,
                "details": {c: self._score_option_by_criterion(option, c) for c in criteria}
            }
            
            if score > best_score:
                best_score = score
                best_option = option
        
        trade_offs = self._identify_tradeoffs(options, criteria, comparison)
        
        return MCPResponse(
            success=True,
            data={
                "comparison": comparison,
                "best_option": best_option,
                "best_score": best_score,
                "trade_offs": trade_offs,
                "decision": decision
            }
        )
    
    # Helper methods
    
    def _calculate_approach_score(self, approach: str, task: str, constraints: List[str]) -> float:
        """Calculate score for an approach"""
        score = 0.5
        
        if "simple" in approach.lower() or "direct" in approach.lower():
            score += 0.2
        if "safe" in approach.lower():
            score += 0.15
        if "fast" in approach.lower():
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_approach_pros(self, approach: str) -> List[str]:
        """Get pros for an approach"""
        pros = []
        if "simple" in approach.lower():
            pros.append("Easy to understand and implement")
        if "safe" in approach.lower():
            pros.append("Lower risk of failure")
        if "fast" in approach.lower():
            pros.append("Quick execution")
        return pros or ["Straightforward approach"]
    
    def _get_approach_cons(self, approach: str) -> List[str]:
        """Get cons for an approach"""
        cons = []
        if "slow" in approach.lower():
            cons.append("May take longer to complete")
        if "risky" in approach.lower():
            cons.append("Higher failure risk")
        if "complex" in approach.lower():
            cons.append("More difficult to implement")
        return cons or []
    
    def _score_to_level(self, score: float) -> str:
        """Convert score to level"""
        if score < 0.3:
            return "trivial"
        elif score < 0.6:
            return "moderate"
        elif score < 0.8:
            return "complex"
        else:
            return "very_complex"
    
    def _extract_required_tools(self, task: str) -> List[str]:
        """Extract required tools from task description"""
        tools = set()
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["email", "send", "compose"]):
            tools.add("email_api")
        if any(word in task_lower for word in ["web", "browse", "http", "fetch"]):
            tools.add("web_browser")
        if any(word in task_lower for word in ["file", "read", "write"]):
            tools.add("file_system")
        if any(word in task_lower for word in ["execute", "command", "shell"]):
            tools.add("shell")
        
        return list(tools)
    
    def _score_option_by_criterion(self, option: str, criterion: str) -> float:
        """Score an option by a criterion"""
        option_lower = option.lower()
        
        if criterion == "efficiency":
            if "quick" in option_lower or "fast" in option_lower:
                return 0.9
            elif "slow" in option_lower:
                return 0.3
            return 0.6
        
        elif criterion == "safety":
            if "safe" in option_lower or "careful" in option_lower:
                return 0.9
            elif "risky" in option_lower or "dangerous" in option_lower:
                return 0.2
            return 0.6
        
        elif criterion == "cost":
            if "cheap" in option_lower or "free" in option_lower:
                return 0.9
            elif "expensive" in option_lower:
                return 0.2
            return 0.6
        
        return 0.5
    
    def _identify_tradeoffs(self, options: List[str], criteria: List[str], comparison: Dict) -> List[str]:
        """Identify trade-offs between options"""
        tradeoffs = []
        
        if len(options) < 2:
            return tradeoffs
        
        # Find options with opposite strengths
        scores_by_criterion = {}
        for criterion in criteria:
            scores_by_criterion[criterion] = {
                opt: comparison[opt]["details"].get(criterion, 0.5)
                for opt in options
            }
        
        for criterion in criteria:
            max_score = max(scores_by_criterion[criterion].values())
            min_score = min(scores_by_criterion[criterion].values())
            if max_score - min_score > 0.3:
                best = [o for o in options if scores_by_criterion[criterion][o] == max_score][0]
                worst = [o for o in options if scores_by_criterion[criterion][o] == min_score][0]
                tradeoffs.append(f"{best} is better for {criterion}, but {worst} is worse")
        
        return tradeoffs
