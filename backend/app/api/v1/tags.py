"""Tags API — CRUD and paper-tag association management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.schemas.collection import TagCreate, TagResponse, TagUpdate
from app.services.collection_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new tag."""
    svc = TagService(db, user_id)
    try:
        tag = await svc.create_tag(
            name=body.name,
            color=body.color,
            description=body.description,
        )
        return TagResponse(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            description=tag.description,
            paper_count=0,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Tag name already exists")


@router.get("", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all tags with paper counts for the current user."""
    svc = TagService(db, user_id)
    return await svc.list_tags()


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a single tag."""
    svc = TagService(db, user_id)
    tag = await svc.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        description=tag.description,
        paper_count=0,
    )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    body: TagUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a tag."""
    svc = TagService(db, user_id)
    tag = await svc.update_tag(tag_id, **body.model_dump(exclude_none=True))
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        description=tag.description,
        paper_count=0,
    )


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a tag."""
    svc = TagService(db, user_id)
    if not await svc.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
