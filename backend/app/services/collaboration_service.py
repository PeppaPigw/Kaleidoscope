"""Collaboration service — comments, tasks, screening (§8)."""

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collaboration import (
    PaperComment,
    ReviewTask,
    ScreeningDecision,
)

logger = structlog.get_logger(__name__)


class CollaborationService:
    """Business logic for paper review collaboration."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    # ─── Comments ────────────────────────────────────────────────

    async def add_comment(
        self,
        paper_id: str,
        content: str,
        parent_id: str | None = None,
        anchor_type: str | None = None,
        anchor_ref: str | None = None,
    ) -> dict:
        """Add a threaded comment to a paper."""
        comment = PaperComment(
            paper_id=paper_id,
            user_id=self.user_id,
            parent_id=parent_id,
            content=content,
            anchor_type=anchor_type,
            anchor_ref=anchor_ref,
        )
        self.db.add(comment)
        await self.db.flush()
        return self._ser_comment(comment)

    async def list_comments(self, paper_id: str, limit: int = 100) -> list[dict]:
        """List top-level comments for a paper."""
        result = await self.db.execute(
            select(PaperComment)
            .where(
                PaperComment.paper_id == paper_id,
                PaperComment.parent_id.is_(None),
            )
            .order_by(PaperComment.created_at)
            .limit(limit)
        )
        return [self._ser_comment(c) for c in result.scalars().all()]

    # ─── Review Tasks ────────────────────────────────────────────

    async def create_task(
        self,
        paper_id: str,
        task_type: str = "review",
        priority: int = 0,
        notes: str | None = None,
    ) -> dict:
        """Create a review task assigned to current user."""
        task = ReviewTask(
            paper_id=paper_id,
            assignee_id=self.user_id,
            task_type=task_type,
            priority=priority,
            notes=notes,
        )
        self.db.add(task)
        await self.db.flush()
        return self._ser_task(task)

    async def list_tasks(
        self, status: str | None = None, limit: int = 50
    ) -> list[dict]:
        """List tasks for current user."""
        query = (
            select(ReviewTask)
            .where(ReviewTask.assignee_id == self.user_id)
            .order_by(ReviewTask.priority.desc(), ReviewTask.created_at)
            .limit(limit)
        )
        if status:
            query = query.where(ReviewTask.status == status)
        result = await self.db.execute(query)
        return [self._ser_task(t) for t in result.scalars().all()]

    async def complete_task(
        self, task_id: str, decision: str, notes: str | None = None
    ) -> dict | None:
        """Complete a review task with a decision."""
        result = await self.db.execute(
            select(ReviewTask).where(
                ReviewTask.id == task_id,
                ReviewTask.assignee_id == self.user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        task.status = "done"
        task.decision = decision
        task.notes = notes
        task.completed_at = func.now()
        return self._ser_task(task)

    # ─── Screening ───────────────────────────────────────────────

    async def record_screening(
        self,
        paper_id: str,
        stage: str,
        decision: str,
        reason: str | None = None,
        criteria_met: dict | None = None,
    ) -> dict:
        """Record a screening decision."""
        sd = ScreeningDecision(
            paper_id=paper_id,
            reviewer_id=self.user_id,
            stage=stage,
            decision=decision,
            reason=reason,
            criteria_met=criteria_met,
        )
        self.db.add(sd)
        await self.db.flush()
        return {
            "id": str(sd.id),
            "paper_id": paper_id,
            "stage": stage,
            "decision": decision,
        }

    # ─── Serializers ─────────────────────────────────────────────

    @staticmethod
    def _ser_comment(c: PaperComment) -> dict:
        return {
            "id": str(c.id),
            "paper_id": str(c.paper_id),
            "user_id": str(c.user_id),
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "content": c.content,
            "anchor_type": c.anchor_type,
            "anchor_ref": c.anchor_ref,
            "created_at": str(c.created_at),
        }

    @staticmethod
    def _ser_task(t: ReviewTask) -> dict:
        return {
            "id": str(t.id),
            "paper_id": str(t.paper_id),
            "title": t.task_type,
            "description": t.notes,
            "completed": t.status == "done",
            "task_type": t.task_type,
            "status": t.status,
            "priority": t.priority,
            "decision": t.decision,
            "notes": t.notes,
            "created_at": str(t.created_at),
            "completed_at": str(t.completed_at) if t.completed_at else None,
        }
