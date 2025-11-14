"""Advanced Performance Monitoring - Track metrics and agent health"""

import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
import asyncio


class MetricType:
    """Metric type constants"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class Metric:
    """Represents a single metric"""
    
    def __init__(self, name: str, metric_type: str, value: Any, timestamp: datetime = None):
        self.name = name
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp or datetime.utcnow()
        self.tags = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.metric_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


class MetricBuffer:
    """Ring buffer for storing time-series metrics"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
        self.max_size = max_size
    
    def add(self, metric: Metric):
        self.buffer.append(metric)
    
    def get_recent(self, count: int = 10) -> List[Metric]:
        """Get most recent metrics"""
        return list(self.buffer)[-count:]
    
    def get_range(self, start_time: datetime, end_time: datetime) -> List[Metric]:
        """Get metrics in time range"""
        return [
            m for m in self.buffer
            if start_time <= m.timestamp <= end_time
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistics"""
        if not self.buffer:
            return {}
        
        values = [m.value for m in self.buffer if isinstance(m.value, (int, float))]
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }


class AgentHealthStatus:
    """Health status for an agent"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.is_healthy = True
        self.last_heartbeat = datetime.utcnow()
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.avg_response_time = 0.0
        self.error_rate = 0.0
        self.last_error = None
        self.last_error_time = None
    
    def update_heartbeat(self):
        self.last_heartbeat = datetime.utcnow()
    
    def record_success(self, response_time: float):
        self.total_tasks += 1
        self.successful_tasks += 1
        self._update_avg_response_time(response_time)
        self._update_error_rate()
        self.is_healthy = True
    
    def record_failure(self, error: str):
        self.total_tasks += 1
        self.failed_tasks += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()
        self._update_error_rate()
        
        # Mark unhealthy if error rate > 50%
        if self.error_rate > 0.5:
            self.is_healthy = False
    
    def _update_avg_response_time(self, new_time: float):
        """Update average response time"""
        if self.successful_tasks == 1:
            self.avg_response_time = new_time
        else:
            # Exponential moving average
            alpha = 0.2
            self.avg_response_time = (
                alpha * new_time + (1 - alpha) * self.avg_response_time
            )
    
    def _update_error_rate(self):
        """Update error rate"""
        if self.total_tasks > 0:
            self.error_rate = self.failed_tasks / self.total_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "is_healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / self.total_tasks if self.total_tasks > 0 else 0,
            "error_rate": self.error_rate,
            "avg_response_time_ms": self.avg_response_time * 1000,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class PerformanceMonitor:
    """
    Advanced Performance Monitoring System
    
    Features:
    - Real-time metrics collection
    - System resource monitoring (CPU, memory, disk)
    - Agent health tracking
    - Performance statistics
    - Alert thresholds
    - Time-series data storage
    """
    
    def __init__(self, alert_callback: Optional[callable] = None):
        self.metrics: Dict[str, MetricBuffer] = {}
        self.agent_health: Dict[str, AgentHealthStatus] = {}
        self.system_metrics = MetricBuffer(max_size=500)
        self.alert_callback = alert_callback
        
        # Alert thresholds
        self.thresholds = {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "disk_percent": 90.0,
            "agent_error_rate": 0.5,
            "response_time_ms": 10000,
        }
        
        self._monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval: int = 30):
        """Start background system monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        print("✅ Performance Monitor started")
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        print("🛑 Performance Monitor stopped")
    
    async def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self.collect_system_metrics()
                self._check_thresholds()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️  Monitor error: {e}")
                await asyncio.sleep(interval)
    
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        
        now = datetime.utcnow()
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric("system.cpu_percent", cpu_percent, MetricType.GAUGE)
        
        # Memory
        memory = psutil.virtual_memory()
        self.record_metric("system.memory_percent", memory.percent, MetricType.GAUGE)
        self.record_metric("system.memory_used_mb", memory.used / 1024 / 1024, MetricType.GAUGE)
        
        # Disk
        disk = psutil.disk_usage('/')
        self.record_metric("system.disk_percent", disk.percent, MetricType.GAUGE)
        self.record_metric("system.disk_free_gb", disk.free / 1024 / 1024 / 1024, MetricType.GAUGE)
        
        # Network (if available)
        try:
            net = psutil.net_io_counters()
            self.record_metric("system.network_sent_mb", net.bytes_sent / 1024 / 1024, MetricType.COUNTER)
            self.record_metric("system.network_recv_mb", net.bytes_recv / 1024 / 1024, MetricType.COUNTER)
        except:
            pass
    
    def record_metric(self, name: str, value: Any, metric_type: str = MetricType.GAUGE):
        """Record a custom metric"""
        
        if name not in self.metrics:
            self.metrics[name] = MetricBuffer()
        
        metric = Metric(name, metric_type, value)
        self.metrics[name].add(metric)
        
        if name.startswith("system."):
            self.system_metrics.add(metric)
    
    def record_agent_task(
        self,
        agent_name: str,
        success: bool,
        response_time: float,
        error: str = None
    ):
        """Record agent task execution"""
        
        if agent_name not in self.agent_health:
            self.agent_health[agent_name] = AgentHealthStatus(agent_name)
        
        health = self.agent_health[agent_name]
        health.update_heartbeat()
        
        if success:
            health.record_success(response_time)
        else:
            health.record_failure(error or "Unknown error")
        
        # Record metrics
        self.record_metric(f"agent.{agent_name}.tasks_total", health.total_tasks, MetricType.COUNTER)
        self.record_metric(f"agent.{agent_name}.response_time_ms", response_time * 1000, MetricType.TIMER)
        self.record_metric(f"agent.{agent_name}.error_rate", health.error_rate, MetricType.GAUGE)
    
    def get_agent_health(self, agent_name: str = None) -> Dict[str, Any]:
        """Get agent health status"""
        if agent_name:
            if agent_name in self.agent_health:
                return self.agent_health[agent_name].to_dict()
            return {}
        
        return {
            name: health.to_dict()
            for name, health in self.agent_health.items()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if all([
                    cpu < self.thresholds["cpu_percent"],
                    memory.percent < self.thresholds["memory_percent"],
                    disk.percent < self.thresholds["disk_percent"],
                ]) else "degraded",
                "cpu_percent": cpu,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime_seconds": time.time() - psutil.boot_time(),
                "agents_healthy": sum(1 for h in self.agent_health.values() if h.is_healthy),
                "agents_total": len(self.agent_health),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        
        summary = {}
        for name, buffer in self.metrics.items():
            summary[name] = buffer.get_stats()
        
        return summary
    
    def _check_thresholds(self):
        """Check if any thresholds are exceeded"""
        
        alerts = []
        
        # Check system metrics
        try:
            cpu = psutil.cpu_percent()
            if cpu > self.thresholds["cpu_percent"]:
                alerts.append(f"High CPU usage: {cpu:.1f}%")
            
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds["memory_percent"]:
                alerts.append(f"High memory usage: {memory.percent:.1f}%")
            
            disk = psutil.disk_usage('/')
            if disk.percent > self.thresholds["disk_percent"]:
                alerts.append(f"High disk usage: {disk.percent:.1f}%")
        except:
            pass
        
        # Check agent health
        for agent_name, health in self.agent_health.items():
            if health.error_rate > self.thresholds["agent_error_rate"]:
                alerts.append(f"High error rate for {agent_name}: {health.error_rate:.1%}")
            
            if health.avg_response_time * 1000 > self.thresholds["response_time_ms"]:
                alerts.append(f"Slow response time for {agent_name}: {health.avg_response_time*1000:.0f}ms")
        
        # Send alerts
        if alerts and self.alert_callback:
            try:
                self.alert_callback({
                    "type": "threshold_alert",
                    "timestamp": datetime.utcnow().isoformat(),
                    "alerts": alerts,
                })
            except:
                pass
    
    def set_threshold(self, metric_name: str, value: float):
        """Set alert threshold"""
        self.thresholds[metric_name] = value
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "system_health": self.get_system_health(),
            "agent_health": self.get_agent_health(),
            "metrics_summary": self.get_metrics_summary(),
            "thresholds": self.thresholds,
            "timestamp": datetime.utcnow().isoformat(),
        }
