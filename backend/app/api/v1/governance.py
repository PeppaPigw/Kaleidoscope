"""Governance API — saved searches, audit trails, webhooks, and curation."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.governance_service import GovernanceService

router = APIRouter(prefix="/governance", tags=["governance"])


class SavedSearchCreateRequest(BaseModel):
    name: str
    query: str
    filters: dict = Field(default_factory=dict)
    collection_id: str | None = None


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str]


class CorrectionCreateRequest(BaseModel):
    field_name: str
    original_value: str
    corrected_value: str
    note: str | None = None


class ReproductionCreateRequest(BaseModel):
    status: str
    notes: str
    code_url: str | None = None


@router.post("/searches", status_code=201)
async def create_saved_search(
    body: SavedSearchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a saved search."""
    svc = GovernanceService(db)
    saved_search = await svc.create_saved_search(
        name=body.name,
        query=body.query,
        filters=body.filters,
        collection_id=body.collection_id,
    )
    return saved_search


@router.get("/searches")
async def list_saved_searches(
    db: AsyncSession = Depends(get_db),
):
    """List saved searches."""
    svc = GovernanceService(db)
    return await svc.list_saved_searches()


@router.delete("/searches/{search_id}", status_code=204)
async def delete_saved_search(
    search_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved search."""
    svc = GovernanceService(db)
    deleted = await svc.delete_saved_search(str(search_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved search not found")


@router.get("/audit")
async def list_audit_log(
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List audit log entries."""
    svc = GovernanceService(db)
    return await svc.list_audit_log(limit=limit, offset=offset, entity_type=entity_type)


@router.post("/webhooks", status_code=201)
async def create_webhook(
    body: WebhookCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a webhook."""
    svc = GovernanceService(db)
    webhook = await svc.create_webhook(url=body.url, events=body.events)
    return webhook


@router.get("/webhooks")
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
):
    """List webhooks."""
    svc = GovernanceService(db)
    return await svc.list_webhooks()


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook."""
    svc = GovernanceService(db)
    deleted = await svc.delete_webhook(str(webhook_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/papers/{paper_id}/corrections", status_code=201)
async def submit_correction(
    paper_id: UUID,
    body: CorrectionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a correction for paper metadata."""
    svc = GovernanceService(db)
    correction = await svc.submit_correction(
        paper_id=str(paper_id),
        field_name=body.field_name,
        original_value=body.original_value,
        corrected_value=body.corrected_value,
        note=body.note,
    )
    return correction


@router.get("/papers/{paper_id}/corrections")
async def get_paper_corrections(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List corrections submitted for a paper."""
    svc = GovernanceService(db)
    return await svc.get_paper_corrections(str(paper_id))


@router.post("/papers/{paper_id}/reproductions", status_code=201)
async def log_reproduction(
    paper_id: UUID,
    body: ReproductionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Log a reproduction attempt for a paper."""
    svc = GovernanceService(db)
    reproduction = await svc.log_reproduction(
        paper_id=str(paper_id),
        status=body.status,
        notes=body.notes,
        code_url=body.code_url,
    )
    return reproduction


@router.get("/papers/{paper_id}/reproductions")
async def get_reproductions(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List reproduction attempts for a paper."""
    svc = GovernanceService(db)
    return await svc.get_reproductions(str(paper_id))
