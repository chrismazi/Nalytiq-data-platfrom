"""
Production-Ready Health Check Endpoints

Comprehensive health monitoring for:
- Application readiness and liveness
- Database connectivity
- Redis connectivity
- External service status
- Disk and memory usage
"""

from fastapi import APIRouter, Response, HTTPException
from typing import Dict, Any, Optional
import asyncio
import psutil
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthChecker:
    """Health check orchestrator"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks = {}
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from database_enhanced import SessionLocal
            async with SessionLocal() as session:
                await session.execute("SELECT 1")
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis
            from settings import settings
            
            client = redis.from_url(settings.redis.redis_url)
            start = datetime.utcnow()
            await client.ping()
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            await client.close()
            
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_disk(self) -> Dict[str, Any]:
        """Check disk usage"""
        try:
            disk = psutil.disk_usage('/')
            return {
                "status": "healthy" if disk.percent < 90 else "warning",
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": disk.percent
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            mem = psutil.virtual_memory()
            return {
                "status": "healthy" if mem.percent < 90 else "warning",
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return {
                "status": "healthy" if cpu_percent < 90 else "warning",
                "percent_used": cpu_percent,
                "cores": psutil.cpu_count()
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def get_uptime(self) -> Dict[str, Any]:
        """Get application uptime"""
        uptime = datetime.utcnow() - self.start_time
        return {
            "started_at": self.start_time.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0]
        }


# Global health checker instance
health_checker = HealthChecker()


@router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe(response: Response) -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    Returns 200 if the application is ready to accept traffic.
    """
    checks = {}
    is_ready = True
    
    # Check database
    db_check = await health_checker.check_database()
    checks["database"] = db_check
    if db_check["status"] != "healthy":
        is_ready = False
    
    # Check Redis (non-critical)
    redis_check = await health_checker.check_redis()
    checks["redis"] = redis_check
    
    result = {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if not is_ready:
        response.status_code = 503
    
    return result


@router.get("/")
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for monitoring dashboards.
    Returns detailed status of all components.
    """
    from settings import settings
    
    # Run all checks
    db_check = await health_checker.check_database()
    redis_check = await health_checker.check_redis()
    disk_check = health_checker.check_disk()
    memory_check = health_checker.check_memory()
    cpu_check = health_checker.check_cpu()
    uptime = health_checker.get_uptime()
    
    # Determine overall status
    all_checks = [db_check, redis_check, disk_check, memory_check, cpu_check]
    if any(c.get("status") == "unhealthy" for c in all_checks):
        overall_status = "unhealthy"
    elif any(c.get("status") == "warning" for c in all_checks):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime": uptime,
        "checks": {
            "database": db_check,
            "redis": redis_check,
            "disk": disk_check,
            "memory": memory_check,
            "cpu": cpu_check
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """
    Prometheus-compatible metrics endpoint.
    """
    from settings import settings
    
    uptime = health_checker.get_uptime()
    memory = health_checker.check_memory()
    cpu = health_checker.check_cpu()
    disk = health_checker.check_disk()
    
    metrics = []
    
    # Application metrics
    metrics.append(f'# HELP nalytiq_uptime_seconds Application uptime in seconds')
    metrics.append(f'# TYPE nalytiq_uptime_seconds gauge')
    metrics.append(f'nalytiq_uptime_seconds {uptime["uptime_seconds"]}')
    
    # Memory metrics
    metrics.append(f'# HELP nalytiq_memory_used_bytes Memory used in bytes')
    metrics.append(f'# TYPE nalytiq_memory_used_bytes gauge')
    metrics.append(f'nalytiq_memory_used_bytes {int(memory.get("used_gb", 0) * 1024**3)}')
    
    metrics.append(f'# HELP nalytiq_memory_percent Memory usage percentage')
    metrics.append(f'# TYPE nalytiq_memory_percent gauge')
    metrics.append(f'nalytiq_memory_percent {memory.get("percent_used", 0)}')
    
    # CPU metrics
    metrics.append(f'# HELP nalytiq_cpu_percent CPU usage percentage')
    metrics.append(f'# TYPE nalytiq_cpu_percent gauge')
    metrics.append(f'nalytiq_cpu_percent {cpu.get("percent_used", 0)}')
    
    # Disk metrics
    metrics.append(f'# HELP nalytiq_disk_percent Disk usage percentage')
    metrics.append(f'# TYPE nalytiq_disk_percent gauge')
    metrics.append(f'nalytiq_disk_percent {disk.get("percent_used", 0)}')
    
    return Response(
        content='\n'.join(metrics),
        media_type='text/plain; charset=utf-8'
    )
