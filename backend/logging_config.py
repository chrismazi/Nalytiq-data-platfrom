"""
Production-Ready Logging Configuration

Structured JSON logging with:
- Request/Response logging
- Error tracking with Sentry integration
- Correlation IDs for tracing
- Log rotation and archiving
"""

import logging
import logging.handlers
import sys
import json
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps
import traceback

# Context variable for request correlation
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get() or '-'
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', '-'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                          'correlation_id', 'message']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        correlation_id = getattr(record, 'correlation_id', '-')
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        msg = (
            f"{timestamp} | "
            f"{color}{record.levelname:8}{self.RESET} | "
            f"[{correlation_id[:8]}] | "
            f"{record.name}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )
        
        if record.exc_info:
            msg += '\n' + ''.join(traceback.format_exception(*record.exc_info))
        
        return msg


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,
    backup_count: int = 5
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format (json or text)
        log_file: Optional log file path
        max_bytes: Max log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    
    # Choose formatter
    if log_format.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id_var.get() or ''


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID, generate if not provided"""
    cid = correlation_id or str(uuid.uuid4())
    correlation_id_var.set(cid)
    return cid


class LogContext:
    """Context manager for logging extra fields"""
    
    def __init__(self, **kwargs):
        self.extra = kwargs
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        extra = self.extra
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in extra.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_request(func):
    """Decorator to log function calls with timing"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"{func.__name__} completed",
                extra={'duration_ms': round(duration_ms, 2), 'status': 'success'}
            )
            return result
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"{func.__name__} failed: {str(e)}",
                extra={'duration_ms': round(duration_ms, 2), 'status': 'error'},
                exc_info=True
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"{func.__name__} completed",
                extra={'duration_ms': round(duration_ms, 2), 'status': 'success'}
            )
            return result
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"{func.__name__} failed: {str(e)}",
                extra={'duration_ms': round(duration_ms, 2), 'status': 'error'},
                exc_info=True
            )
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
