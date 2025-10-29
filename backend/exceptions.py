"""
Custom exceptions and error handlers
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class DataProcessingError(Exception):
    """Raised when data processing fails"""
    pass


class FileValidationError(Exception):
    """Raised when file validation fails"""
    pass


class AnalysisError(Exception):
    """Raised when data analysis fails"""
    pass


class AuthenticationError(HTTPException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Raised when authorization fails"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors"""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip 'body' or 'query'
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "code": "VALIDATION_ERROR",
            "errors": errors,
            "detail": exc.errors()
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error on {request.url.path}: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": "HTTP_ERROR",
            "status_code": exc.status_code,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions"""
    logger.exception(f"Unexpected error on {request.url.path}: {exc}")
    
    # Don't expose internal errors in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An internal server error occurred",
            "code": "INTERNAL_ERROR",
            "detail": str(exc) if logger.level == logging.DEBUG else "Please contact support",
        },
    )


def create_error_response(
    message: str,
    code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create a standardized error response"""
    content = {
        "error": message,
        "code": code,
        "status_code": status_code,
    }
    if details:
        content["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)
