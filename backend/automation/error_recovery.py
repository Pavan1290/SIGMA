"""Enhanced Error Recovery - Auto-retry with intelligent backoff strategies"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
from enum import Enum
import random


class BackoffStrategy(str, Enum):
    CONSTANT = "constant"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    JITTER = "jitter"  # Exponential with random jitter


class ErrorCategory(str, Enum):
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH = "authentication"
    RESOURCE = "resource"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class RetryPolicy:
    """Defines retry behavior for errors"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retry_on_errors: list = None,
        fallback_action: Optional[Callable] = None,
    ):
        self.max_attempts = max_attempts
        self.backoff_strategy = backoff_strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_on_errors = retry_on_errors or [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
        ]
        self.fallback_action = fallback_action
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay before next retry"""
        
        if self.backoff_strategy == BackoffStrategy.CONSTANT:
            delay = self.base_delay
            
        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.base_delay * attempt
            
        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
            
        elif self.backoff_strategy == BackoffStrategy.FIBONACCI:
            delay = self._fibonacci(attempt) * self.base_delay
            
        elif self.backoff_strategy == BackoffStrategy.JITTER:
            # Exponential with random jitter to prevent thundering herd
            exp_delay = self.base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, exp_delay * 0.1)  # 10% jitter
            delay = exp_delay + jitter
        
        else:
            delay = self.base_delay
        
        # Cap at max_delay
        return min(delay, self.max_delay)
    
    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 2:
            return 1
        a, b = 1, 1
        for _ in range(n - 2):
            a, b = b, a + b
        return b


class ErrorRecovery:
    """
    Advanced Error Recovery System
    
    Features:
    - Multiple backoff strategies
    - Error categorization
    - Circuit breaker pattern
    - Automatic fallback actions
    - Error statistics tracking
    - Smart retry decisions
    """
    
    def __init__(self):
        self.error_stats: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.default_policy = RetryPolicy()
        self.custom_policies: Dict[str, RetryPolicy] = {}
    
    async def execute_with_retry(
        self,
        func: Callable,
        func_args: tuple = (),
        func_kwargs: dict = None,
        policy: Optional[RetryPolicy] = None,
        context: str = "default",
    ) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            func_args: Positional arguments
            func_kwargs: Keyword arguments
            policy: Retry policy (uses default if None)
            context: Context identifier for circuit breaker
        """
        
        func_kwargs = func_kwargs or {}
        policy = policy or self.default_policy
        
        # Check circuit breaker
        if self._is_circuit_open(context):
            raise Exception(f"Circuit breaker open for context: {context}")
        
        last_error = None
        
        for attempt in range(1, policy.max_attempts + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*func_args, **func_kwargs)
                else:
                    result = func(*func_args, **func_kwargs)
                
                # Success - reset circuit breaker
                self._record_success(context)
                return result
                
            except Exception as e:
                last_error = e
                error_category = self._categorize_error(e)
                
                # Record error
                self._record_error(context, error_category, str(e))
                
                # Check if error is retryable
                if error_category not in policy.retry_on_errors:
                    print(f"❌ Non-retryable error ({error_category}): {e}")
                    break
                
                # Last attempt?
                if attempt >= policy.max_attempts:
                    print(f"❌ Max retry attempts ({policy.max_attempts}) reached")
                    break
                
                # Calculate delay and wait
                delay = policy.calculate_delay(attempt)
                print(f"⚠️  Attempt {attempt}/{policy.max_attempts} failed: {e}")
                print(f"   Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        self._trip_circuit_breaker(context)
        
        # Try fallback action
        if policy.fallback_action:
            try:
                print("🔄 Executing fallback action...")
                if asyncio.iscoroutinefunction(policy.fallback_action):
                    return await policy.fallback_action(last_error)
                else:
                    return policy.fallback_action(last_error)
            except Exception as fallback_error:
                print(f"❌ Fallback action failed: {fallback_error}")
        
        # Re-raise last error
        raise last_error
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error type"""
        
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if "timeout" in error_str or "timeout" in error_type:
            return ErrorCategory.TIMEOUT
        
        if any(word in error_str for word in ["network", "connection", "unreachable"]):
            return ErrorCategory.NETWORK
        
        if any(word in error_str for word in ["rate limit", "too many requests", "429"]):
            return ErrorCategory.RATE_LIMIT
        
        if any(word in error_str for word in ["auth", "unauthorized", "401", "403"]):
            return ErrorCategory.AUTH
        
        if any(word in error_str for word in ["memory", "disk", "resource", "quota"]):
            return ErrorCategory.RESOURCE
        
        if any(word in error_str for word in ["validation", "invalid", "bad request", "400"]):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def _record_error(self, context: str, category: ErrorCategory, error_msg: str):
        """Record error statistics"""
        
        if context not in self.error_stats:
            self.error_stats[context] = {
                "total_errors": 0,
                "errors_by_category": {},
                "last_error": None,
                "last_error_time": None,
            }
        
        stats = self.error_stats[context]
        stats["total_errors"] += 1
        stats["last_error"] = error_msg
        stats["last_error_time"] = datetime.utcnow()
        
        if category.value not in stats["errors_by_category"]:
            stats["errors_by_category"][category.value] = 0
        stats["errors_by_category"][category.value] += 1
    
    def _record_success(self, context: str):
        """Record successful execution"""
        
        # Reset circuit breaker
        if context in self.circuit_breakers:
            self.circuit_breakers[context]["failures"] = 0
            self.circuit_breakers[context]["state"] = "closed"
    
    def _is_circuit_open(self, context: str) -> bool:
        """Check if circuit breaker is open"""
        
        if context not in self.circuit_breakers:
            self.circuit_breakers[context] = {
                "state": "closed",
                "failures": 0,
                "opened_at": None,
                "threshold": 5,
                "timeout": 60,  # seconds
            }
        
        breaker = self.circuit_breakers[context]
        
        if breaker["state"] == "open":
            # Check if timeout elapsed
            if breaker["opened_at"]:
                elapsed = (datetime.utcnow() - breaker["opened_at"]).total_seconds()
                if elapsed > breaker["timeout"]:
                    # Half-open: allow one retry
                    breaker["state"] = "half-open"
                    return False
            return True
        
        return False
    
    def _trip_circuit_breaker(self, context: str):
        """Trip circuit breaker after repeated failures"""
        
        if context not in self.circuit_breakers:
            return
        
        breaker = self.circuit_breakers[context]
        breaker["failures"] += 1
        
        if breaker["failures"] >= breaker["threshold"]:
            breaker["state"] = "open"
            breaker["opened_at"] = datetime.utcnow()
            print(f"🔴 Circuit breaker OPEN for context: {context}")
    
    def set_custom_policy(self, context: str, policy: RetryPolicy):
        """Set custom retry policy for a context"""
        self.custom_policies[context] = policy
    
    def get_error_stats(self, context: str = None) -> Dict[str, Any]:
        """Get error statistics"""
        if context:
            return self.error_stats.get(context, {})
        return self.error_stats
    
    def reset_circuit_breaker(self, context: str):
        """Manually reset circuit breaker"""
        if context in self.circuit_breakers:
            self.circuit_breakers[context]["state"] = "closed"
            self.circuit_breakers[context]["failures"] = 0
            self.circuit_breakers[context]["opened_at"] = None
            print(f"🟢 Circuit breaker RESET for context: {context}")
