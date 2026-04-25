"""Agent-facing JSON service routes beyond basic CRUD/tool dispatch."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user_id, get_db
from app.services.agent_information_service import AgentInformationService
from app.services.governance_service import GovernanceService
from app.services.local_rag_service import LocalRAGService

router = APIRouter(tags=["agent-services"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
UserId = Annotated[str, Depends(get_current_user_id)]


class EvidenceSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    paper_ids: list[str] = Field(default_factory=list, max_length=300)
    collection_id: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)
    include_paper_fallback: bool = True


class EvidencePackRequest(EvidenceSearchRequest):
    token_budget: int = Field(default=4000, ge=500, le=64000)


class ClaimVerifyRequest(BaseModel):
    claim: str = Field(..., min_length=1, max_length=4000)
    paper_ids: list[str] = Field(default_factory=list, max_length=300)
    collection_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)


class CitationIntentRequest(BaseModel):
    context: str | None = Field(default=None, max_length=5000)
    contexts: list[str] = Field(default_factory=list, max_length=100)


class BenchmarkExtractRequest(BaseModel):
    text: str | None = Field(default=None, max_length=100000)
    paper_ids: list[str] = Field(default_factory=list, max_length=100)
    evidence_pack: dict[str, Any] | None = None


class JsonlExportRequest(BaseModel):
    resources: list[str] = Field(default_factory=lambda: ["papers"])
    paper_ids: list[str] = Field(default_factory=list, max_length=1000)
    limit: int = Field(default=1000, ge=1, le=10000)


class BatchPaperRequest(BaseModel):
    paper_ids: list[str] = Field(default_factory=list, max_length=100)


class LiteratureRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=1000)
    paper_ids: list[str] = Field(default_factory=list, max_length=200)
    limit: int = Field(default=30, ge=1, le=100)


class ReviewScreenRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=1000)
    paper_ids: list[str] = Field(default_factory=list, max_length=300)
    include_reasons: bool = True


class FederatedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    sources: list[str] = Field(default_factory=lambda: ["local", "deepxiv", "openalex"])
    limit: int = Field(default=20, ge=1, le=100)


class SearchSubscriptionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1, max_length=4000)
    filters: dict[str, Any] = Field(default_factory=dict)
    collection_id: str | None = None


class WebhookCreateRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=4096)
    events: list[str] = Field(default_factory=lambda: ["*"])


class WebhookTestRequest(BaseModel):
    url: str | None = Field(default=None, max_length=4096)
    event: str = Field(default="webhook.test", max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    deliver: bool = False


class TranslationBatchRequest(BaseModel):
    paper_ids: list[str] = Field(default_factory=list, max_length=100)
    fields: list[str] = Field(default_factory=lambda: ["title", "abstract"])
    direction: str = Field(default="en2zh", pattern="^(en2zh|zh2en|auto)$")
    execute: bool = False


class WorkspaceAskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=10, ge=1, le=50)
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0)
    answer: bool = False


class CitationCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    paper_ids: list[str] = Field(default_factory=list, max_length=300)


@router.post("/evidence/search")
async def search_evidence(body: EvidenceSearchRequest, db: DbSession, user_id: UserId):
    """Search local paper chunks and metadata for cited evidence snippets."""
    return await AgentInformationService(db, user_id).search_evidence(
        query=body.query,
        paper_ids=body.paper_ids,
        collection_id=body.collection_id,
        top_k=body.top_k,
        include_paper_fallback=body.include_paper_fallback,
    )


@router.post("/evidence/packs")
async def build_evidence_pack(body: EvidencePackRequest, db: DbSession, user_id: UserId):
    """Build a token-budgeted evidence pack for downstream agents."""
    return await AgentInformationService(db, user_id).build_evidence_pack(
        question=body.query,
        paper_ids=body.paper_ids,
        collection_id=body.collection_id,
        token_budget=body.token_budget,
        top_k=body.top_k,
    )


@router.post("/claims/verify")
async def verify_claim(body: ClaimVerifyRequest, db: DbSession, user_id: UserId):
    """Verify a claim against local evidence and return a cited label."""
    return await AgentInformationService(db, user_id).verify_claim(
        claim=body.claim,
        paper_ids=body.paper_ids,
        collection_id=body.collection_id,
        top_k=body.top_k,
    )


@router.post("/citations/intent-classify")
async def classify_citation_intent(body: CitationIntentRequest):
    """Classify citation context intent as background, method, criticism, etc."""
    contexts = body.contexts or ([body.context] if body.context else [])
    return {
        "total": len(contexts),
        "results": [
            {
                "context": context,
                **AgentInformationService.classify_citation_intent(context),
            }
            for context in contexts
        ],
    }


@router.get("/papers/{paper_id}/references")
async def get_paper_references(paper_id: str, db: DbSession, user_id: UserId):
    """Return a paper's extracted reference list."""
    return await AgentInformationService(db, user_id).get_references(paper_id)


