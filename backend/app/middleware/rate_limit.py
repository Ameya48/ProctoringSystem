from __future__ import annotations

import time
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

from app.core.redis import check_rate_limit
from app.core.logging import security_logger

logger = structlog.get_logger(__name__)


class CustomLimiter(Limiter):
    """Custom rate limiter using Redis"""
    
    def __init__(self, key_func: Callable = get_remote_address):
        self.key_func = key_func
        self.logger = structlog.get_logger("rate_limit")
    
    async def check(self, limit: int, window: int) -> bool:
        """Check if request is allowed"""
        identifier = self.key_func()
        
        try:
            allowed, info = await check_rate_limit(identifier, limit, window)
            
            if not allowed:
                self.logger.warning(
                    "Rate limit exceeded",
                    identifier=identifier,
                    limit=limit,
                    window=window,
                    retry_after=info.get("retry_after", 0),
                )
                
                # Log security event
                security_logger.log_rate_limit_exceeded(
                    identifier=identifier,
                    limit=limit,
                    window=window,
                    ip_address=identifier,
                )
                
                raise RateLimitExceeded(
                    detail=f"Rate limit exceeded. Try again in {info.get('retry_after', 0)} seconds."
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True


# Global limiter instance
limiter = CustomLimiter()


class RateLimitMiddleware:
    """Rate limiting middleware for FastAPI"""
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger("rate_limit_middleware")
        
        # Rate limit configurations
        self.rate_limits = {
            # Global limits
            "global": {"limit": 1000, "window": 60},  # 1000 requests per minute
            
            # API endpoints
            "/auth/login": {"limit": 5, "window": 300},  # 5 login attempts per 5 minutes
            "/auth/register": {"limit": 3, "window": 300},  # 3 registrations per 5 minutes
            "/webcam": {"limit": 60, "window": 60},  # 60 webcam requests per minute
            "/ai/analyze-frame": {"limit": 30, "window": 60},  # 30 AI analyses per minute
            
            # WebSocket connections
            "/ws/webcam": {"limit": 10, "window": 60},  # 10 WebSocket connections per minute
            "/ws/sessions": {"limit": 20, "window": 60},  # 20 session connections per minute
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Get rate limit for this path
            rate_limit = self._get_rate_limit(request.url.path)
            
            if rate_limit:
                try:
                    await limiter.check(rate_limit["limit"], rate_limit["window"])
                except RateLimitExceeded as e:
                    # Create rate limit response
                    response = self._create_rate_limit_response(e)
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
    
    def _get_rate_limit(self, path: str) -> dict:
        """Get rate limit configuration for path"""
        # Check for exact matches first
        if path in self.rate_limits:
            return self.rate_limits[path]
        
        # Check for prefix matches
        for pattern, config in self.rate_limits.items():
            if pattern != "global" and path.startswith(pattern):
                return config
        
        # Return global limit
        return self.rate_limits["global"]
    
    def _create_rate_limit_response(self, error: RateLimitExceeded) -> JSONResponse:
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "detail": str(error.detail),
                "code": "RATE_LIMIT_EXCEEDED"
            },
            headers={
                "Retry-After": str(60),  # Default retry after
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60),
            }
        )


class UserBasedRateLimiter:
    """Rate limiter based on user ID"""
    
    def __init__(self):
        self.logger = structlog.get_logger("user_rate_limit")
    
    async def check_user_rate_limit(
        self,
        user_id: str,
        action: str,
        limit: int = 100,
        window: int = 60
    ) -> bool:
        """Check rate limit for specific user action"""
        identifier = f"user:{user_id}:{action}"
        
        try:
            allowed, info = await check_rate_limit(identifier, limit, window)
            
            if not allowed:
                self.logger.warning(
                    "User rate limit exceeded",
                    user_id=user_id,
                    action=action,
                    limit=limit,
                    window=window,
                    retry_after=info.get("retry_after", 0),
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {action}. Try again in {info.get('retry_after', 0)} seconds."
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"User rate limit check error: {e}")
            return True


