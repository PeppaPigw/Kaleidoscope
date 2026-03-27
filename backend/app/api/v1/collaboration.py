"""Collaboration API — comments, tasks, screening (§8)."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.collection import DEFAULT_USER_ID

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# ─── Schemas ─────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    paper_id: str
    content: str
    parent_id: str | None = None
    anchor_type: str | None = None
    anchor_ref: str | None = None


class TaskCreate(BaseModel):
    paper_id: str
    task_type: str = "review"
    priority: int = 0
    notes: str | None = None


class TaskComplete(BaseModel):
    decision: str
    notes: str | None = None


class ScreeningCreate(BaseModel):
    paper_id: str
    stage: str  # title_abstract | full_text
    decision: str  # include | exclude | maybe
    reason: str | None = None
    criteria_met: dict | None = None


# ─── Comment endpoints ───────────────────────────────────────────

@router.post("/comments")
async def add_comment(body: CommentCreate, db: AsyncSession = Depends(get_db)):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    result = await svc.add_comment(
        paper_id=body.paper_id,
        content=body.content,
        parent_id=body.parent_id,
        anchor_type=body.anchor_type,
        anchor_ref=body.anchor_ref,
    )
    await db.commit()
    return result


@router.get("/comments/{paper_id}")
async def list_comments(
    paper_id: str,
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    return await svc.list_comments(paper_id, limit=limit)


# ─── Task endpoints ──────────────────────────────────────────────

@router.post("/tasks")
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    result = await svc.create_task(
        paper_id=body.paper_id,
        task_type=body.task_type,
        priority=body.priority,
        notes=body.notes,
    )
    await db.commit()
    return result


@router.get("/tasks")
async def list_tasks(
    status: str | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    return await svc.list_tasks(status=status, limit=limit)


@router.patch("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str, body: TaskComplete, db: AsyncSession = Depends(get_db)
):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    result = await svc.complete_task(task_id, body.decision, body.notes)
    if result:
        await db.commit()
    return result or {"error": "Task not found"}


# ─── Screening endpoints ─────────────────────────────────────────

@router.post("/screening")
async def record_screening(
    body: ScreeningCreate, db: AsyncSession = Depends(get_db)
):
    from app.services.collaboration_service import CollaborationService
    svc = CollaborationService(db, user_id=DEFAULT_USER_ID)
    result = await svc.record_screening(
        paper_id=body.paper_id,
        stage=body.stage,
        decision=body.decision,
        reason=body.reason,
        criteria_met=body.criteria_met,
    )
    await db.commit()
    return result
