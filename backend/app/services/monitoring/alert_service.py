"""Alert and monitoring service — rules, notifications, digests.

P2 WS-4: §23 (#201-212) from FeasibilityAnalysis.md

Provides:
- Alert rule CRUD (create/update/delete conditions)
- Alert evaluation (match new papers against rules)
- In-app notification management
- Weekly/daily digest generation
"""

from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertRule, Digest
from app.models.paper import Paper

logger = structlog.get_logger(__name__)

PREFERENCE_RULE_MANAGER = "user_preferences"


def _dedupe_strings(values: list[str] | None) -> list[str]:
    """Normalize free-form string lists while preserving first occurrence."""
    if not values:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)
    return normalized


class AlertService:
    """Manage alert rules and notifications."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    # ─── Alert Rule CRUD ─────────────────────────────────────────

    async def create_rule(
        self,
        name: str,
        rule_type: str,
        condition: dict,
        actions: list[str] | None = None,
    ) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            user_id=self.user_id,
            name=name,
            rule_type=rule_type,
            condition=condition,
            actions=actions or ["in_app"],
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def sync_preference_rules(
        self,
        *,
        keywords: list[str] | None = None,
        tracked_authors: list[str] | None = None,
    ) -> list[AlertRule]:
        """Reconcile settings-managed rules with the latest user preferences."""
        desired_specs = {
            "keywords": {
                "name": "Subscription keywords",
                "rule_type": "keyword_match",
                "condition": {
                    "managed_by": PREFERENCE_RULE_MANAGER,
                    "preference_type": "keywords",
                    "keywords": _dedupe_strings(keywords),
                },
            },
            "tracked_authors": {
                "name": "Tracked authors",
                "rule_type": "author_update",
                "condition": {
                    "managed_by": PREFERENCE_RULE_MANAGER,
                    "preference_type": "tracked_authors",
                    "author_names": _dedupe_strings(tracked_authors),
                },
            },
        }

        result = await self.db.execute(
            select(AlertRule)
            .where(AlertRule.user_id == self.user_id)
            .order_by(AlertRule.created_at.asc())
        )

        managed_rules: dict[str, AlertRule] = {}
        duplicates_to_remove: list[AlertRule] = []

        for rule in result.scalars().all():
            condition = rule.condition or {}
            if condition.get("managed_by") != PREFERENCE_RULE_MANAGER:
                continue
            preference_type = condition.get("preference_type")
            if preference_type not in desired_specs:
                duplicates_to_remove.append(rule)
                continue
            if preference_type in managed_rules:
                duplicates_to_remove.append(rule)
                continue
            managed_rules[str(preference_type)] = rule

        synced_rules: list[AlertRule] = []
        for preference_type, spec in desired_specs.items():
            condition = spec["condition"]
            values = (
                condition.get("keywords")
                if preference_type == "keywords"
                else condition.get("author_names")
            )
            rule = managed_rules.pop(preference_type, None)

            if not values:
                if rule is not None:
                    duplicates_to_remove.append(rule)
                continue

            if rule is None:
                rule = AlertRule(
                    user_id=self.user_id,
                    name=str(spec["name"]),
                    rule_type=str(spec["rule_type"]),
                    condition=condition,
                    actions=["in_app"],
                    is_active=True,
                )
                self.db.add(rule)
            else:
                rule.name = str(spec["name"])
                rule.rule_type = str(spec["rule_type"])
                rule.condition = condition
                rule.actions = ["in_app"]
                rule.is_active = True

            synced_rules.append(rule)

        duplicates_to_remove.extend(managed_rules.values())
        for rule in duplicates_to_remove:
            await self.db.delete(rule)

        await self.db.flush()
        return synced_rules

    async def list_rules(self) -> list[AlertRule]:
        """List all rules for this user."""
        result = await self.db.execute(
            select(AlertRule)
            .where(AlertRule.user_id == self.user_id)
            .order_by(AlertRule.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_rule(self, rule_id: str, **kwargs) -> AlertRule | None:
        """Update a rule's fields."""
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.id == rule_id,
                AlertRule.user_id == self.user_id,
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return None
        for k, v in kwargs.items():
            if hasattr(rule, k):
                setattr(rule, k, v)
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        result = await self.db.execute(
            select(AlertRule).where(
                AlertRule.id == rule_id,
                AlertRule.user_id == self.user_id,
            )
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        await self.db.delete(rule)
        return True

    # ─── Alerts ──────────────────────────────────────────────────

    async def list_alerts(
        self, limit: int = 50, unread_only: bool = False
    ) -> list[dict]:
        """List alerts for this user."""
        query = (
            select(Alert)
            .where(Alert.user_id == self.user_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(Alert.is_read == False)

        result = await self.db.execute(query)
        return [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "title": a.title,
                "message": a.body,
                "body": a.body,
                "is_read": a.is_read,
                "paper_id": str(a.paper_id) if a.paper_id else None,
                "created_at": str(a.created_at),
            }
            for a in result.scalars().all()
        ]

    async def mark_read(self, alert_id: str) -> bool:
        """Mark an alert as read."""
        result = await self.db.execute(
            update(Alert)
            .where(Alert.id == alert_id, Alert.user_id == self.user_id)
            .values(is_read=True)
        )
        return result.rowcount > 0

    async def mark_all_read(self) -> int:
        """Mark all alerts as read."""
        result = await self.db.execute(
            update(Alert)
            .where(Alert.user_id == self.user_id, Alert.is_read == False)
            .values(is_read=True)
        )
        return result.rowcount

    async def get_unread_count(self) -> int:
        """Get count of unread alerts."""
        result = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.user_id == self.user_id,
                Alert.is_read == False,
            )
        )
        return result.scalar() or 0

    # ─── Rule Evaluation ─────────────────────────────────────────

    async def evaluate_rules(self, paper: Paper) -> list[Alert]:
        """
        Evaluate all active rules against a newly ingested paper.

        Called by the ingestion pipeline after a paper is indexed.
        Creates Alert objects for matching rules.
        """
        rules = await self.db.execute(
            select(AlertRule).where(
                AlertRule.user_id == self.user_id,
                AlertRule.is_active == True,
            )
        )
        alerts_created = []

        for rule in rules.scalars().all():
            if self._matches_rule(rule, paper):
                alert = Alert(
                    user_id=self.user_id,
                    rule_id=str(rule.id),
                    alert_type=rule.rule_type,
                    title=f"[{rule.name}] {paper.title[:200]}",
                    body=f"New paper matches your alert rule '{rule.name}': {paper.title}",
                    paper_id=str(paper.id),
                )
                self.db.add(alert)
                rule.last_triggered_at = datetime.utcnow()
                rule.trigger_count += 1
                alerts_created.append(alert)

        return alerts_created

    @staticmethod
    def _matches_rule(rule: AlertRule, paper: Paper) -> bool:
        """Check if a paper matches a rule's condition."""
        cond: dict[str, Any] = rule.condition or {}
        if not cond:
            return False

        # Keyword match
        if "keywords" in cond:
            paper_text = ((paper.title or "") + " " + (paper.abstract or "")).lower()
            if not any(kw.lower() in paper_text for kw in cond["keywords"]):
                return False

        # Author match
        if "author_names" in cond:
            # Simplified: check if any author name appears in raw_metadata
            if paper.raw_metadata:
                authors_str = str(paper.raw_metadata.get("authors", "")).lower()
                if not any(
                    name.lower() in authors_str for name in cond["author_names"]
                ):
                    return False

        # Venue match
        if "venue_ids" in cond and paper.venue_id:
            if str(paper.venue_id) not in cond["venue_ids"]:
                return False

        # Citation threshold (for citation_milestone type)
        if "min_citations" in cond:
            if (paper.citation_count or 0) < cond["min_citations"]:
                return False

        return True