@router.get("/papers/{paper_id}/citations/context")
async def get_paper_citation_context(
    paper_id: str,
    db: DbSession,
    user_id: UserId,
    limit: int = Query(50, ge=1, le=200),
):
    """Return contexts and intent labels for outgoing references."""
    return await AgentInformationService(db, user_id).get_citation_contexts(
        paper_id,
        limit=limit,
    )


@router.get("/papers/{paper_id}/citation-contexts")
async def get_paper_citation_contexts(
    paper_id: str,
    db: DbSession,
    user_id: UserId,
    limit: int = Query(50, ge=1, le=200),
):
    """Alias for citation-context retrieval with an agent-friendly name."""
    return await AgentInformationService(db, user_id).get_citation_contexts(
        paper_id,
        limit=limit,
    )


@router.post("/benchmarks/extract")
async def extract_benchmarks(body: BenchmarkExtractRequest, db: DbSession, user_id: UserId):
    """Extract benchmark datasets, metrics, baselines, hardware, and values."""
    return await AgentInformationService(db, user_id).extract_benchmarks(
        text=body.text,
        paper_ids=body.paper_ids,
        evidence_pack=body.evidence_pack,
    )


@router.get("/papers/{paper_id}/sections")
async def get_paper_sections(paper_id: str, db: DbSession, user_id: UserId):
    """Return parsed paper sections normalized for JSON consumers."""
    return await AgentInformationService(db, user_id).paper_sections(paper_id)


@router.get("/papers/{paper_id}/assets")
async def get_paper_assets(paper_id: str, db: DbSession, user_id: UserId):
    """Return normalized figures, tables, code/data, and supplementary assets."""
    return await AgentInformationService(db, user_id).paper_assets(paper_id)


@router.get("/papers/{paper_id}/figures")
async def get_paper_figures(paper_id: str, db: DbSession, user_id: UserId):
    """Return normalized figure metadata for a paper."""
    assets = await AgentInformationService(db, user_id).paper_assets(paper_id)
    return {
        "paper_id": paper_id,
        "figures": assets.get("figures", []),
        "error": assets.get("error"),
    }


@router.get("/papers/{paper_id}/tables")
async def get_paper_tables(paper_id: str, db: DbSession, user_id: UserId):
    """Return normalized table metadata for a paper."""
    assets = await AgentInformationService(db, user_id).paper_assets(paper_id)
    return {"paper_id": paper_id, "tables": assets.get("tables", []), "error": assets.get("error")}


@router.get("/papers/{paper_id}/code-and-data")
async def get_paper_code_and_data(paper_id: str, db: DbSession, user_id: UserId):
    """Return code, dataset, model-weight, and project-page links for a paper."""
    assets = await AgentInformationService(db, user_id).paper_assets(paper_id)
    return {
        "paper_id": paper_id,
        "code_and_data": assets.get("code_and_data", {}),
        "error": assets.get("error"),
    }


