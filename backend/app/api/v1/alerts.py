"""Monitoring & Alerts API — rules, notifications, digests.

P2 WS-4: §23 (#201-212) from FeasibilityAnalysis.md
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user_id
from app.services.monitoring.alert_service import AlertService, DigestService

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ─── Schemas ─────────────────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    name: str
    rule_type: str = Field(
        ..., description="new_paper, citation_milestone, author_update, keyword_match"
    )
    condition: dict = Field(
        ..., description='e.g. {"keywords": ["transformer"], "venue_ids": [...]}'
    )
    actions: list[str] = Field(
        default=["in_app"], description='["in_app", "email", "webhook"]'
    )


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    condition: dict | None = None
    actions: list[str] | None = None
    is_active: bool | None = None


# ─── Alert Rules ─────────────────────────────────────────────────

@router.post("/rules", status_code=201)
async def create_alert_rule(
    body: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new alert rule that triggers on matching events."""
    svc = AlertService(db, user_id)
    rule = await svc.create_rule(
        name=body.name,
        rule_type=body.rule_type,
        condition=body.condition,
        actions=body.actions,
    )
    return {
        "id": str(rule.id),
        "name": rule.name,
        "rule_type": rule.rule_type,
        "condition": rule.condition,
        "actions": rule.actions,
        "is_active": rule.is_active,
    }


@router.get("/rules")
async def list_alert_rules(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all alert rules for the current user."""
    svc = AlertService(db, user_id)
    rules = await svc.list_rules()
    return {
        "rules": [
            {
                "id": str(r.id),
                "name": r.name,
                "rule_type": r.rule_type,
                "condition": r.condition,
                "actions": r.actions,
                "is_active": r.is_active,
                "trigger_count": r.trigger_count,
                "last_triggered_at": str(r.last_triggered_at) if r.last_triggered_at else None,
            }
            for r in rules
        ]
    }


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    body: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an alert rule."""
    svc = AlertService(db, user_id)
    rule = await svc.update_rule(rule_id, **body.model_dump(exclude_none=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {
        "id": str(rule.id),
        "name": rule.name,
        "rule_type": rule.rule_type,
        "is_active": rule.is_active,
    }


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete an alert rule."""
    svc = AlertService(db, user_id)
    if not await svc.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")


# ─── Notifications ───────────────────────────────────────────────

@router.get("")
async def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List alerts/notifications for the current user."""
    svc = AlertService(db, user_id)
    alerts = await svc.list_alerts(limit=limit, unread_only=unread_only)
    unread_count = await svc.get_unread_count()
    return {"alerts": alerts, "unread_count": unread_count}


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mark a single alert as read."""
    svc = AlertService(db, user_id)
    if not await svc.mark_read(alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "read"}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Mark all alerts as read."""
    svc = AlertService(db, user_id)
    count = await svc.mark_all_read()
    return {"marked_read": count}


# ─── Digests ─────────────────────────────────────────────────────

@router.get("/digests")
async def list_digests(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List recent digest summaries."""
    svc = DigestService(db, user_id)
    return {"digests": await svc.list_digests(limit=limit)}


@router.post("/digests/preview")
async def preview_digest(
    period: str = Query("weekly", description="daily or weekly"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Preview the next digest (dry run).

    Generates a digest of papers since the last one without saving.
    """
    svc = DigestService(db, user_id)
    return await svc.generate_digest(period=period)
