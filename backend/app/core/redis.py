from __future__ import annotations

import json
import pickle
from typing import Any, Optional, Union
import aioredis
from aioredis import Redis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RedisService:
    """Redis service for caching and session management"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # Handle binary data properly
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            # Test connection
            await self.redis.ping()
            self._connected = True
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self._connected or not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            self._connected = False
            return False
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set a value in Redis"""
        try:
            if serialize:
                value = pickle.dumps(value)
            
            result = await self.redis.set(key, value, ex=expire)
            return result is True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def get(
        self,
        key: str,
        deserialize: bool = True,
        default: Any = None
    ) -> Any:
        """Get a value from Redis"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return default
            
            if deserialize:
                return pickle.loads(value)
            return value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            result = await self.redis.expire(key, seconds)
            return result is True
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a value"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None
    
    async def hset(self, name: str, mapping: dict) -> bool:
        """Set hash fields"""
        try:
            # Serialize values if needed
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list, tuple)):
                    serialized_mapping[k] = json.dumps(v)
                else:
                    serialized_mapping[k] = str(v)
            
            result = await self.redis.hset(name, mapping=serialized_mapping)
            return result > 0
        except Exception as e:
            logger.error(f"Redis hset error for {name}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Any:
        """Get hash field"""
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis hget error for {name}.{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> dict:
        """Get all hash fields"""
        try:
            data = await self.redis.hgetall(name)
            result = {}
            
            for key, value in data.items():
                # Try to parse as JSON
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"Redis hgetall error for {name}: {e}")
            return {}
    
    async def lpush(self, name: str, *values: Any) -> Optional[int]:
        """Push values to list"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, tuple)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            
            return await self.redis.lpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis lpush error for {name}: {e}")
            return None
    
    async def rpop(self, name: str) -> Any:
        """Pop value from list"""
        try:
            value = await self.redis.rpop(name)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis rpop error for {name}: {e}")
            return None
    
    async def lrange(self, name: str, start: int = 0, end: int = -1) -> list:
        """Get range of list values"""
        try:
            values = await self.redis.lrange(name, start, end)
            result = []
            
            for value in values:
                # Try to parse as JSON
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            
            return result
        except Exception as e:
            logger.error(f"Redis lrange error for {name}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """Flush current database"""
        try:
            result = await self.redis.flushdb()
            return result is True
        except Exception as e:
            logger.error(f"Redis flushdb error: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()


async def get_redis() -> RedisService:
    """Get Redis service instance"""
    if not redis_service._connected:
        await redis_service.connect()
    return redis_service


# Cache decorators
def cache_result(expire: int = 300, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            redis = await get_redis()
            
            # Try to get from cache
            cached_result = await redis.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis.set(cache_key, result, expire=expire)
            logger.debug(f"Cache set for {cache_key}")
            
            return result
        return wrapper
    return decorator


# Rate limiting
async def check_rate_limit(
    identifier: str,
    limit: int = 100,
    window: int = 60
) -> tuple[bool, dict]:
    """
    Check rate limit for identifier
    Returns (allowed, info_dict)
    """
    redis = await get_redis()
    
    current_time = int(time.time())
    window_start = current_time - window
    
    # Clean old entries
    await redis.zremrangebyscore(f"rate_limit:{identifier}", 0, window_start)
    
    # Count current requests
    current_requests = await redis.zcard(f"rate_limit:{identifier}")
    
    if current_requests >= limit:
        # Get oldest request for retry-after
        oldest = await redis.zrange(f"rate_limit:{identifier}", 0, 0, withscores=True)
        retry_after = int(oldest[0][1]) + window - current_time if oldest else window
        
        return False, {
            "limit": limit,
            "remaining": 0,
            "reset": current_time + window,
            "retry_after": retry_after
        }
    
    # Add current request
    await redis.zadd(f"rate_limit:{identifier}", {str(current_time): current_time})
    await redis.expire(f"rate_limit:{identifier}", window)
    
    return True, {
        "limit": limit,
        "remaining": limit - current_requests - 1,
        "reset": current_time + window,
        "retry_after": 0
    }