@router.get("/discovery/delta")
async def discovery_delta(
    db: DbSession,
    user_id: UserId,
    since: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Return newly discovered/updated papers and saved-search matches."""
    since_dt = _parse_datetime(since) if since else None
    return await AgentInformationService(db, user_id).discovery_delta(
        since=since_dt,
        limit=limit,
    )


@router.post("/exports/jsonl")
async def export_jsonl(body: JsonlExportRequest, db: DbSession, user_id: UserId):
    """Export selected resources as JSONL inside a JSON response envelope."""
    return await AgentInformationService(db, user_id).export_jsonl(
        resources=body.resources,
        paper_ids=body.paper_ids,
        limit=body.limit,
    )


@router.post("/extract/claims/batch")
async def extract_claims_batch(body: BatchPaperRequest, db: DbSession, user_id: UserId):
    """Return cached extracted claims for multiple papers without LLM side effects."""
    service = AgentInformationService(db, user_id)
    results = []
    for paper_id in body.paper_ids:
        export = await service.export_jsonl(["claims"], [paper_id], limit=500)
        claims = [json.loads(line)["data"] for line in export["jsonl"].splitlines() if line]
        results.append({"paper_id": paper_id, "claims": claims, "count": len(claims)})
    return {"total": len(results), "results": results}


@router.post("/extract/experiments/batch")
async def extract_experiments_batch(body: BatchPaperRequest, db: DbSession, user_id: UserId):
    """Return cached experiment records for multiple papers."""
    service = AgentInformationService(db, user_id)
    results = []
    for paper_id in body.paper_ids:
        export = await service.export_jsonl(["experiments"], [paper_id], limit=500)
        rows = [json.loads(line)["data"] for line in export["jsonl"].splitlines() if line]
        results.append({"paper_id": paper_id, "experiments": rows, "count": len(rows)})
    return {"total": len(results), "results": results}


@router.post("/extract/figures/batch")
async def extract_figures_batch(body: BatchPaperRequest, db: DbSession, user_id: UserId):
    """Return cached figure/table records for multiple papers."""
    service = AgentInformationService(db, user_id)
    results = []
    for paper_id in body.paper_ids:
        assets = await service.paper_assets(paper_id)
        results.append(
            {
                "paper_id": paper_id,
                "figures": assets.get("figures", []),
                "tables": assets.get("tables", []),
                "error": assets.get("error"),
            }
        )
    return {"total": len(results), "results": results}


@router.post("/quality/batch")
async def quality_batch(body: BatchPaperRequest, db: DbSession):
    """Return quality reports for multiple papers."""
    from app.services.quality_service import QualityService

    quality = QualityService(db)
    results = []
    for paper_id in body.paper_ids:
        results.append(await quality.get_quality_report(paper_id))
    return {"total": len(results), "results": results}


async def _literature(body: LiteratureRequest, db: DbSession, user_id: UserId, mode: str):
    return await AgentInformationService(db, user_id).literature_map(
        topic=body.topic,
        paper_ids=body.paper_ids,
        limit=body.limit,
        mode=mode,
    )


@router.post("/literature/review-map")
async def literature_review_map(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Build a graph-oriented review map for a topic or paper set."""
    return await _literature(body, db, user_id, "review-map")


@router.post("/literature/related-work-pack")
async def related_work_pack(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Build a structured related-work pack with graph and source nodes."""
    return await _literature(body, db, user_id, "related-work-pack")


@router.post("/literature/contradiction-map")
async def contradiction_map(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Return graph data plus contradiction-oriented claim candidates."""
    result = await _literature(body, db, user_id, "contradiction-map")
    result["contradictions"] = [
        claim for claim in result.get("claims", []) if "not" in claim.get("text", "").lower()
    ]
    return result


@router.post("/literature/minimal-reading-set")
async def minimal_reading_set(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Return a compact reading set ranked by citation count and theme coverage."""
    result = await _literature(body, db, user_id, "minimal-reading-set")
    result["minimal_set"] = result.get("reading_order", [])[: min(10, body.limit)]
    return result


@router.post("/literature/research-timeline")
async def research_timeline(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Return paper nodes grouped into a year-based timeline."""
    result = await _literature(body, db, user_id, "research-timeline")
    timeline: dict[str, list[dict[str, Any]]] = {}
    for node in result.get("nodes", []):
        timeline.setdefault(str(node.get("year") or "unknown"), []).append(node)
    result["timeline"] = timeline
    return result


@router.post("/literature/plan-review")
async def literature_plan_review(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Return a review plan with suggested themes and reading order."""
    result = await _literature(body, db, user_id, "plan-review")
    result["plan"] = {
        "themes_to_cover": result.get("themes", [])[:8],
        "recommended_order": result.get("reading_order", [])[:20],
        "evidence_policy": "cite nodes by paper_id and keep snippets from evidence APIs",
    }
    return result


@router.post("/literature/consensus-map")
async def literature_consensus_map(body: LiteratureRequest, db: DbSession, user_id: UserId):
    """Return theme-level consensus candidates from overlapping keywords/claims."""
    result = await _literature(body, db, user_id, "consensus-map")
    result["consensus"] = [theme for theme in result.get("themes", []) if theme["paper_count"] > 1]
    return result


@router.get("/labs/search")
async def labs_search(
    db: DbSession,
    user_id: UserId,
    q: str | None = Query(None, max_length=500),
    limit: int = Query(20, ge=1, le=100),
):
    """Search local institution/lab profiles."""
    return await AgentInformationService(db, user_id).labs_search(query=q, limit=limit)


@router.post("/reproducibility/dossier")
async def reproducibility_dossier(
    body: BatchPaperRequest,
    db: DbSession,
    user_id: UserId,
):
    """Build reproducibility dossiers from quality signals and artifact links."""
    return await AgentInformationService(db, user_id).reproducibility_dossier(
        paper_ids=body.paper_ids
    )


@router.get("/researchers/{author_id}/global-profile")
async def researcher_global_profile(author_id: str, db: DbSession, user_id: UserId):
    """Return a local/global-shaped author profile for agents."""
    result = await AgentInformationService(db, user_id).researcher_global_profile(author_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Researcher not found")
    return result


@router.post("/review/screen")
async def review_screen(body: ReviewScreenRequest, db: DbSession, user_id: UserId):
    """Screen papers against a review topic with inclusion reasons."""
    return await AgentInformationService(db, user_id).review_screen(
        topic=body.topic,
        paper_ids=body.paper_ids,
        include_reasons=body.include_reasons,
    )


@router.post("/search/federated")
async def search_federated(body: FederatedSearchRequest, db: DbSession, user_id: UserId):
    """Return a federated-search response shape with local hits and provider status."""
    return await AgentInformationService(db, user_id).federated_search(
        query=body.query,
        sources=body.sources,
        limit=body.limit,
    )


@router.post("/subscriptions/searches", status_code=201)
async def create_search_subscription(
    body: SearchSubscriptionRequest,
    db: DbSession,
):
    """Create a saved search subscription for discovery delta matching."""
    return await GovernanceService(db).create_saved_search(
        name=body.name,
        query=body.query,
        filters=body.filters,
        collection_id=body.collection_id,
    )


@router.get("/subscriptions/searches")
async def list_search_subscriptions(db: DbSession):
    """List saved search subscriptions."""
    return {"subscriptions": await GovernanceService(db).list_saved_searches()}


@router.delete("/subscriptions/searches/{search_id}", status_code=204)
async def delete_search_subscription(search_id: str, db: DbSession):
    """Delete a saved search subscription."""
    if not await GovernanceService(db).delete_saved_search(search_id):
        raise HTTPException(status_code=404, detail="Subscription not found")


@router.get("/subscriptions/events")
async def subscription_events(request: Request, heartbeat: int = Query(30, ge=5, le=120)):
    """Open an SSE stream for subscription and webhook event payloads."""
    import asyncio

    from app.api.v1.sse import _event_stream, _subscribers

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(queue)
    return StreamingResponse(
        _event_stream(queue, request, heartbeat),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/webhooks")
async def list_webhooks(db: DbSession):
    """List active webhooks through the public API namespace."""
    return {"webhooks": await GovernanceService(db).list_webhooks()}


@router.post("/webhooks", status_code=201)
async def create_webhook(body: WebhookCreateRequest, db: DbSession):
    """Create a webhook through the public API namespace."""
    return await GovernanceService(db).create_webhook(url=body.url, events=body.events)


@router.post("/webhooks/test")
async def test_webhook(body: WebhookTestRequest):
    """Build or optionally deliver a test webhook payload."""
    payload = {
        "event": body.event,
        "data": body.payload or {"ok": True},
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }
    if not body.deliver:
        return {"delivered": False, "dry_run": True, "payload": payload}
    if not body.url:
        raise HTTPException(status_code=422, detail="url is required when deliver=true")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(body.url, json=payload)
    return {"delivered": response.status_code < 300, "status_code": response.status_code}


@router.post("/webhooks/{webhook_id}/rotate-secret")
async def rotate_webhook_secret(webhook_id: str, db: DbSession, user_id: UserId):
    """Rotate a webhook signing secret and return the new secret once."""
    result = await AgentInformationService(db, user_id).rotate_webhook_secret(webhook_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return result


@router.post("/translate/evidence-pack")
async def translate_evidence_pack(body: dict[str, Any]):
    """Return a translation-ready evidence pack envelope without losing citations."""
    evidence_pack = body.get("evidence_pack") or body
    return {
        "status": "prepared",
        "direction": body.get("direction", "en2zh"),
        "evidence_pack": evidence_pack,
        "translation_policy": "preserve anchors, paper_id, section_title, and provenance",
        "execute_endpoint": "/api/v1/translate",
    }


@router.post("/translate/papers/batch")
async def translate_papers_batch(body: TranslationBatchRequest, db: DbSession, user_id: UserId):
    """Prepare or execute batch paper metadata translation."""
    service = AgentInformationService(db, user_id)
    results = []
    for paper_id in body.paper_ids:
        sections = await service.paper_sections(paper_id)
        results.append(
            {
                "paper_id": paper_id,
                "status": "prepared" if not body.execute else "queued_for_existing_translate_api",
                "fields": body.fields,
                "title": sections.get("title"),
                "direction": body.direction,
            }
        )
    return {"execute": body.execute, "total": len(results), "results": results}


@router.get("/usage/current")
async def usage_current(db: DbSession, user_id: UserId):
    """Return current API usage/accounting metadata for the caller."""
    return await AgentInformationService(db, user_id).usage_current()


@router.get("/usage/history")
async def usage_history(
    db: DbSession,
    user_id: UserId,
    days: int = Query(30, ge=1, le=366),
):
    """Return available API usage history for the caller."""
    return await AgentInformationService(db, user_id).usage_history(days=days)


@router.post("/workspaces/{collection_id}/ask-local")
async def ask_workspace_local(
    collection_id: str,
    body: WorkspaceAskRequest,
    db: DbSession,
    user_id: UserId,
):
    """Ask a collection using local RAG evidence, optionally with an LLM answer."""
    service = LocalRAGService(db, user_id=user_id)
    if body.answer:
        return await service.ask_collection(
            collection_id=collection_id,
            question=body.question,
            top_k=body.top_k,
            min_similarity=body.min_similarity,
        )
    return await service.get_collection_evidence(
        collection_id=collection_id,
        question=body.question,
        top_k=body.top_k,
        min_similarity=body.min_similarity,
    )


@router.post("/writing/citation-check")
async def writing_citation_check(body: CitationCheckRequest, db: DbSession, user_id: UserId):
    """Check citation-like writing sentences against local evidence."""
    return await AgentInformationService(db, user_id).citation_check(
        text=body.text,
        paper_ids=body.paper_ids,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
