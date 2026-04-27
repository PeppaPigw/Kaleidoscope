"""Unit tests for governance and quality services."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

if "structlog" not in sys.modules:
    _logger = SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        bind=lambda *args, **kwargs: None,
    )
    sys.modules["structlog"] = SimpleNamespace(
        get_logger=lambda *args, **kwargs: _logger
    )


class FakeScalarResult:
    """Mimics SQLAlchemy scalar result helpers used in services."""

    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return self


class FakeRowResult:
    """Mimics SQLAlchemy row result for DELETE/UPDATE statements."""

    def __init__(self, rowcount: int):
        self.rowcount = rowcount


def make_db(execute_results: list[object], flush_templates: list[object]):
    """Create a lightweight async-session double."""
    db = SimpleNamespace()
    db._last_added = None
    db._flush_templates = list(flush_templates)

    def add(obj):
        db._last_added = obj

    async def flush():
        if db._last_added is None or not db._flush_templates:
            return
        template = db._flush_templates.pop(0)
        for key, value in vars(template).items():
            setattr(db._last_added, key, value)

    db.add = MagicMock(side_effect=add)
    db.flush = AsyncMock(side_effect=flush)
    db.execute = AsyncMock(side_effect=execute_results)
    return db


def test_governance_service_saved_search_and_webhook_flows():
    """GovernanceService creates, lists, and deletes saved searches/webhooks."""
    from app.services.governance_service import GovernanceService

    created_at = datetime(2026, 3, 27, 12, 0, tzinfo=UTC)
    saved_search = SimpleNamespace(
        id=uuid4(),
        name="Recent AI",
        query="transformer interpretability",
        filters={"year_gte": 2024},
        collection_id=None,
        created_at=created_at,
    )
    webhook = SimpleNamespace(
        id=uuid4(),
        url="https://example.com/hooks",
        events=["paper.updated"],
        is_active=True,
        created_at=created_at,
    )

    db = make_db(
        execute_results=[
            FakeScalarResult([saved_search]),
            FakeRowResult(1),
            FakeScalarResult([webhook]),
            FakeRowResult(1),
        ],
        flush_templates=[
            saved_search,
            SimpleNamespace(),
            SimpleNamespace(),
            webhook,
        ],
    )

    service = GovernanceService(db)

    async def run_test():
        create_result = await service.create_saved_search(
            name="Recent AI",
            query="transformer interpretability",
            filters={"year_gte": 2024},
        )
        assert create_result == {
            "id": str(saved_search.id),
            "name": "Recent AI",
            "query": "transformer interpretability",
            "filters": {"year_gte": 2024},
            "collection_id": None,
            "created_at": str(created_at),
        }
        db.add.assert_called()
        db.flush.assert_awaited()

        list_result = await service.list_saved_searches()
        assert list_result == [create_result]

        assert await service.delete_saved_search(str(saved_search.id)) is True

        webhook_result = await service.create_webhook(
            url="https://example.com/hooks",
            events=["paper.updated"],
        )
        assert webhook_result == {
            "id": str(webhook.id),
            "url": "https://example.com/hooks",
            "events": ["paper.updated"],
            "is_active": True,
            "created_at": str(created_at),
        }

        listed_webhooks = await service.list_webhooks()
        assert listed_webhooks == [webhook_result]

        assert await service.delete_webhook(str(webhook.id)) is True

    asyncio.run(run_test())


def test_governance_service_audit_corrections_and_reproductions():
    """GovernanceService serializes audit, correction, and reproduction rows."""
    from app.services.governance_service import GovernanceService

    created_at = datetime(2026, 3, 27, 13, 0, tzinfo=UTC)
    audit = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        action="update",
        entity_type="paper",
        entity_id="paper-1",
        diff={"title": ["old", "new"]},
        ip_address="127.0.0.1",
        created_at=created_at,
    )
    correction = SimpleNamespace(
        id=uuid4(),
        paper_id=uuid4(),
        field_name="title",
        status="pending",
        note="Typo fix",
        original_value="Orig",
        corrected_value="Corrected",
        created_at=created_at,
    )
    reproduction = SimpleNamespace(
        id=uuid4(),
        paper_id=uuid4(),
        status="confirmed",
        notes="Reproduced locally",
        code_url="https://github.com/example/repro",
        created_at=created_at,
    )

    db = make_db(
        execute_results=[
            FakeScalarResult([audit]),
            FakeScalarResult([correction]),
            FakeScalarResult([reproduction]),
        ],
        flush_templates=[
            audit,
            correction,
            SimpleNamespace(),
            reproduction,
            SimpleNamespace(),
        ],
    )

    service = GovernanceService(db)

    async def run_test():
        await service.log_audit(
            action="update",
            entity_type="paper",
            entity_id="paper-1",
            diff={"title": ["old", "new"]},
            ip_address="127.0.0.1",
        )
        db.add.assert_called()
        db.flush.assert_awaited()

        listed_audit = await service.list_audit_log(
            limit=10,
            offset=5,
            entity_type="paper",
        )
        assert listed_audit == [
            {
                "id": str(audit.id),
                "user_id": str(audit.user_id),
                "action": "update",
                "entity_type": "paper",
                "entity_id": "paper-1",
                "diff": {"title": ["old", "new"]},
                "ip_address": "127.0.0.1",
                "created_at": str(created_at),
            }
        ]

        created_correction = await service.submit_correction(
            paper_id=str(correction.paper_id),
            field_name="title",
            original_value="Orig",
            corrected_value="Corrected",
            note="Typo fix",
        )
        assert created_correction == {
            "id": str(correction.id),
            "paper_id": str(correction.paper_id),
            "field_name": "title",
            "status": "pending",
            "created_at": str(created_at),
        }

        corrections = await service.get_paper_corrections(str(correction.paper_id))
        assert corrections == [
            {
                "id": str(correction.id),
                "paper_id": str(correction.paper_id),
                "field_name": "title",
                "original_value": "Orig",
                "corrected_value": "Corrected",
                "note": "Typo fix",
                "status": "pending",
                "created_at": str(created_at),
            }
        ]

        created_reproduction = await service.log_reproduction(
            paper_id=str(reproduction.paper_id),
            status="confirmed",
            notes="Reproduced locally",
            code_url="https://github.com/example/repro",
        )
        assert created_reproduction == {
            "id": str(reproduction.id),
            "paper_id": str(reproduction.paper_id),
            "status": "confirmed",
            "notes": "Reproduced locally",
            "code_url": "https://github.com/example/repro",
            "created_at": str(created_at),
        }

        reproductions = await service.get_reproductions(str(reproduction.paper_id))
        assert reproductions == [created_reproduction]

    asyncio.run(run_test())


def test_quality_service_reports_metadata_and_reproducibility():
    """QualityService aggregates metadata completeness and reproducibility signals."""
    from app.services.quality_service import QualityService

    paper_id = str(uuid4())
    paper = SimpleNamespace(
        id=paper_id,
        title="Reproducible Science",
        abstract="A concise abstract.",
        doi="10.1000/example",
        arxiv_id="2401.12345",
        published_at=date(2026, 1, 15),
        keywords=["ml", "science"],
        citation_count=42,
        venue_id=uuid4(),
        summary="Summary text",
        highlights=["Signal one"],
        contributions=["Contribution one"],
        limitations=["Limitation one"],
        has_full_text=True,
        markdown_provenance={"source": "mineru"},
        source_type="local_upload",
        raw_metadata={
            "links": ["https://github.com/example/project"],
            "statement": "Code available and open source.",
        },
        grobid_tei="This manuscript is reproducible and archived on Zenodo.",
        full_text_markdown="Supplementary implementation details.",
    )
    corrections = [
        SimpleNamespace(
            id=uuid4(),
            paper_id=paper_id,
            field_name="title",
            original_value="Old title",
            corrected_value="Reproducible Science",
            note="Fixed typo",
            status="approved",
            created_at=datetime(2026, 3, 26, 9, 0, tzinfo=UTC),
        )
    ]

    db = make_db(
        execute_results=[
            FakeScalarResult([paper]),
            FakeScalarResult([paper]),
            FakeScalarResult([paper]),
            FakeScalarResult([paper]),
            FakeScalarResult(corrections),
        ],
        flush_templates=[],
    )

    service = QualityService(db)

    async def run_test():
        metadata = await service.get_metadata_score(paper_id)
        assert metadata["paper_id"] == paper_id
        assert metadata["total_fields"] == 12
        assert metadata["filled_fields"] == 12
        assert metadata["score_pct"] == 100
        assert metadata["details"][0] == {
            "field": "title",
            "present": True,
            "value_preview": "Reproducible Science",
        }

        reproducibility = await service.get_reproducibility(paper_id)
        assert reproducibility["paper_id"] == paper_id
        assert reproducibility["has_full_text"] is True
        assert reproducibility["has_code_keyword"] is True
        assert reproducibility["score"] == 5
        assert "has_full_text" in reproducibility["reproducibility_signals"]
        assert "markdown_provenance" in reproducibility["reproducibility_signals"]
        assert "source_type:local_upload" in reproducibility["reproducibility_signals"]

        report = await service.get_quality_report(paper_id)
        assert report["paper_id"] == paper_id
        assert report["metadata_score"]["score_pct"] == 100
        assert report["reproducibility"]["score"] == 5
        assert report["corrections"] == [
            {
                "id": str(corrections[0].id),
                "field_name": "title",
                "original_value": "Old title",
                "corrected_value": "Reproducible Science",
                "note": "Fixed typo",
                "status": "approved",
                "created_at": str(corrections[0].created_at),
            }
        ]

    asyncio.run(run_test())
