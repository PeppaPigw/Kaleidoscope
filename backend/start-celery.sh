#!/bin/bash
# Start Celery Worker and Beat for Kaleidoscope

cd "$(dirname "$0")/.."
CELERY_QUEUES="celery,ingestion,parsing,indexing,embedding,ragflow"

echo "Starting Celery Worker..."
celery -A app.worker.celery_app worker --loglevel=info --concurrency=4 -Q "$CELERY_QUEUES" &
WORKER_PID=$!

echo "Starting Celery Beat (Scheduler)..."
celery -A app.worker.celery_app beat --loglevel=info &
BEAT_PID=$!

echo ""
echo "✓ Celery Worker started (PID: $WORKER_PID)"
echo "✓ Celery Beat started (PID: $BEAT_PID)"
echo ""
echo "Auto-discovery task will run every hour."
echo "Dashboard auto-ingest is active when users visit /dashboard."
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for Ctrl+C
trap "kill $WORKER_PID $BEAT_PID; exit" INT TERM

wait
