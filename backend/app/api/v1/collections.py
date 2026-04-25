"""Collections API — CRUD, paper management, smart collections."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id
from app.schemas.collection import (
    CollectionChatMessageAsk,
    CollectionChatMessageResponse,
    CollectionChatThreadCreate,
    CollectionChatThreadResponse,
    CollectionCreate,
    CollectionDetailResponse,
    CollectionFeedSubscriptionCreate,
    CollectionFeedSubscriptionResponse,
    CollectionPaperAdd,
    CollectionPaperReorder,
    CollectionPaperResponse,
    CollectionResponse,
    CollectionUpdate,
    ExportRequest,
)
from app.services.collection_service import (
    CollectionChatService,
    CollectionService,
    ReadingStatusService,
)
from app.services.export_service import ExportService
from app.services.ragflow.ragflow_query_service import RagflowQueryService

router = APIRouter(prefix="/collections", tags=["collections"])


# ─── Collection CRUD ─────────────────────────────────────────────


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(
    body: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.create_collection(
        name=body.name,
        description=body.description,
        kind=body.kind,
        color=body.color,
        icon=body.icon,
        parent_collection_id=(
            str(body.parent_collection_id) if body.parent_collection_id else None
        ),
        is_smart=body.is_smart,
        smart_filter=body.smart_filter,
    )
    return collection


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    kind: str | None = Query(None),
    parent_collection_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all collections for the current user."""
    svc = CollectionService(db, user_id)
    return await svc.list_collections(
        kind=kind,
        parent_collection_id=parent_collection_id,
    )


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get collection with papers."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    papers = await svc.get_collection_papers(collection_id)

    return {
        **{k: getattr(collection, k) for k in CollectionResponse.model_fields},
        "smart_filter": collection.smart_filter,
        "papers": papers,
    }


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    body: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.update_collection(
        collection_id, **body.model_dump(exclude_none=True)
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Soft-delete a collection."""
    svc = CollectionService(db, user_id)
    if not await svc.delete_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")


@router.get("/{collection_id}/children", response_model=list[CollectionResponse])
async def list_child_collections(
    collection_id: str,
    kind: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List child collections for a parent collection."""
    svc = CollectionService(db, user_id)
    parent = await svc.get_collection(collection_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Collection not found")
    return await svc.list_child_collections(collection_id, kind=kind)


# ─── Paper Management ────────────────────────────────────────────


@router.post("/{collection_id}/papers", status_code=201)
async def add_papers_to_collection(
    collection_id: str,
    body: CollectionPaperAdd,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Add paper(s) to a collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    added = await svc.add_papers(
        collection_id,
        [str(pid) for pid in body.paper_ids],
        note=body.note,
    )
    return {"added": added, "total": collection.paper_count + added}


@router.delete("/{collection_id}/papers/{paper_id}", status_code=204)
async def remove_paper_from_collection(
    collection_id: str,
    paper_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Remove a paper from a collection."""
    svc = CollectionService(db, user_id)
    if not await svc.remove_paper(collection_id, paper_id):
        raise HTTPException(status_code=404, detail="Paper not in collection")


@router.patch("/{collection_id}/papers/reorder", status_code=200)
async def reorder_collection_papers(
    collection_id: str,
    body: CollectionPaperReorder,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Reorder papers in a collection."""
    svc = CollectionService(db, user_id)
    await svc.reorder_papers(collection_id, [str(pid) for pid in body.paper_ids])
    return {"status": "reordered"}


@router.get("/{collection_id}/papers", response_model=list[CollectionPaperResponse])
async def get_collection_papers(
    collection_id: str,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List papers in a collection with details."""
    svc = CollectionService(db, user_id)
    return await svc.get_collection_papers(collection_id, limit=limit, offset=offset)


@router.post(
    "/{collection_id}/feeds",
    response_model=list[CollectionFeedSubscriptionResponse],
    status_code=201,
)
async def attach_feeds_to_collection(
    collection_id: str,
    body: CollectionFeedSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Attach RSS feeds to a subscription collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    if collection.kind != "subscription_collection":
        raise HTTPException(
            status_code=422,
            detail="Feeds can only be attached to subscription collections",
        )
    await svc.attach_feeds(collection_id, [str(feed_id) for feed_id in body.feed_ids])
    return await svc.list_feed_subscriptions(collection_id)


@router.get(
    "/{collection_id}/feeds",
    response_model=list[CollectionFeedSubscriptionResponse],
)
async def list_collection_feeds(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List RSS feeds attached to a subscription collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return await svc.list_feed_subscriptions(collection_id)


@router.delete("/{collection_id}/feeds/{feed_id}", status_code=204)
async def detach_feed_from_collection(
    collection_id: str,
    feed_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Detach a feed from a subscription collection."""
    svc = CollectionService(db, user_id)
    if not await svc.detach_feed(collection_id, feed_id):
        raise HTTPException(status_code=404, detail="Feed subscription not found")


@router.post(
    "/{collection_id}/threads",
    response_model=CollectionChatThreadResponse,
    status_code=201,
)
async def create_collection_thread(
    collection_id: str,
    body: CollectionChatThreadCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new chat thread scoped to a collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    chat = CollectionChatService(db, user_id)
    return await chat.create_thread(collection_id, body.title)


@router.get(
    "/{collection_id}/threads",
    response_model=list[CollectionChatThreadResponse],
)
async def list_collection_threads(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List chat threads scoped to a collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    chat = CollectionChatService(db, user_id)
    return await chat.list_threads(collection_id)


@router.get(
    "/{collection_id}/threads/{thread_id}/messages",
    response_model=list[CollectionChatMessageResponse],
)
async def list_collection_thread_messages(
    collection_id: str,
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List persisted messages in a collection thread."""
    chat = CollectionChatService(db, user_id)
    thread = await chat.get_thread(collection_id, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return await chat.list_messages(collection_id, thread_id)


@router.post("/{collection_id}/threads/{thread_id}/ask", status_code=201)
async def ask_collection_thread(
    collection_id: str,
    thread_id: str,
    body: CollectionChatMessageAsk,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Persist a user message and generate an assistant reply for a collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    chat = CollectionChatService(db, user_id)
    thread = await chat.get_thread(collection_id, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    user_message = await chat.create_message(
        thread_id=thread_id,
        role="user",
        content=body.content.strip(),
    )

    # Use local RAG service (primary) with RAGFlow fallback
    from app.services.local_rag_service import LocalRAGService
    from app.config import settings

    if settings.ragflow_sync_enabled:
        # Use RAGFlow if explicitly enabled
        ragflow = RagflowQueryService(db)
        answer = await ragflow.ask_workspace(
            collection_id, body.content.strip(), body.top_k
        )
        assistant_content = answer.get("answer")
        if not assistant_content:
            if answer.get("enabled") is False:
                assistant_content = (
                    "Group chat is unavailable because RAGFlow sync is disabled."
                )
            elif (
                answer.get("ready") is False
                or answer.get("message") == "sync_in_progress"
            ):
                assistant_content = "This group is still syncing. Try again shortly."
            else:
                assistant_content = "I could not find a synced dataset for this group yet. Add papers or trigger sync, then ask again."
        sources = answer.get("sources", [])
        metadata = {
            "latency_ms": answer.get("latency_ms"),
            "enabled": answer.get("enabled"),
            "ready": answer.get("ready"),
            "error": answer.get("error"),
            "message": answer.get("message"),
            "rag_backend": "ragflow",
        }
    else:
        # Use local RAG service (default)
        local_rag = LocalRAGService(db)
        answer = await local_rag.ask_collection(
            collection_id=collection_id,
            question=body.content.strip(),
            top_k=body.top_k,
        )
        assistant_content = answer.get(
            "answer", "I encountered an error processing your question."
        )
        sources = answer.get("sources", [])
        metadata = {
            "latency_ms": answer.get("latency_ms"),
            "chunks_found": answer.get("chunks_found"),
            "error": answer.get("error"),
            "rag_backend": "local",
        }

    assistant_message = await chat.create_message(
        thread_id=thread_id,
        role="assistant",
        content=assistant_content,
        sources={"items": sources},
        metadata_json=metadata,
    )

    return {
        "thread_id": thread_id,
        "user_message": CollectionChatMessageResponse.model_validate(user_message),
        "assistant_message": CollectionChatMessageResponse.model_validate(
            assistant_message
        ),
    }


# ─── Smart Collection ────────────────────────────────────────────


@router.get("/{collection_id}/evaluate")
async def evaluate_smart_collection(
    collection_id: str,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Evaluate a smart collection's filter and return matching papers."""
    svc = CollectionService(db, user_id)
    rs_svc = ReadingStatusService(db, user_id)
    papers = await svc.evaluate_smart_collection(collection_id, limit=limit)

    result = []
    for p in papers:
        status = await rs_svc.get_status(str(p.id))
        result.append(
            {
                "id": str(p.id),
                "title": p.title,
                "doi": p.doi,
                "arxiv_id": p.arxiv_id,
                "published_at": p.published_at,
                "reading_status": status,
            }
        )
    return result


# ─── Export ──────────────────────────────────────────────────────


@router.post("/{collection_id}/export")
async def export_collection_citations(
    collection_id: str,
    body: ExportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Export citations for papers in a collection."""
    svc = CollectionService(db, user_id)
    collection = await svc.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if body.paper_ids:
        paper_ids = [str(pid) for pid in body.paper_ids]
    else:
        papers = await svc.get_collection_papers(collection_id, limit=500)
        paper_ids = [str(p["paper_id"]) for p in papers]

    export_svc = ExportService(db)
    content = await export_svc.export_papers(paper_ids, format=body.format)

    # Return as downloadable text
    content_types = {
        "bibtex": "application/x-bibtex",
        "ris": "application/x-research-info-systems",
        "csl_json": "application/json",
    }
    extensions = {"bibtex": "bib", "ris": "ris", "csl_json": "json"}

    from fastapi.responses import Response

    return Response(
        content=content,
        media_type=content_types.get(body.format, "text/plain"),
        headers={
            "Content-Disposition": f'attachment; filename="{collection.name}.{extensions.get(body.format, "txt")}"'
        },
    )