class DigestService:
    """Generate periodic digest summaries."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def generate_digest(
        self,
        period: str = "weekly",
        *,
        save: bool = True,
        use_llm: bool = True,
    ) -> dict:
        """
        Generate a digest of recent papers.

        Finds papers ingested since last digest, summarizes via LLM.
        """
        log = logger.bind(user_id=self.user_id, period=period)

        # Find last digest for this user + period
        last_digest = await self.db.execute(
            select(Digest)
            .where(Digest.user_id == self.user_id, Digest.period == period)
            .order_by(Digest.generated_at.desc())
            .limit(1)
        )
        last = last_digest.scalar_one_or_none()
        since = last.generated_at if last else datetime.utcnow() - timedelta(days=7)

        # Get new papers since then
        papers_result = await self.db.execute(
            select(Paper)
            .where(
                Paper.deleted_at.is_(None),
                Paper.created_at >= since,
            )
            .order_by(Paper.citation_count.desc().nullslast())
            .limit(50)
        )
        papers = papers_result.scalars().all()

        if not papers:
            return {
                "period": period,
                "paper_count": 0,
                "content": "No new papers since last digest.",
            }

        paper_list = "\n".join(
            f"- {p.title} (citations: {p.citation_count or 0})" for p in papers[:20]
        )
        fallback_content = f"## New Papers ({len(papers)} total)\n\n{paper_list}"

        content = fallback_content
        if use_llm:
            try:
                from app.clients.llm_client import LLMClient

                llm = LLMClient()
                prompt = (
                    f"Summarize these {len(papers)} new research papers for a weekly digest. "
                    f"Group by theme, highlight the most impactful ones, and note any trends.\n\n"
                    f"{paper_list}"
                )
                content = await llm.complete(prompt=prompt, temperature=0.3)
                await llm.close()
            except Exception as e:
                log.error("digest_llm_failed", error=str(e))
                content = fallback_content

        if save:
            digest = Digest(
                user_id=self.user_id,
                period=period,
                content=content,
                paper_ids=[str(p.id) for p in papers],
                paper_count=len(papers),
            )
            self.db.add(digest)

        return {
            "period": period,
            "paper_count": len(papers),
            "content": content,
            "paper_ids": [str(p.id) for p in papers],
        }

    async def list_digests(self, limit: int = 10) -> list[dict]:
        """List recent digests."""
        result = await self.db.execute(
            select(Digest)
            .where(Digest.user_id == self.user_id)
            .order_by(Digest.generated_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(d.id),
                "period": d.period,
                "paper_count": d.paper_count,
                "generated_at": str(d.generated_at),
                "content_preview": (d.content or "")[:200],
            }
            for d in result.scalars().all()
        ]
