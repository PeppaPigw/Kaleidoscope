"""Celery worker configuration and app factory."""

from celery import Celery
from kombu import Queue

from app.config import settings

CELERY_QUEUE_NAMES = (
    "celery",
    "ingestion",
    "parsing",
    "indexing",
    "embedding",
    "ragflow",
)

celery_app = Celery(
    "kaleidoscope",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.graph_tasks",
        "app.tasks.ingest_tasks",
        "app.tasks.embedding_tasks",
        "app.services.ragflow.ragflow_sync_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="celery",
    task_queues=tuple(Queue(name) for name in CELERY_QUEUE_NAMES),
    task_track_started=True,
    task_acks_late=True,  # Acknowledge after completion (not before)
    worker_prefetch_multiplier=1,  # One task at a time per worker
    imports=(
        "app.tasks.graph_tasks",
        "app.tasks.ingest_tasks",
        "app.tasks.embedding_tasks",
        "app.services.ragflow.ragflow_sync_tasks",
    ),
    # Task routing
    task_routes={
        "app.tasks.ingest_tasks.ingest_paper": {"queue": "ingestion"},
        "app.tasks.ingest_tasks.acquire_fulltext": {"queue": "ingestion"},
        "app.tasks.ingest_tasks.parse_fulltext_task": {"queue": "parsing"},
        "app.tasks.ingest_tasks.parse_via_mineru": {"queue": "parsing"},
        "app.tasks.ingest_tasks.index_paper_task": {"queue": "indexing"},
        "app.tasks.ingest_tasks.fetch_paper_links_task": {"queue": "ingestion"},
        # Keep lightweight tasks in default queue
        "app.tasks.ingest_tasks.poll_rss_feeds": {"queue": "celery"},
        "app.tasks.ingest_tasks.auto_discover_papers": {"queue": "celery"},
        "app.tasks.ingest_tasks.refresh_trending_keywords": {"queue": "celery"},
        "app.services.ragflow.ragflow_sync_tasks.*": {"queue": "ragflow"},
        "embedding.*": {"queue": "embedding"},
    },
    # Priority queue support for Redis broker
    broker_transport_options={
        "priority_steps": list(range(11)),
        "queue_order_strategy": "priority",
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "poll-rss-feeds": {
            "task": "app.tasks.ingest_tasks.poll_rss_feeds",
            "schedule": settings.rss_poll_interval_minutes * 60,  # seconds
        },
        "sweep-unembedded-papers": {
            "task": "embedding.sweep_unembedded_papers",
            "schedule": settings.paper_qa_sweep_interval_minutes * 60,  # seconds
        },
        "auto-discover-papers": {
            "task": "app.tasks.ingest_tasks.auto_discover_papers",
            "schedule": 3600,  # Run every hour
        },
        "refresh-trending-keywords": {
            "task": "app.tasks.ingest_tasks.refresh_trending_keywords",
            "schedule": 21600,  # Run every 6 hours
        },
    },
)
