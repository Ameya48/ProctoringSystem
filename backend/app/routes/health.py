from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any
import psutil

from fastapi import APIRouter, HTTPException, status, Response
from app.core.redis import get_redis
from app.core.config import settings
from app.db.mongo import get_db
# Temporarily disabled for demo
# from app.celery_app import celery_app
# from app.services.ai_detection import get_ai_detection_service
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Basic health check"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/detailed")
async def detailed_health() -> Dict[str, Any]:
    """Comprehensive health check with system status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Check database connection
    db_status = await check_database()
    health_status["checks"]["database"] = db_status
    if not db_status["healthy"]:
        overall_healthy = False
    
    # Check Redis connection
    redis_status = await check_redis()
    health_status["checks"]["redis"] = redis_status
    if not redis_status["healthy"]:
        overall_healthy = False
    
    # Check Celery (temporarily disabled)
    # celery_status = await check_celery()
    # health_status["checks"]["celery"] = celery_status
    # if not celery_status["healthy"]:
    #     overall_healthy = False
    
    # Check AI detection service (temporarily disabled)
    # ai_status = await check_ai_service()
    # health_status["checks"]["ai_service"] = ai_status
    # if not ai_status["healthy"]:
    #     overall_healthy = False
    
    # Check system resources
    system_status = check_system_resources()
    health_status["checks"]["system"] = system_status
    if not system_status["healthy"]:
        overall_healthy = False
    
    # Check storage
    storage_status = await check_storage()
    health_status["checks"]["storage"] = storage_status
    if not storage_status["healthy"]:
        overall_healthy = False
    
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    if not overall_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@router.get("/health/ready")
async def readiness() -> Dict[str, Any]:
    """Readiness probe - checks if application is ready to serve traffic"""
    try:
        # Check critical dependencies
        db_ok = await check_database()
        redis_ok = await check_redis()
        
        if db_ok["healthy"] and redis_ok["healthy"]:
            return {
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {
                    "database": db_ok,
                    "redis": redis_ok
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/health/live")
async def liveness() -> Dict[str, Any]:
    """Liveness probe - checks if application is alive"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": time.time() - psutil.boot_time()
    }


async def check_database() -> Dict[str, Any]:
    """Check database connection"""
    start_time = time.time()
    try:
        db = get_db()
        # Simple ping operation
        await db.admin.command('ping')
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "healthy": True,
            "response_time_ms": round(response_time, 2),
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "disconnected"
        }


async def check_redis() -> Dict[str, Any]:
    """Check Redis connection"""
    start_time = time.time()
    try:
        redis = await get_redis()
        await redis.redis.ping()
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "healthy": True,
            "response_time_ms": round(response_time, 2),
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "disconnected"
        }


async def check_celery() -> Dict[str, Any]:
    """Check Celery workers"""
    try:
        # Check if Celery app is configured
        inspect = celery_app.control.inspect()
        
        # Get active tasks
        active_tasks = inspect.active()
        
        # Get registered tasks
        registered_tasks = inspect.registered()
        
        # Get stats
        stats = inspect.stats()
        
        worker_count = len(active_tasks) if active_tasks else 0
        
        return {
            "healthy": worker_count > 0,
            "workers": worker_count,
            "active_tasks": len(active_tasks) if active_tasks else 0,
            "registered_tasks": len(registered_tasks) if registered_tasks else 0,
            "status": "running" if worker_count > 0 else "no_workers"
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "error"
        }


async def check_ai_service() -> Dict[str, Any]:
    """Check AI detection service"""
    try:
        ai_service = get_ai_detection_service()
        
        if not ai_service:
            return {
                "healthy": False,
                "error": "AI service not initialized",
                "status": "not_initialized"
            }
        
        # Check if service is responsive
        active_sessions = len(ai_service.session_states)
        
        return {
            "healthy": True,
            "active_sessions": active_sessions,
            "status": "running"
        }
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "error"
        }


def check_system_resources() -> Dict[str, Any]:
    """Check system resources"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Load average (Linux/Unix)
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            load_avg = [0, 0, 0]  # Windows fallback
        
        # Determine health based on thresholds
        cpu_healthy = cpu_percent < 80
        memory_healthy = memory_percent < 85
        disk_healthy = disk_percent < 90
        
        return {
            "healthy": cpu_healthy and memory_healthy and disk_healthy,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "load_average": load_avg,
            "status": "normal" if (cpu_healthy and memory_healthy and disk_healthy) else "warning"
        }
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "error"
        }


async def check_storage() -> Dict[str, Any]:
    """Check storage availability"""
    try:
        import os
        storage_path = "/app/storage"
        
        if not os.path.exists(storage_path):
            return {
                "healthy": False,
                "error": "Storage directory not found",
                "status": "missing"
            }
        
        # Check write permissions
        test_file = os.path.join(storage_path, ".health_check")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            writeable = True
        except Exception:
            writeable = False
        
        # Check disk space
        disk_usage = psutil.disk_usage(storage_path)
        free_space_gb = disk_usage.free / (1024**3)
        
        return {
            "healthy": writeable and free_space_gb > 1,  # At least 1GB free
            "writeable": writeable,
            "free_space_gb": round(free_space_gb, 2),
            "status": "available" if writeable and free_space_gb > 1 else "limited"
        }
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "status": "error"
        }


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application metrics
        ai_service = get_ai_detection_service()
        active_sessions = len(ai_service.session_states) if ai_service else 0
        
        # Format as Prometheus metrics
        metrics_text = f"""
# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu_percent}

# HELP system_memory_percent Memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent {memory.percent}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {disk.percent}

# HELP app_active_sessions Number of active AI detection sessions
# TYPE app_active_sessions gauge
app_active_sessions {active_sessions}

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {time.time() - psutil.boot_time()}
"""
        
        return Response(
            content=metrics_text,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect metrics"
        )

