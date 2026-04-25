"""Smoke-test agent-facing API routes with safe in-process HTTP requests.

This script is intentionally non-destructive: it overrides the DB dependency with
an empty in-memory async session and validates response status/content shape for
agent-facing routes added from docs/memo/API-todo.md.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from app import dependencies
from app.main import create_app


class EmptyResult:
    """Minimal SQLAlchemy result double for smoke testing empty DB responses."""

    rowcount = 0

    def __init__(self, row: Any = None, rows: list[Any] | None = None):
        self.row = row
        self.rows = rows

    def scalar_one_or_none(self) -> Any:
        return self.row

    def scalars(self) -> EmptyResult:
        return self

    def all(self) -> list[Any]:
        if self.rows is not None:
            return self.rows
        if self.row is None:
            return []
        return [self.row]

    def first(self) -> Any:
        rows = self.all()
        return rows[0] if rows else None

    def scalar(self) -> Any:
        return self.row


class EmptyAsyncSession:
    """Small async-session double sufficient for safe response smoke tests."""

    def __init__(self) -> None:
        self.added: list[Any] = []

    async def execute(self, statement: Any) -> EmptyResult:
        return EmptyResult(rows=[])

    async def scalar(self, statement: Any) -> int:
        return 0

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(tz=UTC)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def delete(self, obj: Any) -> None:
        return None


@dataclass(frozen=True)
class SmokeCase:
    method: str
    path: str
    json_body: dict[str, Any] | None = None
    expected_statuses: tuple[int, ...] = (200, 201, 204, 404, 422)
    expect_stream: bool = False


PID = "00000000-0000-0000-0000-000000000001"
PAPER = f"/api/v1/papers/{PID}"
PAPER_BODY = {"paper_ids": [PID]}
LIT_BODY = {"topic": "retrieval", "limit": 3}
API_KEY_HEADERS = {"X-API-Key": "sk-kaleidoscope"}

SMOKE_CASES: tuple[SmokeCase, ...] = (
    SmokeCase("POST", "/api/v1/evidence/search", {"query": "ImageNet accuracy"}),
    SmokeCase("POST", "/api/v1/evidence/packs", {"query": "ImageNet accuracy"}),
    SmokeCase("POST", "/api/v1/claims/verify", {"claim": "The model improves."}),
    SmokeCase(
        "POST",
        "/api/v1/citations/intent-classify",
        {"context": "We compare against this baseline."},
    ),
    SmokeCase("GET", f"{PAPER}/references"),
    SmokeCase("GET", f"{PAPER}/citations/context"),
    SmokeCase("GET", f"{PAPER}/citation-contexts"),
    SmokeCase(
        "POST",
        "/api/v1/benchmarks/extract",
        {"text": "ImageNet accuracy is 83.4% on A100."},
    ),
    SmokeCase("GET", f"{PAPER}/sections"),
    SmokeCase("GET", f"{PAPER}/assets"),
    SmokeCase("GET", f"{PAPER}/figures"),
    SmokeCase("GET", f"{PAPER}/tables"),
    SmokeCase("GET", f"{PAPER}/code-and-data"),
    SmokeCase("GET", "/api/v1/discovery/delta?since=2026-04-24T00:00:00Z"),
    SmokeCase("POST", "/api/v1/exports/jsonl", {"resources": ["papers"], "limit": 5}),
    SmokeCase("POST", "/api/v1/extract/claims/batch", PAPER_BODY),
    SmokeCase("POST", "/api/v1/extract/experiments/batch", PAPER_BODY),
    SmokeCase("POST", "/api/v1/extract/figures/batch", PAPER_BODY),
    SmokeCase("POST", "/api/v1/quality/batch", PAPER_BODY),
    SmokeCase("GET", "/api/v1/labs/search?q=university"),
    SmokeCase("POST", "/api/v1/literature/review-map", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/related-work-pack", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/contradiction-map", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/minimal-reading-set", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/research-timeline", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/plan-review", LIT_BODY),
    SmokeCase("POST", "/api/v1/literature/consensus-map", LIT_BODY),
    SmokeCase("POST", "/api/v1/reproducibility/dossier", PAPER_BODY),
    SmokeCase("GET", f"/api/v1/researchers/{PID}/global-profile", expected_statuses=(404,)),
    SmokeCase("POST", "/api/v1/review/screen", {"topic": "retrieval"}),
    SmokeCase("POST", "/api/v1/search/federated", {"query": "retrieval", "limit": 3}),
    SmokeCase(
        "POST",
        "/api/v1/subscriptions/searches",
        {"name": "retrieval", "query": "retrieval"},
        expected_statuses=(201,),
    ),
    SmokeCase("GET", "/api/v1/subscriptions/searches"),
    SmokeCase(
        "DELETE",
        f"/api/v1/subscriptions/searches/{PID}",
        expected_statuses=(404,),
    ),
    SmokeCase("GET", "/api/v1/webhooks"),
    SmokeCase(
        "POST",
        "/api/v1/webhooks",
        {"url": "https://example.org/webhook", "events": ["paper.indexed"]},
        expected_statuses=(201,),
    ),
    SmokeCase("POST", "/api/v1/webhooks/test", {"event": "webhook.test"}),
    SmokeCase("POST", f"/api/v1/webhooks/{PID}/rotate-secret", expected_statuses=(404,)),
    SmokeCase("POST", "/api/v1/translate/evidence-pack", {"evidence_pack": {}}),
    SmokeCase("POST", "/api/v1/translate/papers/batch", PAPER_BODY),
    SmokeCase("GET", "/api/v1/usage/current"),
    SmokeCase("GET", "/api/v1/usage/history?days=30"),
    SmokeCase("POST", f"/api/v1/workspaces/{PID}/ask-local", {"question": "What?"}),
    SmokeCase("POST", "/api/v1/writing/citation-check", {"text": "It improves [1]."}),
)


async def override_get_db():
    yield EmptyAsyncSession()


def build_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[dependencies.get_db] = override_get_db
    return TestClient(app)


def is_json_response(response: Any) -> bool:
    content_type = response.headers.get("content-type", "")
    if response.status_code == 204:
        return True
    if "application/json" not in content_type:
        return False
    try:
        response.json()
    except ValueError:
        return False
    return True


def run_case(client: TestClient, case: SmokeCase) -> dict[str, Any]:
    response = client.request(case.method, case.path, json=case.json_body, headers=API_KEY_HEADERS)
    ok = response.status_code in case.expected_statuses and is_json_response(response)
    return {
        "method": case.method,
        "path": case.path,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "rate_limit_policy": response.headers.get("x-ratelimit-policy"),
        "ok": ok,
        "preview": response.text[:240] if response.text else "",
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    passed = sum(1 for item in results if item["ok"])
    lines = [
        "# Agent API Smoke Report",
        "",
        f"Generated at: {datetime.now(tz=UTC).isoformat()}",
        f"Cases: {passed}/{len(results)} passed",
        "",
        "| Method | Path | Status | JSON | Rate-limit header |",
        "|---|---|---:|---|---|",
    ]
    for item in results:
        json_status = "yes" if item["ok"] else "no"
        policy = item["rate_limit_policy"] or "-"
        lines.append(
            "| `{method}` | `{path}` | {status} | {json_status} | {policy} |".format(
                method=item["method"],
                path=item["path"],
                status=item["status"],
                json_status=json_status,
                policy=policy,
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    client = build_client()
    results = [run_case(client, case) for case in SMOKE_CASES]
    report = render_markdown(results)
    output_path = Path("docs/memo/api-smoke-report.md")
    if not output_path.parent.exists():
        output_path = Path("../docs/memo/api-smoke-report.md")
    output_path.write_text(report, encoding="utf-8")
    print(report)
    failed = [item for item in results if not item["ok"]]
    if failed:
        print(json.dumps(failed, ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
