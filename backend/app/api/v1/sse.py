"""Server-Sent Events (SSE) stream for real-time paper notifications.

Feature 42: SSE /sse — push paper.indexed, alert.matched events to browser
clients without requiring a WebSocket.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.governance import AuditLog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/sse", tags=["events"])

# ---------------------------------------------------------------------------
# In-process event bus (single-worker deployments).
# For multi-worker, swap this with a Redis pub/sub subscription.
# ---------------------------------------------------------------------------

_subscribers: list[asyncio.Queue] = []


def broadcast_event(event_type: str, payload: dict) -> None:
    """Push an event to all active SSE subscribers.  Call from Celery tasks."""
    message = {
        "type": event_type,
        "data": payload,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
    dead: list[asyncio.Queue] = []
    for queue in _subscribers:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(queue)
    for q in dead:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass


async def _event_stream(
    queue: asyncio.Queue,
    request: Request,
    heartbeat_interval: int,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted messages until the client disconnects."""
    yield 'data: {"type": "connected"}\n\n'
    try:
        while True:
            # Check for client disconnect on each loop
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(
                    queue.get(), timeout=heartbeat_interval
                )
                payload = json.dumps(message, default=str)
                yield f"data: {payload}\n\n"
            except TimeoutError:
                # Send heartbeat ping to keep connection alive
                yield ": heartbeat\n\n"
    finally:
        try:
            _subscribers.remove(queue)
        except ValueError:
            pass
        logger.info("sse_client_disconnected")


@router.get("")
async def event_stream(
    request: Request,
    heartbeat: int = Query(
        30,
        ge=5,
        le=120,
        description="Heartbeat comment interval in seconds.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Open an SSE stream for real-time paper and alert notifications.

    Events pushed:
    - `paper.indexed` — a new paper finished the ingest pipeline
    - `alert.matched` — an alert rule matched a newly indexed paper
    - `connected` — sent immediately on connection

    Usage (JavaScript):
    ```js
    const es = new EventSource('/api/v1/sse');
    es.onmessage = (e) => console.log(JSON.parse(e.data));
    ```
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(queue)
    logger.info("sse_client_connected", remote=request.client)

    return StreamingResponse(
        _event_stream(queue, request, heartbeat),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/recent")
async def recent_events(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return recent audit log entries as a substitute for SSE history replay.

    Clients can call this on reconnect to catch up on missed events.
    """
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    entries = result.scalars().all()
    return {
        "count": len(entries),
        "events": [
            {
                "id": str(e.id),
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "created_at": str(e.created_at),
            }
            for e in entries
        ],
    }
