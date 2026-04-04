"""Celery worker configuration and app factory."""

from celery import Celery

from app.config import settings

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
        "app.tasks.ingest_tasks.*": {"queue": "ingestion"},
        "app.tasks.parse_tasks.*": {"queue": "parsing"},
        "app.tasks.index_tasks.*": {"queue": "indexing"},
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
    },
)
