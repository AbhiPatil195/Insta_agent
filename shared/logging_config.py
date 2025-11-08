"""Structured logging configuration for production."""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "insta-agent"),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "thread_id"):
            log_data["thread_id"] = record.thread_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
            
        return json.dumps(log_data)


class SimpleFormatter(logging.Formatter):
    """Human-readable formatter for development."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        log_msg = f"{color}[{timestamp}] {record.levelname:8s}{reset} {record.name:20s} | {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)
            
        return log_msg


def setup_logging(service: str = "insta-agent", level: str = "INFO", json_format: bool = False):
    """
    Configure logging for the application.
    
    Args:
        service: Service name for log identification
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, output JSON; otherwise human-readable
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = SimpleFormatter()
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)


# Convenience functions for structured logging
def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float):
    """Log an API request with structured data."""
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
    )


def log_message_processed(logger: logging.Logger, user_id: int, thread_id: str, intent: str, duration_ms: float):
    """Log a processed message with structured data."""
    logger.info(
        f"Message processed for user {user_id}",
        extra={
            "user_id": user_id,
            "thread_id": thread_id,
            "intent": intent,
            "duration_ms": duration_ms,
        }
    )


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log an error with context."""
    logger.error(
        f"Error: {str(error)}",
        exc_info=True,
        extra=context or {}
    )
