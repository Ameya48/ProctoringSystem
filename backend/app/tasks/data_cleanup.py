from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.celery_app import celery_app
from app.db.mongo import get_db
from app.core.logging import get_logger
import structlog

logger = structlog.get_logger(__name__)


@celery_app.task
def cleanup_old_data() -> Dict[str, Any]:
    """Clean up old data from database"""
    try:
        logger.info("Starting data cleanup task")
        
        # Define cleanup periods
        cleanup_periods = {
            "webcam_logs": timedelta(days=30),  # Keep 30 days
            "ai_detections": timedelta(days=30),  # Keep 30 days
            "ai_alerts": timedelta(days=90),  # Keep 90 days
            "events": timedelta(days=60),  # Keep 60 days
        }
        
        cleanup_results = {}
        
        async def _cleanup_async():
            db = get_db()
            
            for collection_name, period in cleanup_periods.items():
                cutoff_date = datetime.now(timezone.utc) - period
                
                # Count documents to be deleted
                count_query = {"timestamp": {"$lt": cutoff_date}}
                count = await db[collection_name].count_documents(count_query)
                
                if count > 0:
                    # Delete old documents
                    result = await db[collection_name].delete_many(count_query)
                    
                    cleanup_results[collection_name] = {
                        "deleted_count": result.deleted_count,
                        "cutoff_date": cutoff_date.isoformat(),
                    }
                    
                    logger.info(
                        f"Cleaned up {collection_name}",
                        deleted_count=result.deleted_count,
                        cutoff_date=cutoff_date.isoformat(),
                    )
                else:
                    cleanup_results[collection_name] = {
                        "deleted_count": 0,
                        "cutoff_date": cutoff_date.isoformat(),
                    }
            
            # Clean up expired sessions
            expired_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            expired_sessions = await db["sessions"].find({
                "started_at": {"$lt": expired_cutoff},
                "status": {"$ne": "active"}
            }).to_list(length=1000)
            
            expired_count = 0
            for session in expired_sessions:
                # Check if session has recent activity
                recent_activity = await db["events"].find_one({
                    "session_id": session["_id"],
                    "timestamp": {"$gt": expired_cutoff}
                })
                
                if not recent_activity:
                    # Archive session instead of deleting
                    await db["archived_sessions"].insert_one(session)
                    await db["sessions"].delete_one({"_id": session["_id"]})
                    expired_count += 1
            
            cleanup_results["expired_sessions"] = {
                "archived_count": expired_count,
                "cutoff_date": expired_cutoff.isoformat(),
            }
            
            if expired_count > 0:
                logger.info(
                    "Archived expired sessions",
                    archived_count=expired_count,
                    cutoff_date=expired_cutoff.isoformat(),
                )
        
        # Run async cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_cleanup_async())
        finally:
            loop.close()
        
        total_deleted = sum(result["deleted_count"] for result in cleanup_results.values())
        
        logger.info(
            "Data cleanup completed",
            total_deleted=total_deleted,
            collections_processed=list(cleanup_periods.keys()),
        )
        
        return {
            "success": True,
            "total_deleted": total_deleted,
            "cleanup_results": cleanup_results,
        }
        
    except Exception as exc:
        logger.error(f"Data cleanup failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
        }


