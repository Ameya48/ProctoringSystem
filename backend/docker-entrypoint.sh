#!/bin/bash
set -e

# Wait for Redis to be ready
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    while ! python -c "import redis; redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
        echo "Redis unavailable, sleeping..."
        sleep 2
    done
    echo "Redis is ready!"
fi

# Wait for MongoDB to be ready
if [ -n "$MONGODB_URI" ]; then
    echo "Waiting for MongoDB..."
    while ! python -c "from motor.motor_asyncio import AsyncIOMotorClient; AsyncIOMotorClient('$MONGODB_URI').admin.command('ping')" 2>/dev/null; do
        echo "MongoDB unavailable, sleeping..."
        sleep 2
    done
    echo "MongoDB is ready!"
fi

# Wait for RabbitMQ to be ready
if [ -n "$RABBITMQ_URL" ]; then
    echo "Waiting for RabbitMQ..."
    while ! python -c "import kombu; kombu.Connection('$RABBITMQ_URL').connect()" 2>/dev/null; do
        echo "RabbitMQ unavailable, sleeping..."
        sleep 2
    done
    echo "RabbitMQ is ready!"
fi

# Run database migrations if needed
echo "Running database setup..."
python -c "
import asyncio
from app.db.mongo import connect_to_mongo, close_mongo_connection

async def setup():
    await connect_to_mongo()
    # Create indexes for better performance
    from app.db.mongo import get_db
    db = get_db()
    
    # Create indexes for collections
    await db['sessions'].create_index('student_id')
    await db['sessions'].create_index('started_at')
    await db['events'].create_index([('session_id', 1), ('timestamp', -1)])
    await db['webcam_logs'].create_index([('session_id', 1), ('captured_at', -1)])
    await db['ai_detections'].create_index([('session_id', 1), ('frame_timestamp', -1)])
    await db['ai_detections'].create_index('suspicious_score')
    
    await close_mongo_connection()
    print('Database setup completed!')

asyncio.run(setup())
"

# Start Celery worker if enabled
if [ "$ENABLE_CELERY_WORKER" = "true" ]; then
    echo "Starting Celery worker..."
    celery -A app.celery_app worker --loglevel=info --concurrency=4 &
fi

# Start the application
echo "Starting FastAPI application..."
exec "$@"
