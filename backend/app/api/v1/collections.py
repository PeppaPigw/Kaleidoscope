"""Collections API — CRUD, paper management, smart collections."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id
from app.schemas.collection import (
    CollectionCreate,
    CollectionDetailResponse,
    CollectionPaperAdd,
    CollectionPaperReorder,
    CollectionPaperResponse,
    CollectionResponse,
    CollectionUpdate,
    ExportRequest,
    ReadingStatusUpdate,
    TagCreate,
    TagResponse,
    TagUpdate,
)
from app.services.collection_service import CollectionService, ReadingStatusService
from app.services.export_service import ExportService

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
        color=body.color,
        icon=body.icon,
        is_smart=body.is_smart,
        smart_filter=body.smart_filter,
    )
    return collection


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all collections for the current user."""
    svc = CollectionService(db, user_id)
    return await svc.list_collections()


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
        collection_id, [str(pid) for pid in body.paper_ids], note=body.note,
    )
    return {"added": added, "total": collection.paper_count + added}


@router.delete("/{collection_id}/papers/{paper_id}", status_code=204)
async def remove_paper_from_collection(
    collection_id: str, paper_id: str,
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
        result.append({
            "id": str(p.id),
            "title": p.title,
            "doi": p.doi,
            "arxiv_id": p.arxiv_id,
            "published_at": p.published_at,
            "reading_status": status,
        })
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
