from __future__ import annotations

import logging
import sys
import traceback
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_LEVEL == "INFO" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger("request")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Get request details
            method = scope["method"]
            path = scope["path"]
            headers = dict(scope.get("headers", []))
            
            # Log request
            self.logger.info(
                "HTTP request started",
                method=method,
                path=path,
                client=scope.get("client"),
                user_agent=headers.get(b"user-agent", b"").decode("utf-8"),
            )
            
            # Track response
            start_time = time.time()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    duration = time.time() - start_time
                    
                    self.logger.info(
                        "HTTP request completed",
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=round(duration * 1000, 2),
                    )
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class WebSocketLogger:
    """Logger for WebSocket connections"""
    
    def __init__(self):
        self.logger = structlog.get_logger("websocket")
    
    def log_connection(self, websocket_path: str, client_info: Dict[str, Any]):
        """Log new WebSocket connection"""
        self.logger.info(
            "WebSocket connection established",
            path=websocket_path,
            client=client_info,
        )
    
    def log_disconnection(self, websocket_path: str, client_info: Dict[str, Any]):
        """Log WebSocket disconnection"""
        self.logger.info(
            "WebSocket connection closed",
            path=websocket_path,
            client=client_info,
        )
    
    def log_message(self, websocket_path: str, message_type: str, client_info: Dict[str, Any]):
        """Log WebSocket message"""
        self.logger.debug(
            "WebSocket message",
            path=websocket_path,
            message_type=message_type,
            client=client_info,
        )
    
    def log_error(self, websocket_path: str, error: Exception, client_info: Dict[str, Any]):
        """Log WebSocket error"""
        self.logger.error(
            "WebSocket error",
            path=websocket_path,
            error=str(error),
            error_type=type(error).__name__,
            client=client_info,
            exc_info=True,
        )


class AILogger:
    """Logger for AI detection events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("ai_detection")
    
    def log_frame_processing(
        self,
        session_id: str,
        student_id: str,
        processing_time_ms: float,
        face_count: int,
        events_detected: int,
    ):
        """Log frame processing results"""
        self.logger.info(
            "AI frame processed",
            session_id=session_id,
            student_id=student_id,
            processing_time_ms=processing_time_ms,
            face_count=face_count,
            events_detected=events_detected,
        )
    
    def log_suspicious_activity(
        self,
        session_id: str,
        student_id: str,
        detection_type: str,
        severity: int,
        confidence: float,
        details: Dict[str, Any],
    ):
        """Log suspicious activity detection"""
        self.logger.warning(
            "Suspicious activity detected",
            session_id=session_id,
            student_id=student_id,
            detection_type=detection_type,
            severity=severity,
            confidence=confidence,
            details=details,
        )
    
    def log_performance_metrics(
        self,
        avg_fps: float,
        memory_usage_mb: float,
        cpu_usage_percent: float,
        active_sessions: int,
    ):
        """Log AI performance metrics"""
        self.logger.info(
            "AI performance metrics",
            avg_fps=avg_fps,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            active_sessions=active_sessions,
        )
    
    def log_error(self, session_id: str, error: Exception, context: Dict[str, Any]):
        """Log AI processing error"""
        self.logger.error(
            "AI processing error",
            session_id=session_id,
            error=str(error),
            error_type=type(error).__name__,
            context=context,
            exc_info=True,
        )


class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_authentication_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
    ):
        """Log authentication attempt"""
        level = "info" if success else "warning"
        getattr(self.logger, level)(
            "Authentication attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
    ):
        """Log authorization failure"""
        self.logger.warning(
            "Authorization failure",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
        )
    
    def log_rate_limit_exceeded(
        self,
        identifier: str,
        limit: int,
        window: int,
        ip_address: str,
    ):
        """Log rate limit exceeded"""
        self.logger.warning(
            "Rate limit exceeded",
            identifier=identifier,
            limit=limit,
            window=window,
            ip_address=ip_address,
        )
    
    def log_suspicious_request(
        self,
        ip_address: str,
        path: str,
        method: str,
        reason: str,
        details: Dict[str, Any],
    ):
        """Log suspicious request"""
        self.logger.warning(
            "Suspicious request detected",
            ip_address=ip_address,
            path=path,
            method=method,
            reason=reason,
            details=details,
        )


class DatabaseLogger:
    """Logger for database operations"""
    
    def __init__(self):
        self.logger = structlog.get_logger("database")
    
    def log_query(
        self,
        collection: str,
        operation: str,
        query: Dict[str, Any],
        duration_ms: float,
        result_count: int = None,
    ):
        """Log database query"""
        self.logger.debug(
            "Database query",
            collection=collection,
            operation=operation,
            query=query,
            duration_ms=duration_ms,
            result_count=result_count,
        )
    
    def log_connection_error(self, error: Exception, retry_count: int):
        """Log database connection error"""
        self.logger.error(
            "Database connection error",
            error=str(error),
            error_type=type(error).__name__,
            retry_count=retry_count,
            exc_info=True,
        )
    
    def log_slow_query(
        self,
        collection: str,
        operation: str,
        query: Dict[str, Any],
        duration_ms: float,
        threshold_ms: float = 1000,
    ):
        """Log slow database query"""
        self.logger.warning(
            "Slow database query detected",
            collection=collection,
            operation=operation,
            query=query,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
        )


# Global logger instances
ai_logger = AILogger()
security_logger = SecurityLogger()
database_logger = DatabaseLogger()
websocket_logger = WebSocketLogger()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


# Exception logging
def log_exception(logger: structlog.stdlib.BoundLogger, exception: Exception, context: Dict[str, Any] = None):
    """Log exception with context"""
    logger.error(
        "Exception occurred",
        exception=str(exception),
        exception_type=type(exception).__name__,
        context=context or {},
        exc_info=True,
    )


# Performance logging
import time
from functools import wraps


def log_performance(logger: structlog.stdlib.BoundLogger):
    """Decorator to log function performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    "Function executed successfully",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    args_count=len(args),
                    kwargs_count=len(kwargs),
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "Function execution failed",
                    function=func.__name__,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                
                raise
        return wrapper
    return decorator
