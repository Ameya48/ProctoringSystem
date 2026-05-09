from __future__ import annotations

import os
from celery import Celery
from kombu import Queue
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Celery configuration
celery_app = Celery(
    "proctoring_system",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ai_processing",
        "app.tasks.email_notifications",
        "app.tasks.data_cleanup",
        "app.tasks.analytics",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Queue settings
    task_routes={
        "app.tasks.ai_processing.*": {"queue": "ai_processing"},
        "app.tasks.email_notifications.*": {"queue": "notifications"},
        "app.tasks.data_cleanup.*": {"queue": "cleanup"},
        "app.tasks.analytics.*": {"queue": "analytics"},
    },
    
    # Define queues
    task_queues=(
        Queue("ai_processing", routing_key="ai_processing"),
        Queue("notifications", routing_key="notifications"),
        Queue("cleanup", routing_key="cleanup"),
        Queue("analytics", routing_key="analytics"),
        Queue("default", routing_key="default"),
    ),
    
    # Default queue
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Worker settings
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Beat scheduler settings
    beat_schedule={
        # Cleanup old data every hour
        "cleanup-old-data": {
            "task": "app.tasks.data_cleanup.cleanup_old_data",
            "schedule": 3600.0,  # 1 hour
        },
        
        # Generate analytics reports every 30 minutes
        "generate-analytics": {
            "task": "app.tasks.analytics.generate_session_analytics",
            "schedule": 1800.0,  # 30 minutes
        },
        
        # Send performance alerts every 15 minutes
        "performance-alerts": {
            "task": "app.tasks.analytics.check_performance_alerts",
            "schedule": 900.0,  # 15 minutes
        },
        
        # Cleanup expired sessions every 5 minutes
        "cleanup-expired-sessions": {
            "task": "app.tasks.data_cleanup.cleanup_expired_sessions",
            "schedule": 300.0,  # 5 minutes
        },
    },
)

# Optional: Configure for production
if os.getenv("CELERY_BROKER_URL"):
    celery_app.conf.broker_url = os.getenv("CELERY_BROKER_URL")

if os.getenv("CELERY_RESULT_BACKEND"):
    celery_app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND")


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    logger.info(f"Request: {self.request!r}")
    return f"Debug task executed: {self.request!r}"


# Error handling
@celery_app.task(bind=True)
def error_handler_task(self, task_id, error, traceback):
    """Handle task errors"""
    logger.error(
        f"Task {task_id} failed with error: {error}",
        traceback=traceback,
        task_id=task_id,
    )


# Connect to error handling
celery_app.task_postrun.connect(error_handler_task)


# Health check task
@celery_app.task
def health_check():
    """Health check task for Celery"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
