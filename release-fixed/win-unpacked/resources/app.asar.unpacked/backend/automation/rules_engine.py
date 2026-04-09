"""Automation Rules Engine - Define and evaluate complex automation rules"""

from datetime import datetime, time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import re


class RuleType(str, Enum):
    TRIGGER = "trigger"  # Event-based triggers
    CONDITION = "condition"  # Conditional logic
    SCHEDULE = "schedule"  # Time-based rules
    THRESHOLD = "threshold"  # Metric-based thresholds


class RuleOperator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"  # Regex match
    IN = "in"
    NOT_IN = "not_in"


class Rule:
    """Represents an automation rule"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        rule_type: RuleType,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        enabled: bool = True,
        priority: int = 5,
    ):
        self.rule_id = rule_id
        self.name = name
        self.rule_type = rule_type
        self.conditions = conditions
        self.actions = actions
        self.enabled = enabled
        self.priority = priority
        self.evaluation_count = 0
        self.trigger_count = 0
        self.last_triggered = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "rule_type": self.rule_type.value,
            "conditions": self.conditions,
            "actions": self.actions,
            "enabled": self.enabled,
            "priority": self.priority,
            "evaluation_count": self.evaluation_count,
            "trigger_count": self.trigger_count,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
        }


class RulesEngine:
    """
    Automation Rules Engine
    
    Features:
    - Define complex automation rules
    - Evaluate conditions against context
    - Trigger actions based on rules
    - Support for multiple rule types
    - Priority-based execution
    - Rule chaining and composition
    
    Example Rules:
    1. "If CPU > 90% for 5 minutes, send alert and scale resources"
    2. "If it's Monday 9 AM, run weekly report workflow"
    3. "If email contains 'urgent', prioritize and notify immediately"
    4. "If workflow fails 3 times, pause and escalate"
    """
    
    def __init__(self, action_executor: Optional[Callable] = None):
        """
        Args:
            action_executor: Function to execute actions when rules trigger
        """
        self.rules: Dict[str, Rule] = {}
        self.action_executor = action_executor
        self.context: Dict[str, Any] = {}
    
    def add_rule(self, rule: Rule):
        """Add a new rule"""
        self.rules[rule.rule_id] = rule
        print(f"✅ Rule added: {rule.name} ({rule.rule_id})")
    
    def remove_rule(self, rule_id: str):
        """Remove a rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            print(f"🗑️  Rule removed: {rule_id}")
    
    def enable_rule(self, rule_id: str):
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def update_context(self, context: Dict[str, Any]):
        """Update global context for rule evaluation"""
        self.context.update(context)
    
    def evaluate_all_rules(self, event_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled rules against current context
        
        Args:
            event_context: Additional context for this evaluation
        
        Returns:
            List of triggered rules with their actions
        """
        
        # Merge contexts
        full_context = {**self.context, **(event_context or {})}
        
        triggered_rules = []
        
        # Get enabled rules sorted by priority
        enabled_rules = [
            rule for rule in self.rules.values()
            if rule.enabled
        ]
        enabled_rules.sort(key=lambda r: r.priority)
        
        for rule in enabled_rules:
            rule.evaluation_count += 1
            
            if self.evaluate_rule(rule, full_context):
                rule.trigger_count += 1
                rule.last_triggered = datetime.utcnow()
                
                triggered_rules.append({
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "actions": rule.actions,
                    "context": full_context,
                })
                
                # Execute actions
                if self.action_executor:
                    try:
                        for action in rule.actions:
                            self.action_executor(action, full_context)
                    except Exception as e:
                        print(f"❌ Error executing actions for rule {rule.rule_id}: {e}")
        
        return triggered_rules
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> bool:
        """
        Evaluate a single rule against context
        
        Returns:
            True if all conditions are met
        """
        
        if not rule.enabled:
            return False
        
        # All conditions must be true (AND logic)
        # For OR logic, create multiple rules
        for condition in rule.conditions:
            if not self.evaluate_condition(condition, context):
                return False
        
        return True
    
    def evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition
        
        Condition format:
        {
            "field": "cpu_percent",
            "operator": ">",
            "value": 90,
            "source": "metrics"  # where to get the field value
        }
        """
        
        try:
            field = condition.get("field")
            operator = condition.get("operator")
            expected_value = condition.get("value")
            source = condition.get("source", "context")
            
            # Get actual value from context
            if source == "context":
                actual_value = self._get_nested_value(context, field)
            elif source == "metrics":
                actual_value = self._get_metric_value(field)
            elif source == "time":
                actual_value = datetime.utcnow()
            else:
                actual_value = context.get(field)
            
            # Evaluate operator
            return self._evaluate_operator(actual_value, operator, expected_value)
            
        except Exception as e:
            print(f"⚠️  Condition evaluation error: {e}")
            return False
    
    def _evaluate_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate comparison operator"""
        
        try:
            if operator == RuleOperator.EQUALS or operator == "==":
                return actual == expected
            
            elif operator == RuleOperator.NOT_EQUALS or operator == "!=":
                return actual != expected
            
            elif operator == RuleOperator.GREATER or operator == ">":
                return actual > expected
            
            elif operator == RuleOperator.GREATER_EQUAL or operator == ">=":
                return actual >= expected
            
            elif operator == RuleOperator.LESS or operator == "<":
                return actual < expected
            
            elif operator == RuleOperator.LESS_EQUAL or operator == "<=":
                return actual <= expected
            
            elif operator == RuleOperator.CONTAINS or operator == "contains":
                return expected in str(actual)
            
            elif operator == RuleOperator.NOT_CONTAINS or operator == "not_contains":
                return expected not in str(actual)
            
            elif operator == RuleOperator.MATCHES or operator == "matches":
                return bool(re.search(expected, str(actual)))
            
            elif operator == RuleOperator.IN or operator == "in":
                return actual in expected
            
            elif operator == RuleOperator.NOT_IN or operator == "not_in":
                return actual not in expected
            
            else:
                print(f"⚠️  Unknown operator: {operator}")
                return False
                
        except Exception as e:
            print(f"⚠️  Operator evaluation error: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation"""
        
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def _get_metric_value(self, metric_name: str) -> Any:
        """Get metric value from monitoring system"""
        # This should integrate with PerformanceMonitor
        # For now, return from context if available
        return self.context.get(f"metrics.{metric_name}")
    
    def get_rule_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all rules"""
        return [rule.to_dict() for rule in self.rules.values()]
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Rule:
        """Create rule from JSON config"""
        
        return Rule(
            rule_id=config.get("id", f"rule_{datetime.utcnow().timestamp()}"),
            name=config["name"],
            rule_type=RuleType(config.get("type", "condition")),
            conditions=config.get("conditions", []),
            actions=config.get("actions", []),
            enabled=config.get("enabled", True),
            priority=config.get("priority", 5),
        )


# Predefined rule templates
class RuleTemplates:
    """Common rule templates for quick setup"""
    
    @staticmethod
    def high_cpu_alert(threshold: float = 90.0) -> Dict[str, Any]:
        """Alert when CPU usage is high"""
        return {
            "name": "High CPU Alert",
            "type": "threshold",
            "conditions": [
                {
                    "field": "cpu_percent",
                    "operator": ">",
                    "value": threshold,
                    "source": "metrics"
                }
            ],
            "actions": [
                {
                    "type": "alert",
                    "message": f"CPU usage exceeded {threshold}%",
                    "severity": "warning"
                }
            ]
        }
    
    @staticmethod
    def workflow_failure_escalation(failure_count: int = 3) -> Dict[str, Any]:
        """Escalate after multiple workflow failures"""
        return {
            "name": "Workflow Failure Escalation",
            "type": "trigger",
            "conditions": [
                {
                    "field": "workflow.status",
                    "operator": "==",
                    "value": "failed",
                    "source": "context"
                },
                {
                    "field": "workflow.failure_count",
                    "operator": ">=",
                    "value": failure_count,
                    "source": "context"
                }
            ],
            "actions": [
                {
                    "type": "pause_workflow",
                },
                {
                    "type": "alert",
                    "message": f"Workflow failed {failure_count} times, pausing execution",
                    "severity": "critical"
                }
            ]
        }
    
    @staticmethod
    def scheduled_backup(hour: int = 2, minute: int = 0) -> Dict[str, Any]:
        """Run backup at specific time"""
        return {
            "name": "Scheduled Backup",
            "type": "schedule",
            "conditions": [
                {
                    "field": "time.hour",
                    "operator": "==",
                    "value": hour,
                    "source": "time"
                },
                {
                    "field": "time.minute",
                    "operator": "==",
                    "value": minute,
                    "source": "time"
                }
            ],
            "actions": [
                {
                    "type": "run_workflow",
                    "workflow_id": "backup_workflow"
                }
            ]
        }
