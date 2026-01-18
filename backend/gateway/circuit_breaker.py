"""
Circuit Breaker Module

Fault tolerance for X-Road services:
- Automatic failure detection
- Service isolation on failures
- Automatic recovery
- Half-open state for testing
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Service isolated (failing)
    HALF_OPEN = "half_open"  # Testing service recovery


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.
    
    States:
    - CLOSED: Normal - requests pass through
    - OPEN: Failing - requests blocked
    - HALF_OPEN: Testing - limited requests allowed
    
    Transitions:
    - CLOSED -> OPEN: When failure threshold exceeded
    - OPEN -> HALF_OPEN: After reset timeout
    - HALF_OPEN -> CLOSED: On successful request
    - HALF_OPEN -> OPEN: On failed request
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        reset_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes in half-open to close circuit
            reset_timeout: Seconds before transitioning to half-open
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # Per-service state
        self._circuits: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
        logger.info("CircuitBreaker initialized")
    
    def _get_circuit(self, service_key: str) -> Dict:
        """Get or create circuit for a service"""
        if service_key not in self._circuits:
            self._circuits[service_key] = {
                "state": CircuitState.CLOSED,
                "failure_count": 0,
                "success_count": 0,
                "last_failure_time": None,
                "last_state_change": datetime.utcnow(),
                "half_open_calls": 0
            }
        return self._circuits[service_key]
    
    def can_execute(self, service_key: str) -> Dict:
        """
        Check if a request can be executed.
        
        Args:
            service_key: Service identifier
            
        Returns:
            Result with allowed status and circuit state
        """
        with self._lock:
            circuit = self._get_circuit(service_key)
            state = circuit["state"]
            
            # Check for state transitions
            if state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if circuit["last_failure_time"]:
                    elapsed = (datetime.utcnow() - circuit["last_failure_time"]).total_seconds()
                    if elapsed >= self.reset_timeout:
                        # Transition to half-open
                        circuit["state"] = CircuitState.HALF_OPEN
                        circuit["half_open_calls"] = 0
                        circuit["success_count"] = 0
                        circuit["last_state_change"] = datetime.utcnow()
                        state = CircuitState.HALF_OPEN
                        logger.info(f"Circuit {service_key} transitioned to HALF_OPEN")
            
            # Determine if call is allowed
            if state == CircuitState.CLOSED:
                return {
                    "allowed": True,
                    "state": state.value,
                    "failure_count": circuit["failure_count"]
                }
            
            elif state == CircuitState.OPEN:
                retry_after = self.reset_timeout
                if circuit["last_failure_time"]:
                    elapsed = (datetime.utcnow() - circuit["last_failure_time"]).total_seconds()
                    retry_after = max(0, self.reset_timeout - elapsed)
                
                return {
                    "allowed": False,
                    "state": state.value,
                    "reason": "circuit_open",
                    "retry_after_seconds": retry_after
                }
            
            else:  # HALF_OPEN
                if circuit["half_open_calls"] < self.half_open_max_calls:
                    circuit["half_open_calls"] += 1
                    return {
                        "allowed": True,
                        "state": state.value,
                        "test_call": True,
                        "success_count": circuit["success_count"]
                    }
                else:
                    return {
                        "allowed": False,
                        "state": state.value,
                        "reason": "half_open_limit_reached",
                        "retry_after_seconds": 5
                    }
    
    def record_success(self, service_key: str):
        """
        Record a successful request.
        
        Args:
            service_key: Service identifier
        """
        with self._lock:
            circuit = self._get_circuit(service_key)
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                circuit["success_count"] += 1
                
                if circuit["success_count"] >= self.success_threshold:
                    # Close the circuit
                    circuit["state"] = CircuitState.CLOSED
                    circuit["failure_count"] = 0
                    circuit["success_count"] = 0
                    circuit["last_state_change"] = datetime.utcnow()
                    logger.info(f"Circuit {service_key} CLOSED (recovered)")
            
            elif circuit["state"] == CircuitState.CLOSED:
                # Reset failure count on success
                if circuit["failure_count"] > 0:
                    circuit["failure_count"] = max(0, circuit["failure_count"] - 1)
    
    def record_failure(self, service_key: str, error: str = None):
        """
        Record a failed request.
        
        Args:
            service_key: Service identifier
            error: Optional error message
        """
        with self._lock:
            circuit = self._get_circuit(service_key)
            circuit["last_failure_time"] = datetime.utcnow()
            circuit["last_error"] = error
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                # Open the circuit immediately
                circuit["state"] = CircuitState.OPEN
                circuit["last_state_change"] = datetime.utcnow()
                logger.warning(f"Circuit {service_key} OPENED (half-open test failed)")
            
            elif circuit["state"] == CircuitState.CLOSED:
                circuit["failure_count"] += 1
                
                if circuit["failure_count"] >= self.failure_threshold:
                    # Open the circuit
                    circuit["state"] = CircuitState.OPEN
                    circuit["last_state_change"] = datetime.utcnow()
                    logger.warning(f"Circuit {service_key} OPENED (threshold exceeded)")
    
    def get_circuit_status(self, service_key: str) -> Dict:
        """
        Get current status of a circuit.
        
        Args:
            service_key: Service identifier
            
        Returns:
            Circuit status
        """
        with self._lock:
            circuit = self._get_circuit(service_key)
            
            return {
                "service": service_key,
                "state": circuit["state"].value,
                "failure_count": circuit["failure_count"],
                "success_count": circuit["success_count"],
                "last_failure": circuit["last_failure_time"].isoformat() if circuit["last_failure_time"] else None,
                "last_state_change": circuit["last_state_change"].isoformat(),
                "last_error": circuit.get("last_error")
            }
    
    def get_all_circuits(self) -> Dict:
        """Get status of all circuits"""
        with self._lock:
            return {
                key: {
                    "state": circuit["state"].value,
                    "failure_count": circuit["failure_count"],
                    "last_failure": circuit["last_failure_time"].isoformat() if circuit["last_failure_time"] else None
                }
                for key, circuit in self._circuits.items()
            }
    
    def reset_circuit(self, service_key: str):
        """
        Manually reset a circuit to closed state.
        
        Args:
            service_key: Service identifier
        """
        with self._lock:
            if service_key in self._circuits:
                self._circuits[service_key] = {
                    "state": CircuitState.CLOSED,
                    "failure_count": 0,
                    "success_count": 0,
                    "last_failure_time": None,
                    "last_state_change": datetime.utcnow(),
                    "half_open_calls": 0
                }
                logger.info(f"Circuit {service_key} manually reset")
    
    def get_open_circuits(self) -> list:
        """Get list of currently open circuits"""
        with self._lock:
            return [
                key for key, circuit in self._circuits.items()
                if circuit["state"] == CircuitState.OPEN
            ]


# Singleton instance
_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get the global CircuitBreaker instance"""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker
