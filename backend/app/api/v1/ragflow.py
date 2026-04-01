"""RAGFlow workspace Q&A and sync control API."""
# mypy: disable-error-code="misc,untyped-decorator"

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user_id, get_db
from app.models.collection import Collection
from app.models.paper import Paper
from app.services.ragflow.dataset_registry import DatasetRegistryService, RagflowDocumentMapping
from app.services.ragflow.ragflow_client import RagflowClient
from app.services.ragflow.ragflow_query_service import RagflowQueryService

router = APIRouter(tags=["ragflow"])
sync_router = APIRouter(prefix="/ragflow", tags=["ragflow"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]


class AskRequest(BaseModel):
    """Request body for workspace/paper RAGFlow Q&A."""

    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)


class PaperAskRequest(BaseModel):
    """Request body for single-paper grounded Q&A."""

    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=25)


class SyncTriggerRequest(BaseModel):
    """Request body for manual sync triggers."""

    paper_id: str | None = None
    collection_id: str | None = None


@router.post("/workspaces/{collection_id}/ask")
async def ask_workspace(
    collection_id: str,
    body: AskRequest,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Ask a bounded question against a synced workspace collection."""
    if not settings.ragflow_sync_enabled:
        return {"enabled": False, "answer": None, "sources": []}
    await _require_collection(db, collection_id, user_id)

    service = RagflowQueryService(db)
    return await service.ask_workspace(collection_id, body.question, top_k=body.top_k)


@router.get("/workspaces/{collection_id}/evidence")
async def get_workspace_evidence(
    collection_id: str,
    db: DbSession,
    user_id: UserId,
    q: str = Query(..., min_length=1, max_length=2000),
    top_k: int = Query(15, ge=1, le=50),
) -> dict[str, Any]:
    """Return raw retrieval chunks for a workspace question."""
    if not settings.ragflow_sync_enabled:
        return {"enabled": False, "chunks": [], "total": 0}
    await _require_collection(db, collection_id, user_id)

    service = RagflowQueryService(db)
    return await service.get_evidence_pack(collection_id, q, top_k=top_k)


@router.post("/papers/{paper_id}/ask")
async def ask_paper(
    paper_id: str,
    body: PaperAskRequest,
    db: DbSession,
    _user_id: UserId,
) -> dict[str, Any]:
    """Ask a bounded question against a single synced paper."""
    if not settings.ragflow_sync_enabled:
        return {"enabled": False, "answer": None, "sources": []}
    await _require_paper(db, paper_id)

    service = RagflowQueryService(db)
    return await service.ask_paper(paper_id, body.question, top_k=body.top_k)


@sync_router.get("/sync/status")
async def get_sync_status(db: DbSession, _user_id: UserId) -> dict[str, Any]:
    """Return RAGFlow health, mapping counts, and freshness configuration."""
    total = await _count_mappings(db)
    paper_count = await _count_mappings(db, RagflowDocumentMapping.paper_id.is_not(None))
    collection_count = await _count_mappings(
        db,
        RagflowDocumentMapping.collection_id.is_not(None),
    )
    stale = await DatasetRegistryService(db).list_stale(settings.ragflow_sync_freshness_minutes)

    health: dict[str, Any] | None = None
    if settings.ragflow_sync_enabled:
        try:
            health = await RagflowClient().health()
        except Exception as exc:  # noqa: BLE001
            health = {"status": "error", "error": str(exc)}

    return {
        "enabled": settings.ragflow_sync_enabled,
        "freshness_minutes": settings.ragflow_sync_freshness_minutes,
        "health": health,
        "counts": {
            "total_mappings": total,
            "paper_mappings": paper_count,
            "collection_mappings": collection_count,
            "stale_mappings": len(stale),
        },
    }


@sync_router.post("/sync/trigger")
async def trigger_sync(
    body: SyncTriggerRequest,
    _user_id: UserId,
) -> dict[str, Any]:
    """Queue a paper or collection sync task."""
    if bool(body.paper_id) == bool(body.collection_id):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of paper_id or collection_id.",
        )

    if not settings.ragflow_sync_enabled:
        return {"enabled": False, "queued": False}

    if body.paper_id is not None:
        from app.services.ragflow.ragflow_sync_tasks import sync_paper_task

        task = sync_paper_task.delay(body.paper_id)
        return {"task_id": str(task.id), "queued": True}

    from app.services.ragflow.ragflow_sync_tasks import sync_collection_task

    task = sync_collection_task.delay(body.collection_id)
    return {"task_id": str(task.id), "queued": True}


class RoutedQueryRequest(BaseModel):
    """Request body for the intelligent query router."""

    query: str = Field(..., min_length=1, max_length=2000)
    collection_id: str | None = None
    paper_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class SynthesisRequest(BaseModel):
    """Request body for topic synthesis."""

    topic_query: str = Field(..., min_length=1, max_length=2000)
    max_papers: int = Field(default=20, ge=1, le=100)


@sync_router.post("/query/route")
async def routed_query(body: RoutedQueryRequest, db: DbSession, user_id: UserId) -> dict[str, Any]:
    """Classify and route a query to the best retrieval backend."""
    # Validate ownership if scoped to a collection
    cid = body.collection_id
    if cid is not None:
        await _require_collection(db, cid, user_id)
    from app.services.ragflow.query_router import QueryRouter

    qr = QueryRouter(db)
    return await qr.route(
        body.query,
        collection_id=body.collection_id,
        paper_id=body.paper_id,
        top_k=body.top_k,
    )


@router.post("/workspaces/{collection_id}/synthesize")
async def synthesize_topic(
    collection_id: str,
    body: SynthesisRequest,
    db: DbSession,
    user_id: UserId,
) -> dict[str, Any]:
    """Synthesize a structured overview for a curated topic collection."""
    if not settings.ragflow_sync_enabled:
        return {"enabled": False, "synthesis": None}
    await _require_collection(db, collection_id, user_id)

    from app.services.ragflow.topic_synthesis import TopicSynthesisService

    svc = TopicSynthesisService(db)
    return await svc.synthesize_topic(
        collection_id=collection_id,
        topic_query=body.topic_query,
        max_papers=body.max_papers,
    )


router.include_router(sync_router)


async def _require_collection(
    db: AsyncSession, collection_id: str, user_id: str | None = None,
) -> Collection:
    """Raise 404 if the collection does not exist; 403 if not owned."""
    result = await db.execute(
        select(Collection).where(
            Collection.id == collection_id,
            Collection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if user_id and str(collection.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return collection


async def _require_paper(db: AsyncSession, paper_id: str) -> Paper:
    """Raise 404 if the paper does not exist."""
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


async def _count_mappings(db: AsyncSession, *conditions: Any) -> int:
    """Count registry rows, optionally filtered by SQLAlchemy conditions."""
    query = select(func.count()).select_from(RagflowDocumentMapping)
    for condition in conditions:
        query = query.where(condition)
    result = await db.execute(query)
    value = result.scalar()
    return int(value) if isinstance(value, int) else 0
