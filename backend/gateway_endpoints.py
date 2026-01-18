"""
Gateway API Endpoints

FastAPI router for API Gateway operations:
- Service calls through gateway
- Rate limiting status
- Circuit breaker status
- Gateway health
"""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from gateway.gateway import get_api_gateway
from gateway.rate_limiter import get_rate_limiter
from gateway.circuit_breaker import get_circuit_breaker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gateway", tags=["API Gateway"])


@router.post("/call")
async def gateway_service_call(
    client_org: str = Query(..., description="Client organization code"),
    client_subsystem: str = Query(..., description="Client subsystem code"),
    target_org: str = Query(..., description="Target organization code"),
    target_subsystem: str = Query(..., description="Target subsystem code"),
    service_code: str = Query(..., description="Service code"),
    service_version: str = Query("v1", description="Service version"),
    method: str = Query("GET", description="HTTP method"),
    path: str = Query("/", description="Request path"),
    body: Optional[Dict] = Body(None)
):
    """
    Execute a service call through the API Gateway.
    
    This is the main endpoint for all X-Road service calls with full
    rate limiting, circuit breaking, and access control.
    """
    gateway = get_api_gateway()
    
    result = await gateway.process_request(
        client_org=client_org,
        client_subsystem=client_subsystem,
        target_org=target_org,
        target_subsystem=target_subsystem,
        service_code=service_code,
        service_version=service_version,
        method=method,
        path=path,
        body=body
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=result.get("status_code", 500),
            detail={
                "error": result.get("error"),
                "message": result.get("message"),
                "request_id": result.get("request_id")
            }
        )
    
    return result


@router.get("/status")
async def get_gateway_status():
    """Get API Gateway health and status"""
    gateway = get_api_gateway()
    return gateway.get_gateway_status()


@router.get("/services/{service_key:path}/health")
async def get_service_health(service_key: str):
    """Get health status for a specific service"""
    gateway = get_api_gateway()
    return gateway.get_service_health(service_key)


# ============================================
# RATE LIMITING ENDPOINTS
# ============================================

@router.get("/rate-limits")
async def get_rate_limit_status():
    """Get rate limiting status for all organizations"""
    rate_limiter = get_rate_limiter()
    return {
        "usage": rate_limiter.get_all_usage(),
        "default_org_limit": rate_limiter.DEFAULT_ORG_REQUESTS_PER_MINUTE,
        "default_service_limit": rate_limiter.DEFAULT_SERVICE_REQUESTS_PER_MINUTE
    }


@router.get("/rate-limits/{organization_code}")
async def get_org_rate_limit(organization_code: str, minutes: int = 60):
    """Get rate limit status for a specific organization"""
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_org_usage(organization_code, minutes)


@router.post("/rate-limits/{organization_code}/set")
async def set_org_rate_limit(
    organization_code: str,
    requests_per_minute: int
):
    """Set custom rate limit for an organization"""
    if requests_per_minute < 1 or requests_per_minute > 10000:
        raise HTTPException(
            status_code=400,
            detail="Rate limit must be between 1 and 10000"
        )
    
    rate_limiter = get_rate_limiter()
    rate_limiter.set_org_limit(organization_code, requests_per_minute)
    
    return {
        "success": True,
        "message": f"Rate limit set for {organization_code}",
        "limit": requests_per_minute
    }


@router.post("/rate-limits/{organization_code}/reset")
async def reset_org_rate_limit(organization_code: str):
    """Reset rate limit for an organization (refill tokens)"""
    rate_limiter = get_rate_limiter()
    rate_limiter.reset_org_limit(organization_code)
    
    return {
        "success": True,
        "message": f"Rate limit reset for {organization_code}"
    }


# ============================================
# CIRCUIT BREAKER ENDPOINTS
# ============================================

@router.get("/circuits")
async def get_all_circuits():
    """Get status of all circuit breakers"""
    circuit_breaker = get_circuit_breaker()
    return {
        "circuits": circuit_breaker.get_all_circuits(),
        "open_circuits": circuit_breaker.get_open_circuits()
    }


@router.get("/circuits/{service_key:path}")
async def get_circuit_status(service_key: str):
    """Get circuit breaker status for a service"""
    circuit_breaker = get_circuit_breaker()
    return circuit_breaker.get_circuit_status(service_key)


@router.post("/circuits/{service_key:path}/reset")
async def reset_circuit(service_key: str):
    """Manually reset (close) a circuit breaker"""
    circuit_breaker = get_circuit_breaker()
    circuit_breaker.reset_circuit(service_key)
    
    return {
        "success": True,
        "message": f"Circuit reset for {service_key}",
        "state": "closed"
    }