@celery_app.task
def cleanup_expired_sessions() -> Dict[str, Any]:
    """Clean up expired sessions"""
    try:
        logger.info("Starting expired sessions cleanup")
        
        async def _cleanup_expired_async():
            db = get_db()
            
            # Find sessions that have been inactive for more than 24 hours
            inactive_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            
            inactive_sessions = await db["sessions"].find({
                "status": "active",
                "last_activity": {"$lt": inactive_cutoff}
            }).to_list(length=1000)
            
            archived_count = 0
            for session in inactive_sessions:
                # Update session status to expired
                await db["sessions"].update_one(
                    {"_id": session["_id"]},
                    {
                        "$set": {
                            "status": "expired",
                            "expired_at": datetime.now(timezone.utc),
                        }
                    }
                )
                
                # Archive session data
                session_data = await db["sessions"].find_one({"_id": session["_id"]})
                if session_data:
                    await db["archived_sessions"].insert_one(session_data)
                    archived_count += 1
                
                # Clean up AI service session state
                from app.services.ai_detection import get_ai_detection_service
                ai_service = get_ai_detection_service()
                if ai_service:
                    ai_service.cleanup_session(session["_id"])
            
            return len(inactive_sessions), archived_count
        
        # Run async cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sessions_processed, archived_count = loop.run_until_complete(_cleanup_expired_async())
        finally:
            loop.close()
        
        logger.info(
            "Expired sessions cleanup completed",
            sessions_processed=sessions_processed,
            archived_count=archived_count,
        )
        
        return {
            "success": True,
            "sessions_processed": sessions_processed,
            "archived_count": archived_count,
        }
        
    except Exception as exc:
        logger.error(f"Expired sessions cleanup failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
        }


@celery_app.task
def optimize_database() -> Dict[str, Any]:
    """Optimize database performance"""
    try:
        logger.info("Starting database optimization")
        
        async def _optimize_async():
            db = get_db()
            optimization_results = {}
            
            # Create indexes for better performance
            indexes = [
                # Sessions collection
                {"collection": "sessions", "index": [("student_id", 1)], "name": "student_id_idx"},
                {"collection": "sessions", "index": [("started_at", -1)], "name": "started_at_idx"},
                {"collection": "sessions", "index": [("status", 1)], "name": "status_idx"},
                
                # Events collection
                {"collection": "events", "index": [("session_id", 1), ("timestamp", -1)], "name": "session_timestamp_idx"},
                {"collection": "events", "index": [("event_type", 1)], "name": "event_type_idx"},
                
                # Webcam logs collection
                {"collection": "webcam_logs", "index": [("session_id", 1), ("captured_at", -1)], "name": "session_captured_at_idx"},
                
                # AI detections collection
                {"collection": "ai_detections", "index": [("session_id", 1), ("frame_timestamp", -1)], "name": "session_frame_timestamp_idx"},
                {"collection": "ai_detections", "index": [("suspicious_score", -1)], "name": "suspicious_score_idx"},
                
                # AI alerts collection
                {"collection": "ai_alerts", "index": [("session_id", 1), ("timestamp", -1)], "name": "session_alert_timestamp_idx"},
                {"collection": "ai_alerts", "index": [("acknowledged", 1)], "name": "acknowledged_idx"},
            ]
            
            for index_config in indexes:
                collection_name = index_config["collection"]
                index_spec = index_config["index"]
                index_name = index_config["name"]
                
                try:
                    await db[collection_name].create_index(index_spec, name=index_name)
                    optimization_results[f"{collection_name}_{index_name}"] = "created"
                except Exception as e:
                    optimization_results[f"{collection_name}_{index_name}"] = f"failed: {str(e)}"
            
            # Compact collections (if supported)
            collections_to_compact = ["events", "webcam_logs", "ai_detections"]
            for collection_name in collections_to_compact:
                try:
                    # This is a MongoDB operation that may require admin privileges
                    await db.command({"compact": collection_name})
                    optimization_results[f"compact_{collection_name}"] = "completed"
                except Exception as e:
                    optimization_results[f"compact_{collection_name}"] = f"skipped: {str(e)}"
            
            return optimization_results
        
        # Run async optimization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            optimization_results = loop.run_until_complete(_optimize_async())
        finally:
            loop.close()
        
        logger.info(
            "Database optimization completed",
            results=optimization_results,
        )
        
        return {
            "success": True,
            "optimization_results": optimization_results,
        }
        
    except Exception as exc:
        logger.error(f"Database optimization failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
        }