class SessionBasedRateLimiter:
    """Rate limiter based on session ID"""
    
    def __init__(self):
        self.logger = structlog.get_logger("session_rate_limit")
    
    async def check_session_rate_limit(
        self,
        session_id: str,
        action: str,
        limit: int = 60,
        window: int = 60
    ) -> bool:
        """Check rate limit for specific session action"""
        identifier = f"session:{session_id}:{action}"
        
        try:
            allowed, info = await check_rate_limit(identifier, limit, window)
            
            if not allowed:
                self.logger.warning(
                    "Session rate limit exceeded",
                    session_id=session_id,
                    action=action,
                    limit=limit,
                    window=window,
                    retry_after=info.get("retry_after", 0),
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for session {action}. Try again in {info.get('retry_after', 0)} seconds."
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session rate limit check error: {e}")
            return True


class IPBasedRateLimiter:
    """Rate limiter based on IP address"""
    
    def __init__(self):
        self.logger = structlog.get_logger("ip_rate_limit")
    
    async def check_ip_rate_limit(
        self,
        ip_address: str,
        action: str,
        limit: int = 200,
        window: int = 60
    ) -> bool:
        """Check rate limit for specific IP action"""
        identifier = f"ip:{ip_address}:{action}"
        
        try:
            allowed, info = await check_rate_limit(identifier, limit, window)
            
            if not allowed:
                self.logger.warning(
                    "IP rate limit exceeded",
                    ip_address=ip_address,
                    action=action,
                    limit=limit,
                    window=window,
                    retry_after=info.get("retry_after", 0),
                )
                
                # Log suspicious activity
                security_logger.log_suspicious_request(
                    ip_address=ip_address,
                    path=f"rate_limit:{action}",
                    method="RATE_LIMIT",
                    reason="Excessive requests",
                    details={
                        "limit": limit,
                        "window": window,
                        "retry_after": info.get("retry_after", 0),
                    }
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded from this IP. Try again in {info.get('retry_after', 0)} seconds."
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"IP rate limit check error: {e}")
            return True


# Global rate limiter instances
user_rate_limiter = UserBasedRateLimiter()
session_rate_limiter = SessionBasedRateLimiter()
ip_rate_limiter = IPBasedRateLimiter()


# Rate limit decorators
def rate_limit(limit: int, window: int, key_func: Callable = None):
    """Rate limit decorator for endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get identifier
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                identifier = get_remote_address()
            
            try:
                allowed, info = await check_rate_limit(identifier, limit, window)
                
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {info.get('retry_after', 0)} seconds."
                    )
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Rate limit decorator error: {e}")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# WebSocket rate limiting
class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections"""
    
    def __init__(self):
        self.logger = structlog.get_logger("websocket_rate_limit")
        self.connection_counts = {}
    
    async def check_connection_limit(self, ip_address: str, limit: int = 10) -> bool:
        """Check WebSocket connection limit per IP"""
        current_time = int(time.time())
        window_start = current_time - 60  # 1 minute window
        
        # Clean old connections
        if ip_address in self.connection_counts:
            self.connection_counts[ip_address] = [
                timestamp for timestamp in self.connection_counts[ip_address]
                if timestamp > window_start
            ]
        else:
            self.connection_counts[ip_address] = []
        
        # Check current connections
        if len(self.connection_counts[ip_address]) >= limit:
            self.logger.warning(
                "WebSocket connection limit exceeded",
                ip_address=ip_address,
                current_connections=len(self.connection_counts[ip_address]),
                limit=limit,
            )
            
            return False
        
        # Add current connection
        self.connection_counts[ip_address].append(current_time)
        return True
    
    async def check_message_rate(
        self,
        connection_id: str,
        limit: int = 60,
        window: int = 60
    ) -> bool:
        """Check WebSocket message rate"""
        identifier = f"ws_message:{connection_id}"
        
        try:
            allowed, info = await check_rate_limit(identifier, limit, window)
            
            if not allowed:
                self.logger.warning(
                    "WebSocket message rate limit exceeded",
                    connection_id=connection_id,
                    limit=limit,
                    window=window,
                    retry_after=info.get("retry_after", 0),
                )
                
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"WebSocket message rate limit error: {e}")
            return True


# Global WebSocket rate limiter
websocket_rate_limiter = WebSocketRateLimiter()
