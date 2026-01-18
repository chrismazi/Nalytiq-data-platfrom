"""
Production Middleware Stack

Comprehensive middleware for:
- Request/Response logging
- Error handling
- Security headers
- Rate limiting
- Correlation ID tracking
- Request timing
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import traceback

from logging_config import set_correlation_id, get_correlation_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and correlation IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_correlation_id(correlation_id)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent", "")[:200],
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Add headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling with structured responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            correlation_id = get_correlation_id()
            
            # Log the error
            logger.error(
                f"Unhandled exception: {str(exc)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(exc).__name__,
                },
                exc_info=True
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred",
                    "correlation_id": correlation_id,
                    "path": request.url.path,
                },
                headers={"X-Correlation-ID": correlation_id}
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # IP -> [(timestamp, count)]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        window_start = current_time - 60
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if ts > window_start
            ]
        else:
            self.requests[client_ip] = []
        
        # Count requests in window
        request_count = sum(count for _, count in self.requests[client_ip])
        
        if request_count >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={"client_ip": client_ip, "request_count": request_count}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute}/minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.requests[client_ip].append((current_time, 1))
        
        return await call_next(request)


def setup_middleware(app: FastAPI, settings) -> None:
    """Configure all middleware for the application"""
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.CORS_ORIGINS,
        allow_credentials=settings.security.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.security.CORS_ALLOW_METHODS,
        allow_headers=settings.security.CORS_ALLOW_HEADERS,
    )
    
    # Trusted hosts (production)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["nalytiq.gov.rw", "api.nalytiq.gov.rw", "localhost"]
        )
    
    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting (in production, use Redis-based)
    if settings.ENVIRONMENT != "development":
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.security.RATE_LIMIT_PER_MINUTE
        )
    
    logger.info("Middleware stack configured")
