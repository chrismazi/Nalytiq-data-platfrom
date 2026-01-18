"""
API Exception Handlers and Custom Exceptions

Structured error responses for production APIs.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from logging_config import get_correlation_id

logger = logging.getLogger(__name__)


# ============================================
# CUSTOM EXCEPTIONS
# ============================================

class NalytiqException(Exception):
    """Base exception for all platform errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "platform_error",
        status_code: int = 500,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(NalytiqException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication required", details: Dict = None):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
            details=details
        )


class AuthorizationError(NalytiqException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Insufficient permissions", details: Dict = None):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
            details=details
        )


class NotFoundError(NalytiqException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: str = None, details: Dict = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            message=message,
            error_code="not_found",
            status_code=404,
            details=details or {"resource": resource, "identifier": identifier}
        )


class ConflictError(NalytiqException):
    """Resource conflict"""
    
    def __init__(self, message: str = "Resource already exists", details: Dict = None):
        super().__init__(
            message=message,
            error_code="conflict",
            status_code=409,
            details=details
        )


class ValidationException(NalytiqException):
    """Request validation error"""
    
    def __init__(self, message: str = "Validation failed", errors: list = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=422,
            details={"validation_errors": errors or []}
        )


class RateLimitError(NalytiqException):
    """Rate limit exceeded"""
    
    def __init__(self, limit: int, window_seconds: int = 60):
        super().__init__(
            message=f"Rate limit of {limit} requests per {window_seconds}s exceeded",
            error_code="rate_limit_exceeded",
            status_code=429,
            details={"limit": limit, "window_seconds": window_seconds}
        )


class ServiceUnavailableError(NalytiqException):
    """Service temporarily unavailable"""
    
    def __init__(self, service: str = "service", message: str = None):
        super().__init__(
            message=message or f"{service} is temporarily unavailable",
            error_code="service_unavailable",
            status_code=503,
            details={"service": service}
        )


class XRoadError(NalytiqException):
    """X-Road specific error"""
    
    def __init__(self, message: str, fault_code: str = None, details: Dict = None):
        super().__init__(
            message=message,
            error_code="xroad_error",
            status_code=502,
            details={"fault_code": fault_code, **(details or {})}
        )


# ============================================
# ERROR RESPONSE FORMAT
# ============================================

def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    path: str,
    details: Dict = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
        },
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": path,
            "correlation_id": get_correlation_id() or "-",
        }
    }


# ============================================
# EXCEPTION HANDLERS
# ============================================

async def nalytiq_exception_handler(request: Request, exc: NalytiqException) -> JSONResponse:
    """Handle custom platform exceptions"""
    logger.warning(
        f"Platform error: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
            details=exc.details
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    error_codes = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "too_many_requests",
        500: "internal_error",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout",
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_code=error_codes.get(exc.status_code, "error"),
            message=str(exc.detail),
            status_code=exc.status_code,
            path=request.url.path,
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.info(
        f"Validation error on {request.url.path}",
        extra={"errors": errors}
    )
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            error_code="validation_error",
            message="Request validation failed",
            status_code=422,
            path=request.url.path,
            details={"validation_errors": errors}
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="internal_error",
            message="An unexpected error occurred",
            status_code=500,
            path=request.url.path,
        )
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers"""
    app.add_exception_handler(NalytiqException, nalytiq_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers configured")
