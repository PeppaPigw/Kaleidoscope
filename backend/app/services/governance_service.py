"""Governance service — saved searches, audit trails, webhooks, and curation."""

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import DEFAULT_USER_ID
from app.models.governance import (
    AuditLog,
    ReproductionAttempt,
    SavedSearch,
    UserCorrection,
    Webhook,
)

logger = structlog.get_logger(__name__)


class GovernanceService:
    """Business logic for governance and curation workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_saved_search(
        self,
        name: str,
        query: str,
        filters: dict,
        collection_id: str | None = None,
    ) -> dict:
        """Create a persisted saved search."""
        saved_search = SavedSearch(
            user_id=DEFAULT_USER_ID,
            name=name,
            query=query,
            filters=filters,
            collection_id=collection_id,
        )
        self.db.add(saved_search)
        await self.db.flush()
        await self.log_audit("create", "saved_search", str(saved_search.id))
        return self._serialize_saved_search(saved_search)

    async def list_saved_searches(self) -> list[dict]:
        """List saved searches for the sentinel user."""
        result = await self.db.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == DEFAULT_USER_ID)
            .order_by(SavedSearch.created_at.desc())
        )
        return [self._serialize_saved_search(s) for s in result.scalars().all()]

    async def delete_saved_search(self, search_id: str) -> bool:
        """Delete a saved search."""
        result = await self.db.execute(
            delete(SavedSearch).where(
                SavedSearch.id == search_id,
                SavedSearch.user_id == DEFAULT_USER_ID,
            )
        )
        if result.rowcount > 0:
            await self.log_audit("delete", "saved_search", search_id)
        return result.rowcount > 0

    async def log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        diff: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Insert an audit log entry."""
        entry = AuditLog(
            user_id=DEFAULT_USER_ID,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            diff=diff,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()
        logger.info(
            "audit_logged", action=action, entity_type=entity_type, entity_id=entity_id
        )

    async def list_audit_log(
        self,
        limit: int = 50,
        offset: int = 0,
        entity_type: str | None = None,
    ) -> list[dict]:
        """List audit events, newest first."""
        query = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        result = await self.db.execute(query)
        return [self._serialize_audit_log(e) for e in result.scalars().all()]

    async def create_webhook(self, url: str, events: list[str]) -> dict:
        """Create an active webhook endpoint."""
        webhook = Webhook(
            user_id=DEFAULT_USER_ID, url=url, events=events, is_active=True
        )
        self.db.add(webhook)
        await self.db.flush()
        await self.log_audit("create", "webhook", str(webhook.id))
        return self._serialize_webhook(webhook)

    async def list_webhooks(self) -> list[dict]:
        """List active webhooks."""
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.user_id == DEFAULT_USER_ID, Webhook.is_active.is_(True))
            .order_by(Webhook.created_at.desc())
        )
        return [self._serialize_webhook(w) for w in result.scalars().all()]

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        result = await self.db.execute(
            delete(Webhook).where(
                Webhook.id == webhook_id, Webhook.user_id == DEFAULT_USER_ID
            )
        )
        return result.rowcount > 0

    async def fire_webhooks(self, event_type: str, payload: dict) -> int:
        """
        Dispatch event to all active webhooks subscribed to this event type.

        Returns the number of successfully notified webhooks.
        """
        import httpx
        from datetime import datetime

        hooks = await self.db.execute(
            select(Webhook).where(
                Webhook.user_id == DEFAULT_USER_ID,
                Webhook.is_active.is_(True),
            )
        )
        notified = 0
        for hook in hooks.scalars().all():
            events = hook.events or []
            if event_type not in events and "*" not in events:
                continue
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        hook.url,
                        json={"event": event_type, "data": payload},
                    )
                    if resp.status_code < 300:  # 2xx only; treat 3xx as failure
                        notified += 1
                        hook.last_triggered_at = datetime.utcnow()
                    else:
                        logger.warning(
                            "webhook_failed",
                            url=hook.url,
                            status=resp.status_code,
                        )
            except Exception as e:
                logger.warning("webhook_error", url=hook.url, error=str(e))
        return notified

    async def submit_correction(
        self,
        paper_id: str,
        field_name: str,
        original_value: object,
        corrected_value: object,
        note: str | None = None,
    ) -> dict:
        """Create a user correction proposal."""
        correction = UserCorrection(
            paper_id=paper_id,
            user_id=DEFAULT_USER_ID,
            field_name=field_name,
            original_value=original_value,
            corrected_value=corrected_value,
            note=note,
            status="pending",
        )
        self.db.add(correction)
        await self.db.flush()
        await self.log_audit(
            "create",
            "user_correction",
            str(correction.id),
            diff={"field": field_name, "paper_id": paper_id},
        )
        return {
            "id": str(correction.id),
            "paper_id": str(correction.paper_id),
            "field_name": correction.field_name,
            "status": correction.status,
            "created_at": str(correction.created_at),
        }

    async def get_paper_corrections(self, paper_id: str) -> list[dict]:
        """List all correction submissions for a paper."""
        result = await self.db.execute(
            select(UserCorrection)
            .where(UserCorrection.paper_id == paper_id)
            .order_by(UserCorrection.created_at.desc())
        )
        return [
            {
                "id": str(c.id),
                "paper_id": str(c.paper_id),
                "field_name": c.field_name,
                "original_value": c.original_value,
                "corrected_value": c.corrected_value,
                "note": c.note,
                "status": c.status,
                "created_at": str(c.created_at),
            }
            for c in result.scalars().all()
        ]

    async def log_reproduction(
        self,
        paper_id: str,
        status: str,
        notes: str,
        code_url: str | None = None,
    ) -> dict:
        """Record a reproduction attempt for a paper."""
        attempt = ReproductionAttempt(
            paper_id=paper_id,
            user_id=DEFAULT_USER_ID,
            status=status,
            notes=notes,
            code_url=code_url,
        )
        self.db.add(attempt)
        await self.db.flush()
        await self.log_audit(
            "create",
            "reproduction",
            str(attempt.id),
            diff={"paper_id": paper_id, "status": status},
        )
        return self._serialize_reproduction(attempt)

    async def get_reproductions(self, paper_id: str) -> list[dict]:
        """List reproduction attempts for a paper."""
        result = await self.db.execute(
            select(ReproductionAttempt)
            .where(ReproductionAttempt.paper_id == paper_id)
            .order_by(ReproductionAttempt.created_at.desc())
        )
        return [self._serialize_reproduction(a) for a in result.scalars().all()]

    @staticmethod
    def _serialize_saved_search(s: SavedSearch) -> dict:
        return {
            "id": str(s.id),
            "name": s.name,
            "query": s.query,
            "filters": s.filters,
            "collection_id": str(s.collection_id) if s.collection_id else None,
            "created_at": str(s.created_at),
        }

    @staticmethod
    def _serialize_audit_log(e: AuditLog) -> dict:
        return {
            "id": str(e.id),
            "user_id": str(e.user_id),
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "diff": e.diff,
            "ip_address": e.ip_address,
            "created_at": str(e.created_at),
        }

    @staticmethod
    def _serialize_webhook(w: Webhook) -> dict:
        return {
            "id": str(w.id),
            "url": w.url,
            "events": w.events,
            "is_active": w.is_active,
            "created_at": str(w.created_at),
        }

    @staticmethod
    def _serialize_reproduction(a: ReproductionAttempt) -> dict:
        return {
            "id": str(a.id),
            "paper_id": str(a.paper_id),
            "status": a.status,
            "notes": a.notes,
            "code_url": a.code_url,
            "created_at": str(a.created_at),
        }
