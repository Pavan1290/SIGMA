"""Advanced Automation System for SIGMA-OS

Provides:
- Workflow engine for task chaining
- Smart task scheduler
- Error recovery with retry logic
- Performance monitoring
- Rules engine
- Agent orchestration
"""

from .workflow_engine import WorkflowEngine
from .task_scheduler import TaskScheduler
from .error_recovery import ErrorRecovery
from .monitoring import PerformanceMonitor
from .rules_engine import RulesEngine
from .orchestrator import AgentOrchestrator

__all__ = [
    "WorkflowEngine",
    "TaskScheduler",
    "ErrorRecovery",
    "PerformanceMonitor",
    "RulesEngine",
    "AgentOrchestrator",
]
