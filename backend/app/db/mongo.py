from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db]

    # Ensure unique index on email
    await db["users"].create_index("email", unique=True)

    # Useful session indexes
    await db["sessions"].create_index([("status", 1), ("started_at", -1)])
    await db["sessions"].create_index([("student_id", 1), ("exam_id", 1), ("status", 1)])

    # Webcam logs indexes
    await db["webcam_logs"].create_index([("session_id", 1), ("captured_at", -1)])
    await db["webcam_logs"].create_index([("student_id", 1), ("captured_at", -1)])

    # Proctoring event indexes
    await db["proctoring_events"].create_index([("session_id", 1), ("timestamp", -1)])
    await db["proctoring_events"].create_index([("student_id", 1), ("timestamp", -1)])
    await db["proctoring_events"].create_index([("suspicious", 1), ("timestamp", -1)])

    # Recording indexes
    await db["recordings"].create_index([("session_id", 1), ("started_at", -1)])
    await db["recordings"].create_index([("student_id", 1), ("started_at", -1)])
    await db["recordings"].create_index([("status", 1), ("started_at", -1)])


async def close_mongo_connection() -> None:
    global client, db
    if client is not None:
        client.close()
    client = None
    db = None


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("MongoDB is not initialized. Did you forget to start the app?")
    return db

