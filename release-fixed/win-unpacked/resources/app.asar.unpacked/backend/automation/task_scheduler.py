"""Smart Task Scheduler - Schedule and queue tasks intelligently"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque
import heapq
from enum import Enum


class ScheduleType(str, Enum):
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    CONDITIONAL = "conditional"


class ScheduledTask:
    """Represents a scheduled task"""
    
    def __init__(
        self,
        task_id: str,
        workflow_id: str,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        enabled: bool = True,
        max_runs: Optional[int] = None,
    ):
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.schedule_type = schedule_type
        self.schedule_config = schedule_config
        self.enabled = enabled
        self.max_runs = max_runs
        self.run_count = 0
        self.last_run = None
        self.next_run = None
        self.priority = schedule_config.get("priority", 5)
        
    def should_run(self) -> bool:
        """Check if task should run now"""
        if not self.enabled:
            return False
        
        if self.max_runs and self.run_count >= self.max_runs:
            return False
        
        if not self.next_run:
            return True
        
        return datetime.utcnow() >= self.next_run
    
    def calculate_next_run(self):
        """Calculate next run time"""
        now = datetime.utcnow()
        
        if self.schedule_type == ScheduleType.ONCE:
            # One-time execution
            if self.run_count == 0:
                scheduled_time = self.schedule_config.get("datetime")
                if scheduled_time:
                    self.next_run = datetime.fromisoformat(scheduled_time)
                else:
                    self.next_run = now
            else:
                self.next_run = None  # Already ran
                
        elif self.schedule_type == ScheduleType.INTERVAL:
            # Interval-based (e.g., every 5 minutes)
            interval_seconds = self.schedule_config.get("interval_seconds", 300)
            if self.last_run:
                self.next_run = self.last_run + timedelta(seconds=interval_seconds)
            else:
                self.next_run = now + timedelta(seconds=interval_seconds)
                
        elif self.schedule_type == ScheduleType.CRON:
            # Cron-like scheduling (simplified)
            # Format: {"minute": 0, "hour": 12, "day_of_week": "*"}
            # This is simplified - use APScheduler for full cron support
            self.next_run = self._calculate_cron_next_run(now)
            
        elif self.schedule_type == ScheduleType.CONDITIONAL:
            # Run when condition is met
            # Checked externally by rules engine
            self.next_run = now
    
    def _calculate_cron_next_run(self, from_time: datetime) -> datetime:
        """Calculate next run based on cron-like config"""
        # Simplified cron calculation
        # In production, use APScheduler's CronTrigger
        
        minute = self.schedule_config.get("minute", "*")
        hour = self.schedule_config.get("hour", "*")
        
        next_run = from_time + timedelta(minutes=1)
        
        # Simple logic for hourly/daily patterns
        if hour != "*" and minute != "*":
            # Daily at specific time
            next_run = from_time.replace(hour=int(hour), minute=int(minute), second=0)
            if next_run <= from_time:
                next_run += timedelta(days=1)
        elif minute != "*":
            # Hourly at specific minute
            next_run = from_time.replace(minute=int(minute), second=0)
            if next_run <= from_time:
                next_run += timedelta(hours=1)
        
        return next_run


class TaskQueue:
    """Priority queue for task execution"""
    
    def __init__(self):
        self._queue = []
        self._counter = 0
        
    def push(self, task: ScheduledTask, priority: int = None):
        """Add task to queue with priority"""
        if priority is None:
            priority = task.priority
        
        # Lower number = higher priority
        # Counter ensures FIFO for same priority
        heapq.heappush(self._queue, (priority, self._counter, task))
        self._counter += 1
    
    def pop(self) -> Optional[ScheduledTask]:
        """Get highest priority task"""
        if self._queue:
            return heapq.heappop(self._queue)[2]
        return None
    
    def peek(self) -> Optional[ScheduledTask]:
        """View highest priority task without removing"""
        if self._queue:
            return self._queue[0][2]
        return None
    
    def size(self) -> int:
        return len(self._queue)
    
    def clear(self):
        self._queue.clear()


class TaskScheduler:
    """
    Smart Task Scheduler
    
    Features:
    - Multiple schedule types (once, interval, cron, conditional)
    - Priority-based execution queue
    - Concurrent task limiting
    - Automatic rescheduling
    - Task dependency awareness
    """
    
    def __init__(
        self,
        workflow_executor: Callable,
        max_concurrent: int = 5,
        check_interval: int = 10,
    ):
        """
        Args:
            workflow_executor: Function to execute workflows
            max_concurrent: Max concurrent workflow executions
            check_interval: Seconds between schedule checks
        """
        self.workflow_executor = workflow_executor
        self.max_concurrent = max_concurrent
        self.check_interval = check_interval
        
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_queue = TaskQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        self._running = False
        self._scheduler_task = None
    
    async def start(self):
        """Start the scheduler loop"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        print("✅ Task Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        print("🛑 Task Scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Check for tasks ready to run
                for task in list(self.scheduled_tasks.values()):
                    if task.should_run():
                        self.task_queue.push(task)
                        task.calculate_next_run()
                
                # Execute queued tasks (respecting concurrency limit)
                while (
                    self.task_queue.size() > 0
                    and len(self.running_tasks) < self.max_concurrent
                ):
                    scheduled_task = self.task_queue.pop()
                    if scheduled_task:
                        await self._execute_scheduled_task(scheduled_task)
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"⚠️  Scheduler error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _execute_scheduled_task(self, scheduled_task: ScheduledTask):
        """Execute a scheduled task"""
        
        async def run():
            try:
                scheduled_task.run_count += 1
                scheduled_task.last_run = datetime.utcnow()
                
                # Execute the workflow
                await self.workflow_executor(scheduled_task.workflow_id)
                
            except Exception as e:
                print(f"❌ Scheduled task {scheduled_task.task_id} failed: {e}")
            finally:
                # Remove from running tasks
                if scheduled_task.task_id in self.running_tasks:
                    del self.running_tasks[scheduled_task.task_id]
                
                # Reschedule if needed
                if scheduled_task.enabled:
                    scheduled_task.calculate_next_run()
        
        # Start task execution
        task = asyncio.create_task(run())
        self.running_tasks[scheduled_task.task_id] = task
    
    def add_scheduled_task(self, scheduled_task: ScheduledTask):
        """Add a new scheduled task"""
        scheduled_task.calculate_next_run()
        self.scheduled_tasks[scheduled_task.task_id] = scheduled_task
        print(f"✅ Scheduled task added: {scheduled_task.task_id} (next run: {scheduled_task.next_run})")
    
    def remove_scheduled_task(self, task_id: str):
        """Remove a scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            print(f"🗑️  Scheduled task removed: {task_id}")
    
    def enable_task(self, task_id: str):
        """Enable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = True
            self.scheduled_tasks[task_id].calculate_next_run()
    
    def disable_task(self, task_id: str):
        """Disable a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].enabled = False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get scheduled task status"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks[task_id]
            return {
                "task_id": task.task_id,
                "workflow_id": task.workflow_id,
                "schedule_type": task.schedule_type.value,
                "enabled": task.enabled,
                "run_count": task.run_count,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "is_running": task.task_id in self.running_tasks,
            }
        return None
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        return [
            self.get_task_status(task_id)
            for task_id in self.scheduled_tasks.keys()
        ]
