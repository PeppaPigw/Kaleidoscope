"""Agent-facing deterministic paper intelligence services."""

from __future__ import annotations

import json
import re
import secrets
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.api_key import APIKey
from app.models.author import Author, Institution, PaperAuthor
from app.models.claim import Claim
from app.models.collection import DEFAULT_USER_ID, CollectionPaper
from app.models.experiment import Experiment
from app.models.governance import ReproductionAttempt, SavedSearch, Webhook
from app.models.paper import Paper, PaperReference
from app.models.paper_qa import PaperChunk
from app.services.quality_service import QualityService

_DATASET_PATTERNS = [
    "ImageNet",
    "CIFAR-10",
    "CIFAR-100",
    "COCO",
    "SQuAD",
    "GLUE",
    "SuperGLUE",
    "MNIST",
    "PubMed",
    "MIMIC",
    "arXiv",
    "WikiText",
]
_METRIC_PATTERNS = [
    "accuracy",
    "precision",
    "recall",
    "F1",
    "AUROC",
    "AUC",
    "BLEU",
    "ROUGE",
    "mAP",
    "RMSE",
    "MAE",
    "perplexity",
]
_HARDWARE_PATTERNS = ["GPU", "TPU", "A100", "H100", "V100", "T4", "CPU"]
_BASELINE_PATTERNS = ["baseline", "BERT", "ResNet", "Transformer", "SVM", "CNN"]
_NEGATION_MARKERS = [
    "not",
    "fails",
    "failed",
    "worse",
    "contradict",
    "contradicts",
    "no significant",
    "does not",
    "cannot",
]
_SUPPORT_MARKERS = [
    "support",
    "supports",
    "improve",
    "improves",
    "outperform",
    "outperforms",
    "achieve",
    "achieves",
    "demonstrate",
    "demonstrates",
    "shows",
    "show",
]
_INTENT_KEYWORDS: dict[str, set[str]] = {
    "background": {"background", "prior", "previous", "related", "inspired"},
    "method": {"method", "approach", "algorithm", "architecture", "use", "adopt"},
    "comparison": {"compare", "comparison", "baseline", "outperform", "versus"},
    "criticism": {"limitation", "fail", "weak", "however", "although", "contrary"},
    "extension": {"extend", "build upon", "follow", "adapt", "improve"},
    "dataset": {"dataset", "benchmark", "corpus", "data", "samples"},
    "benchmark": {"benchmark", "metric", "score", "leaderboard", "evaluation"},
    "evidence": {"evidence", "show", "demonstrate", "confirm", "support"},
}


class AgentInformationService:
    """Build JSON-first information services for downstream research agents."""

    def __init__(self, db: AsyncSession, user_id: str = DEFAULT_USER_ID):
        self.db = db
        self.user_id = user_id

    async def resolve_scope(
        self,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        limit: int = 100,
    ) -> list[str]:
        """Resolve explicit paper IDs plus optional collection membership."""
        resolved = [pid.strip() for pid in paper_ids or [] if pid and pid.strip()]
        if collection_id:
            result = await self.db.execute(
                select(CollectionPaper.paper_id)
                .where(CollectionPaper.collection_id == collection_id)
                .order_by(CollectionPaper.position.asc())
                .limit(limit)
            )
            resolved.extend(str(row[0]) for row in result.all())
        return list(dict.fromkeys(resolved))[:limit]

    async def search_evidence(
        self,
        query: str,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        top_k: int = 10,
        include_paper_fallback: bool = True,
    ) -> dict[str, Any]:
        """Return ranked local snippets with paper provenance and citation anchors."""
        terms = self._terms(query)
        scoped_ids = await self.resolve_scope(paper_ids, collection_id, limit=300)
        candidates = await self._chunk_candidates(scoped_ids, limit=max(top_k * 8, 40))
        evidence = [self._chunk_to_evidence(row, terms) for row in candidates]

        if include_paper_fallback:
            seen_papers = {item["paper_id"] for item in evidence}
            papers = await self._paper_candidates(scoped_ids, limit=max(top_k * 3, 20))
            for paper in papers:
                if str(paper.id) not in seen_papers or len(evidence) < top_k:
                    fallback = self._paper_to_evidence(paper, terms)
                    if fallback:
                        evidence.append(fallback)

        ranked = sorted(
            evidence,
            key=lambda item: (item["score"], item.get("created_at") or ""),
            reverse=True,
        )[:top_k]
        for index, item in enumerate(ranked, 1):
            item["anchor"] = f"E{index}"
            item.pop("created_at", None)

        return {
            "query": query,
            "scope": {"paper_ids": scoped_ids, "collection_id": collection_id},
            "total": len(ranked),
            "evidence": ranked,
            "diagnostics": {
                "backend": "local_sql",
                "query_terms": terms,
                "candidate_count": len(evidence),
                "top_k": top_k,
            },
        }

    async def build_evidence_pack(
        self,
        question: str,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        token_budget: int = 4000,
        top_k: int = 12,
    ) -> dict[str, Any]:
        """Build a compact cited evidence pack for agent prompts."""
        search = await self.search_evidence(
            query=question,
            paper_ids=paper_ids,
            collection_id=collection_id,
            top_k=top_k,
        )
        evidence = self._fit_to_budget(search["evidence"], token_budget)
        return {
            "question": question,
            "scope": search["scope"],
            "budget": {
                "requested_tokens": token_budget,
                "estimated_tokens": self._estimate_tokens(evidence),
                "truncated": len(evidence) < len(search["evidence"]),
            },
            "citations": [
                {
                    "anchor": item["anchor"],
                    "paper_id": item["paper_id"],
                    "paper_title": item["paper_title"],
                    "section_title": item.get("section_title"),
                }
                for item in evidence
            ],
            "evidence": evidence,
            "warnings": [] if evidence else ["No local evidence matched the request."],
            "diagnostics": search["diagnostics"],
        }

    async def verify_claim(
        self,
        claim: str,
        paper_ids: list[str] | None = None,
        collection_id: str | None = None,
        top_k: int = 8,
    ) -> dict[str, Any]:
        """Classify a claim as supported, refuted, or insufficient from snippets."""
        pack = await self.build_evidence_pack(
            question=claim,
            paper_ids=paper_ids,
            collection_id=collection_id,
            top_k=top_k,
        )
        evidence = pack["evidence"]
        if not evidence:
            label = "insufficient"
            confidence = 0.0
        else:
            joined = "\n".join(item.get("content", "") for item in evidence).lower()
            support_hits = sum(1 for marker in _SUPPORT_MARKERS if marker in joined)
            refute_hits = sum(1 for marker in _NEGATION_MARKERS if marker in joined)
            top_score = max(item.get("score", 0.0) for item in evidence)
            if refute_hits > support_hits and top_score >= 0.15:
                label = "refuted"
                confidence = min(0.95, 0.45 + refute_hits * 0.12 + top_score)
            elif top_score >= 0.25 or support_hits:
                label = "supported"
                confidence = min(0.95, 0.35 + support_hits * 0.10 + top_score)
            else:
                label = "insufficient"
                confidence = min(0.45, top_score)

        return {
            "claim": claim,
            "label": label,
            "confidence": round(confidence, 3),
            "rationale": self._claim_rationale(label, evidence),
            "evidence_pack": pack,
        }

    async def get_references(self, paper_id: str) -> dict[str, Any]:
        """Return extracted outgoing references for one paper."""
        result = await self.db.execute(
            select(PaperReference)
            .where(PaperReference.citing_paper_id == paper_id)
            .order_by(PaperReference.position.asc().nullslast())
        )
        references = [self._reference_dict(ref) for ref in result.scalars().all()]
        return {"paper_id": paper_id, "total": len(references), "references": references}

    async def get_citation_contexts(
        self,
        paper_id: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Return local contexts around outgoing references when available."""
        refs = (await self.get_references(paper_id))["references"]
        chunk_result = await self.db.execute(
            select(PaperChunk)
            .where(PaperChunk.paper_id == paper_id, PaperChunk.is_references.is_(False))
            .order_by(PaperChunk.order_index.asc())
            .limit(300)
        )
        chunks = list(chunk_result.scalars().all())
        contexts = []
        for ref in refs[:limit]:
            context_text = self._find_reference_context(ref, chunks)
            intent = self.classify_citation_intent(
                context_text or ref.get("raw_string") or ref.get("raw_title") or ""
            )
            contexts.append(
                {
                    "reference": ref,
                    "context": context_text,
                    "intent": intent,
                    "provenance": {"source": "paper_references+paper_chunks"},
                }
            )
        return {"paper_id": paper_id, "total": len(contexts), "contexts": contexts}

    async def extract_benchmarks(
        self,
        text: str | None = None,
        paper_ids: list[str] | None = None,
        evidence_pack: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract deterministic benchmark signals from text, papers, or evidence."""
        sources: list[dict[str, Any]] = []
        if evidence_pack:
            for item in evidence_pack.get("evidence", []):
                sources.append(
                    {
                        "paper_id": item.get("paper_id"),
                        "paper_title": item.get("paper_title"),
                        "text": item.get("content") or item.get("snippet") or "",
                    }
                )
        if text:
            sources.append({"paper_id": None, "paper_title": None, "text": text})
        if paper_ids:
            papers = await self._paper_candidates(paper_ids, limit=len(paper_ids))
            for paper in papers:
                sources.append(
                    {
                        "paper_id": str(paper.id),
                        "paper_title": paper.title,
                        "text": self._paper_text(paper, max_chars=12000),
                    }
                )

        records = [self.extract_benchmark_record(source) for source in sources]
        records = [record for record in records if record["signals_found"]]
        return {
            "total_sources": len(sources),
            "records_found": len(records),
            "records": records,
            "schema": {
                "datasets": "list[str]",
                "metrics": "list[str]",
                "baselines": "list[str]",
                "hardware": "list[str]",
                "result_values": "list[{metric,value,unit,context}]",
            },
        }

    async def paper_sections(self, paper_id: str) -> dict[str, Any]:
        """Return normalized sections from parsed_sections or markdown headings."""
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "sections": [], "error": "Paper not found"}
        sections = self._sections_for_paper(paper)
        return {"paper_id": paper_id, "title": paper.title, "sections": sections}

    async def paper_assets(self, paper_id: str) -> dict[str, Any]:
        """Return figures, tables, code URLs, data URLs, and remote assets."""
        paper = await self._get_paper(paper_id)
        if not paper:
            return {"paper_id": paper_id, "error": "Paper not found"}
        figures, tables = self._split_figures_tables(paper.parsed_figures or [])
        code_and_data = self._code_and_data_assets(paper)
        remote_assets = [
            item
            for item in paper.remote_urls or []
            if isinstance(item, dict) and item.get("url")
        ]
        return {
            "paper_id": str(paper.id),
            "title": paper.title,
            "figures": figures,
            "tables": tables,
            "code_and_data": code_and_data,
            "remote_assets": remote_assets,
            "supplementary_materials": self._supplementary_assets(paper),
        }

    async def discovery_delta(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Return papers and saved-search matches discovered since a timestamp."""
        since = since or datetime.now(tz=UTC) - timedelta(days=1)
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.deleted_at.is_(None),
                or_(Paper.created_at >= since, Paper.updated_at >= since),
            )
            .order_by(desc(Paper.created_at))
            .limit(limit)
        )
        papers = [self._paper_summary(paper) for paper in result.scalars().all()]
        saved_searches = await self._saved_searches()
        alert_matches = self._match_saved_searches(papers, saved_searches)
        return {
            "since": since.isoformat(),
            "new_or_updated_papers": papers,
            "alert_matches": alert_matches,
            "trending_changes": [],
            "importable_candidates": [
                paper for paper in papers if paper.get("ingestion_status") == "discovered"
            ],
            "total": len(papers),
        }

    async def export_jsonl(
        self,
        resources: list[str],
        paper_ids: list[str] | None = None,
        limit: int = 1000,
    ) -> dict[str, Any]:
        """Export selected resources as JSONL embedded in a JSON envelope."""
        scope = await self.resolve_scope(paper_ids, limit=limit)
        lines: list[dict[str, Any]] = []
        normalized = set(resources or ["papers"])
        if "papers" in normalized:
            papers = await self._paper_candidates(scope, limit=limit)
            lines.extend({"type": "paper", "data": self._paper_summary(p)} for p in papers)
        if "chunks" in normalized:
            lines.extend(await self._jsonl_chunks(scope, limit=limit))
        if "claims" in normalized:
            lines.extend(await self._jsonl_claims(scope, limit=limit))
        if "citations" in normalized:
            lines.extend(await self._jsonl_citations(scope, limit=limit))
        if "experiments" in normalized:
            lines.extend(await self._jsonl_experiments(scope, limit=limit))
        jsonl = "\n".join(json.dumps(line, ensure_ascii=False, default=str) for line in lines)
        return {
            "format": "jsonl",
            "content_type": "application/x-ndjson",
            "resources": sorted(normalized),
            "line_count": len(lines),
            "jsonl": jsonl,
        }

    async def literature_map(
        self,
        topic: str | None = None,
        paper_ids: list[str] | None = None,
        mode: str = "review-map",
        limit: int = 30,
    ) -> dict[str, Any]:
        """Build deterministic graph-style literature review artifacts."""
        papers = await self._papers_for_topic(topic, paper_ids, limit=limit)
        nodes = [self._paper_node(paper) for paper in papers]
        edges = self._keyword_edges(nodes)
        themes = self._themes(nodes)
        return {
            "mode": mode,
            "topic": topic,
            "paper_count": len(nodes),
            "nodes": nodes,
            "edges": edges,
            "themes": themes,
            "claims": self._claim_like_statements(papers),
            "reading_order": sorted(
                nodes,
                key=lambda item: (item.get("year") or 0, item.get("citation_count") or 0),
                reverse=True,
            ),
        }

    async def review_screen(
        self,
        topic: str,
        paper_ids: list[str] | None = None,
        include_reasons: bool = True,
    ) -> dict[str, Any]:
        """Screen papers for topical inclusion using lexical evidence."""
        terms = self._terms(topic)
        papers = await self._papers_for_topic(topic, paper_ids, limit=100)
        decisions = []
        for paper in papers:
            text = self._paper_text(paper, max_chars=4000).lower()
            hits = [term for term in terms if term in text]
            decision = "include" if len(hits) >= max(1, min(2, len(terms))) else "maybe"
            item = {
                "paper": self._paper_summary(paper),
                "decision": decision,
                "confidence": round(min(0.95, 0.35 + len(hits) * 0.15), 3),
            }
            if include_reasons:
                item["reasons"] = [f"Matched term: {term}" for term in hits[:5]]
            decisions.append(item)
        return {"topic": topic, "screened": len(decisions), "decisions": decisions}

    async def federated_search(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return local federated-search shape; external providers stay proxied elsewhere."""
        terms = self._terms(query)
        papers = await self._papers_for_topic(query, None, limit=limit)
        local_hits = []
        for paper in papers:
            text = self._paper_text(paper, max_chars=3000)
            local_hits.append(
                {
                    "source": "local",
                    "paper": self._paper_summary(paper),
                    "score": self._score(text, terms),
                    "snippet": self._snippet(text, terms),
                }
            )
        return {
            "query": query,
            "sources_requested": sources or ["local", "deepxiv", "openalex"],
            "hits": sorted(local_hits, key=lambda item: item["score"], reverse=True),
            "provider_status": {
                "local": "ok",
                "deepxiv": "available via /api/v1/deepxiv/*",
                "openalex": "available via /api/v1/openalex/*",
            },
        }

    async def reproducibility_dossier(
        self,
        paper_id: str | None = None,
        paper_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate quality, assets, and reproduction attempts for papers."""
        ids = [paper_id] if paper_id else paper_ids or []
        dossiers = []
        quality = QualityService(self.db)
        for pid in ids:
            assets = await self.paper_assets(pid)
            attempts = await self._reproduction_attempts(pid)
            dossiers.append(
                {
                    "paper_id": pid,
                    "quality": await quality.get_reproducibility(pid),
                    "code_and_data": assets.get("code_and_data", {}),
                    "reproduction_attempts": attempts,
                    "risk_flags": self._reproducibility_flags(assets, attempts),
                }
            )
        return {"total": len(dossiers), "dossiers": dossiers}

    async def usage_current(self) -> dict[str, Any]:
        """Return current local API usage/accounting metadata."""
        key_count = await self.db.scalar(
            select(func.count()).select_from(APIKey).where(APIKey.user_id == self.user_id)
        )
        active_key_count = await self.db.scalar(
            select(func.count())
            .select_from(APIKey)
            .where(APIKey.user_id == self.user_id, APIKey.revoked_at.is_(None))
        )
        return {
            "user_id": self.user_id,
            "api_keys": {"total": key_count or 0, "active": active_key_count or 0},
            "limits": {
                "batch_max_calls": 20,
                "default_page_limit": 20,
                "rate_limit_policy": "deployment-configured",
            },
            "metering": {
                "llm_costs": "available at /api/v1/admin/costs",
                "per_key_usage": "not yet persisted",
            },
        }

    async def usage_history(self, days: int = 30) -> dict[str, Any]:
        """Return available usage history shape without inventing metered rows."""
        since = datetime.now(tz=UTC) - timedelta(days=days)
        created_keys = await self.db.scalar(
            select(func.count())
            .select_from(APIKey)
            .where(APIKey.user_id == self.user_id, APIKey.created_at >= since)
        )
        return {
            "user_id": self.user_id,
            "days": days,
            "since": since.isoformat(),
            "daily": [],
            "summary": {"api_keys_created": created_keys or 0},
            "warnings": ["Request-level usage history is not persisted yet."],
        }

    async def labs_search(self, query: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Search institutions/labs and summarize associated local authors."""
        stmt = select(Institution).order_by(Institution.name.asc()).limit(limit)
        if query:
            like = f"%{query}%"
            stmt = (
                select(Institution)
                .where(or_(Institution.name.ilike(like), Institution.display_name.ilike(like)))
                .order_by(Institution.name.asc())
                .limit(limit)
            )
        result = await self.db.execute(stmt)
        labs = []
        for institution in result.scalars().all():
            author_count = await self.db.scalar(
                select(func.count())
                .select_from(Author)
                .where(Author.institution_id == institution.id)
            )
            labs.append(
                {
                    "id": str(institution.id),
                    "name": institution.display_name or institution.name,
                    "country": institution.country,
                    "type": institution.type,
                    "homepage_url": institution.homepage_url,
                    "author_count": author_count or 0,
                    "identifiers": {
                        "openalex_id": institution.openalex_id,
                        "ror_id": institution.ror_id,
                    },
                }
            )
        return {"query": query, "total": len(labs), "labs": labs}

    async def researcher_global_profile(self, author_id: str) -> dict[str, Any] | None:
        """Return a local-plus-global author profile shape for agents."""
        result = await self.db.execute(
            select(Author)
            .options(selectinload(Author.institution))
            .where(Author.id == author_id)
        )
        author = result.scalar_one_or_none()
        if not author:
            return None
        papers = await self.db.execute(
            select(Paper)
            .join(PaperAuthor, Paper.id == PaperAuthor.paper_id)
            .where(PaperAuthor.author_id == author_id, Paper.deleted_at.is_(None))
            .order_by(Paper.published_at.desc().nullslast())
            .limit(100)
        )
        paper_list = [self._paper_summary(paper) for paper in papers.scalars().all()]
        return {
            "id": str(author.id),
            "display_name": author.display_name,
            "identifiers": {
                "openalex_id": author.openalex_id,
                "orcid": author.orcid,
                "semantic_scholar_id": author.semantic_scholar_id,
            },
            "metrics": {
                "h_index": author.h_index,
                "paper_count": author.paper_count or len(paper_list),
                "citation_count": author.citation_count,
            },
            "institution": (
                {
                    "id": str(author.institution.id),
                    "name": author.institution.display_name or author.institution.name,
                    "country": author.institution.country,
                }
                if author.institution
                else None
            ),
            "local_papers": paper_list,
            "global_sources": {
                "semantic_scholar": bool(author.semantic_scholar_id),
                "openalex": bool(author.openalex_id),
            },
        }

    async def rotate_webhook_secret(self, webhook_id: str) -> dict[str, Any] | None:
        """Rotate a webhook signing secret and return it exactly once."""
        result = await self.db.execute(
            select(Webhook).where(Webhook.id == webhook_id, Webhook.user_id == self.user_id)
        )
        webhook = result.scalar_one_or_none()
        if not webhook:
            return None
        secret = f"whsec_{secrets.token_urlsafe(32)}"
        webhook.secret = secret
        await self.db.flush()
        return {
            "id": str(webhook.id),
            "url": webhook.url,
            "events": webhook.events,
            "secret": secret,
            "secret_returned_once": True,
        }

    async def citation_check(
        self,
        text: str,
        paper_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Check whether citation-like claims have supplied local evidence."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", text) if s.strip()]
        checks = []
        for sentence in sentences[:30]:
            if "[" not in sentence and "(" not in sentence:
                continue
            verification = await self.verify_claim(sentence, paper_ids=paper_ids, top_k=3)
            checks.append(
                {
                    "sentence": sentence,
                    "label": verification["label"],
                    "confidence": verification["confidence"],
                    "evidence": verification["evidence_pack"]["evidence"],
                }
            )
        return {
            "checked_sentences": len(checks),
            "checks": checks,
            "warnings": [] if checks else ["No citation-like sentences detected."],
        }

    @classmethod
    def classify_citation_intent(cls, context: str) -> dict[str, Any]:
        """Classify a citation context into one intent label plus scores."""
        text = (context or "").lower()
        scores = {
            intent: sum(1 for kw in keywords if kw in text)
            for intent, keywords in _INTENT_KEYWORDS.items()
        }
        label, score = max(scores.items(), key=lambda item: item[1])
        if score == 0:
            label = "background"
        total = sum(scores.values()) or 1
        return {
            "label": label,
            "scores": {key: round(value / total, 3) for key, value in scores.items()},
            "confidence": round(max(scores.values()) / total, 3) if total else 0.0,
        }

    @classmethod
    def extract_benchmark_record(cls, source: dict[str, Any]) -> dict[str, Any]:
        """Extract normalized benchmark fields from a single text source."""
        text = source.get("text") or ""
        datasets = cls._known_matches(text, _DATASET_PATTERNS)
        metrics = cls._known_matches(text, _METRIC_PATTERNS)
        hardware = cls._known_matches(text, _HARDWARE_PATTERNS)
        baselines = cls._known_matches(text, _BASELINE_PATTERNS)
        result_values = cls._result_values(text)
        return {
            "paper_id": source.get("paper_id"),
            "paper_title": source.get("paper_title"),
            "datasets": datasets,
            "metrics": metrics,
            "baselines": baselines,
            "hardware": hardware,
            "result_values": result_values,
            "signals_found": bool(datasets or metrics or hardware or baselines or result_values),
        }

    async def _chunk_candidates(
        self,
        paper_ids: list[str],
        limit: int,
    ) -> list[Any]:
        stmt = (
            select(PaperChunk, Paper.title, Paper.doi, Paper.arxiv_id, Paper.created_at)
            .join(Paper, Paper.id == PaperChunk.paper_id)
            .where(Paper.deleted_at.is_(None), PaperChunk.is_references.is_(False))
            .order_by(PaperChunk.order_index.asc())
            .limit(limit)
        )
        if paper_ids:
            stmt = stmt.where(Paper.id.in_(paper_ids))
        result = await self.db.execute(stmt)
        return list(result.all())

    async def _paper_candidates(
        self,
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[Paper]:
        stmt = select(Paper).where(Paper.deleted_at.is_(None)).limit(limit)
        if paper_ids:
            stmt = stmt.where(Paper.id.in_(paper_ids))
        else:
            stmt = stmt.order_by(desc(Paper.created_at))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_paper(self, paper_id: str) -> Paper | None:
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    def _chunk_to_evidence(self, row: Any, terms: list[str]) -> dict[str, Any]:
        chunk, title, doi, arxiv_id, created_at = row
        content = chunk.content or ""
        score = self._score(content, terms)
        return {
            "id": str(chunk.id),
            "paper_id": str(chunk.paper_id),
            "paper_title": title,
            "section_title": chunk.section_title,
            "content": self._snippet(content, terms, max_chars=900),
            "score": score,
            "source": "paper_chunk",
            "doi": doi,
            "arxiv_id": arxiv_id,
            "provenance": {
                "table": "paper_chunks",
                "chunk_id": str(chunk.id),
                "order_index": chunk.order_index,
            },
            "created_at": str(created_at) if created_at else None,
        }

    def _paper_to_evidence(self, paper: Paper, terms: list[str]) -> dict[str, Any] | None:
        content = self._paper_text(paper, max_chars=5000)
        if not content:
            return None
        return {
            "id": f"paper:{paper.id}",
            "paper_id": str(paper.id),
            "paper_title": paper.title,
            "section_title": "metadata",
            "content": self._snippet(content, terms, max_chars=900),
            "score": self._score(content, terms) * 0.8,
            "source": "paper_metadata",
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "provenance": {"table": "papers", "paper_id": str(paper.id)},
            "created_at": str(paper.created_at) if paper.created_at else None,
        }

    @classmethod
    def _terms(cls, text: str | None) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-]{2,}", (text or "").lower())
        stop = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "paper",
            "study",
            "using",
            "into",
            "what",
            "which",
        }
        return [token for token in dict.fromkeys(tokens) if token not in stop][:24]

    @classmethod
    def _score(cls, text: str, terms: list[str]) -> float:
        if not terms:
            return 0.1 if text else 0.0
        lowered = text.lower()
        hits = sum(lowered.count(term) for term in terms)
        coverage = sum(1 for term in terms if term in lowered) / max(len(terms), 1)
        density = min(1.0, hits / max(len(terms), 1))
        return round((coverage * 0.7) + (density * 0.3), 3)

    @classmethod
    def _snippet(cls, text: str, terms: list[str], max_chars: int = 700) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if len(clean) <= max_chars:
            return clean
        lowered = clean.lower()
        positions = [lowered.find(term) for term in terms if term in lowered]
        start = max(min(positions) - max_chars // 4, 0) if positions else 0
        end = min(start + max_chars, len(clean))
        prefix = "..." if start else ""
        suffix = "..." if end < len(clean) else ""
        return f"{prefix}{clean[start:end]}{suffix}"

    @staticmethod
    def _estimate_tokens(items: list[dict[str, Any]]) -> int:
        chars = sum(len(json.dumps(item, ensure_ascii=False, default=str)) for item in items)
        return max(1, chars // 4)

    def _fit_to_budget(
        self,
        evidence: list[dict[str, Any]],
        token_budget: int,
    ) -> list[dict[str, Any]]:
        selected = []
        for item in evidence:
            trial = [*selected, item]
            if self._estimate_tokens(trial) > token_budget and selected:
                break
            selected.append(item)
        return selected

    @staticmethod
    def _claim_rationale(label: str, evidence: list[dict[str, Any]]) -> str:
        if not evidence:
            return "No matching local snippets were found."
        top = evidence[0]
        return (
            f"The claim is labeled {label} from the top local snippet "
            f"{top.get('anchor')} in {top.get('paper_title')}."
        )

    @staticmethod
    def _reference_dict(ref: PaperReference) -> dict[str, Any]:
        return {
            "id": str(ref.id),
            "citing_paper_id": str(ref.citing_paper_id),
            "cited_paper_id": str(ref.cited_paper_id) if ref.cited_paper_id else None,
            "raw_title": ref.raw_title,
            "raw_authors": ref.raw_authors,
            "raw_year": ref.raw_year,
            "raw_doi": ref.raw_doi,
            "raw_string": ref.raw_string,
            "position": ref.position,
        }

    def _find_reference_context(
        self,
        reference: dict[str, Any],
        chunks: list[PaperChunk],
    ) -> str | None:
        terms = self._terms(
            " ".join(
                str(reference.get(field) or "")
                for field in ("raw_title", "raw_authors", "raw_year", "raw_doi")
            )
        )[:8]
        for chunk in chunks:
            content = chunk.content or ""
            if terms and any(term in content.lower() for term in terms):
                return self._snippet(content, terms, max_chars=800)
        return None

    @staticmethod
    def _paper_text(paper: Paper, max_chars: int = 8000) -> str:
        parts: list[str] = [paper.title or "", paper.abstract or "", paper.summary or ""]
        for field in (paper.highlights, paper.contributions, paper.limitations):
            if isinstance(field, list):
                parts.extend(str(item) for item in field)
        if paper.parsed_sections:
            for section in paper.parsed_sections[:20]:
                if isinstance(section, dict):
                    parts.append(str(section.get("title") or ""))
                    paragraphs = section.get("paragraphs") or []
                    if isinstance(paragraphs, list):
                        parts.extend(str(item) for item in paragraphs[:4])
        if paper.full_text_markdown:
            parts.append(paper.full_text_markdown[:max_chars])
        return "\n".join(part for part in parts if part)[:max_chars]

    @staticmethod
    def _known_matches(text: str, patterns: Iterable[str]) -> list[str]:
        lowered = text.lower()
        return [pattern for pattern in patterns if pattern.lower() in lowered]

    @staticmethod
    def _result_values(text: str) -> list[dict[str, Any]]:
        values = []
        metric_pattern = "|".join(re.escape(metric) for metric in _METRIC_PATTERNS)
        pattern = re.compile(
            rf"\b(?P<metric>{metric_pattern})\b[^.\n]{{0,80}}?"
            r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>%|points?|x)?",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text[:20000]):
            values.append(
                {
                    "metric": match.group("metric"),
                    "value": float(match.group("value")),
                    "unit": match.group("unit"),
                    "context": match.group(0)[:160],
                }
            )
            if len(values) >= 20:
                break
        return values

    def _sections_for_paper(self, paper: Paper) -> list[dict[str, Any]]:
        if paper.parsed_sections:
            return [
                {
                    "title": section.get("title"),
                    "level": section.get("level"),
                    "paragraphs": section.get("paragraphs") or [],
                    "token_estimate": self._estimate_text_tokens(
                        " ".join(section.get("paragraphs") or [])
                    ),
                }
                for section in paper.parsed_sections
                if isinstance(section, dict)
            ]
        markdown = paper.full_text_markdown or ""
        if not markdown:
            return []
        sections = []
        current = {"title": "Abstract", "level": 1, "paragraphs": []}
        for line in markdown.splitlines():
            heading = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading:
                if current["paragraphs"]:
                    sections.append(current)
                current = {
                    "title": heading.group(2).strip(),
                    "level": len(heading.group(1)),
                    "paragraphs": [],
                }
            elif line.strip():
                current["paragraphs"].append(line.strip())
        if current["paragraphs"]:
            sections.append(current)
        for section in sections:
            section["token_estimate"] = self._estimate_text_tokens(
                " ".join(section["paragraphs"])
            )
        return sections

    @staticmethod
    def _estimate_text_tokens(text: str) -> int:
        return max(1, len(text) // 4) if text else 0

    @staticmethod
    def _split_figures_tables(
        items: list[Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        figures = []
        tables = []
        for item in items:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label") or item.get("ref") or "").lower()
            content_type = str(item.get("content_type") or item.get("type") or "").lower()
            normalized = {**item, "provenance": {"source": "papers.parsed_figures"}}
            if "table" in label or "table" in content_type:
                tables.append(normalized)
            else:
                figures.append(normalized)
        return figures, tables

    def _code_and_data_assets(self, paper: Paper) -> dict[str, Any]:
        links = paper.paper_links or {}
        text = self._paper_text(paper, max_chars=20000)
        urls = [
            url.rstrip(".,;:")
            for url in re.findall(r"https?://[^\s)\]}>,]+", text)
        ]
        code_urls = [url for url in urls if "github.com" in url or "gitlab.com" in url]
        data_urls = [url for url in urls if "zenodo" in url or "figshare" in url]
        return {
            "code_urls": self._dedupe(
                [links.get("code_url"), *(links.get("code_urls") or []), *code_urls]
            ),
            "dataset_urls": self._dedupe(
                [*(links.get("dataset_urls") or []), links.get("dataset_url"), *data_urls]
            ),
            "model_weights_url": links.get("model_weights_url"),
            "project_page_url": links.get("project_page_url"),
            "related_links": links.get("related_links") or {},
            "provenance": {
                "source": "papers.paper_links+text_regex",
                "fetched_at": links.get("fetched_at"),
                "status": links.get("status"),
            },
        }

    def _supplementary_assets(self, paper: Paper) -> list[dict[str, Any]]:
        assets = []
        for item in paper.remote_urls or []:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or ""
            if "supp" in url.lower() or "supplement" in url.lower():
                assets.append(item)
        return assets

    @staticmethod
    def _dedupe(values: Iterable[Any]) -> list[str]:
        return [str(value) for value in dict.fromkeys(v for v in values if v)]

    @staticmethod
    def _paper_summary(paper: Paper) -> dict[str, Any]:
        return {
            "paper_id": str(paper.id),
            "title": paper.title,
            "doi": paper.doi,
            "arxiv_id": paper.arxiv_id,
            "published_at": str(paper.published_at) if paper.published_at else None,
            "created_at": str(paper.created_at) if paper.created_at else None,
            "updated_at": str(paper.updated_at) if paper.updated_at else None,
            "citation_count": paper.citation_count,
            "ingestion_status": paper.ingestion_status,
            "has_full_text": paper.has_full_text,
            "keywords": paper.keywords or [],
        }

    async def _saved_searches(self) -> list[SavedSearch]:
        result = await self.db.execute(
            select(SavedSearch).where(SavedSearch.user_id == self.user_id).limit(200)
        )
        return list(result.scalars().all())

    def _match_saved_searches(
        self,
        papers: list[dict[str, Any]],
        searches: list[SavedSearch],
    ) -> list[dict[str, Any]]:
        matches = []
        for search in searches:
            terms = self._terms(search.query)
            for paper in papers:
                text = " ".join(
                    [paper.get("title") or "", " ".join(paper.get("keywords") or [])]
                )
                if self._score(text, terms) > 0:
                    matches.append(
                        {
                            "subscription_id": str(search.id),
                            "subscription_name": search.name,
                            "paper_id": paper["paper_id"],
                            "score": self._score(text, terms),
                        }
                    )
        return matches

    async def _jsonl_chunks(
        self,
        paper_ids: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        stmt = select(PaperChunk).order_by(PaperChunk.created_at.desc()).limit(limit)
        if paper_ids:
            stmt = stmt.where(PaperChunk.paper_id.in_(paper_ids))
        result = await self.db.execute(stmt)
        return [
            {
                "type": "chunk",
                "data": {
                    "id": str(chunk.id),
                    "paper_id": str(chunk.paper_id),
                    "section_title": chunk.section_title,
                    "content": chunk.content,
                    "order_index": chunk.order_index,
                    "token_estimate": chunk.token_estimate,
                },
            }
            for chunk in result.scalars().all()
        ]

    async def _jsonl_claims(self, paper_ids: list[str], limit: int) -> list[dict[str, Any]]:
        stmt = select(Claim).order_by(Claim.created_at.desc()).limit(limit)
        if paper_ids:
            stmt = stmt.where(Claim.paper_id.in_(paper_ids))
        result = await self.db.execute(stmt)
        return [
            {
                "type": "claim",
                "data": {
                    "id": str(claim.id),
                    "paper_id": str(claim.paper_id),
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "category": claim.category,
                    "confidence": claim.confidence,
                },
            }
            for claim in result.scalars().all()
        ]

    async def _jsonl_citations(
        self,
        paper_ids: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        stmt = select(PaperReference).order_by(PaperReference.position.asc()).limit(limit)
        if paper_ids:
            stmt = stmt.where(PaperReference.citing_paper_id.in_(paper_ids))
        result = await self.db.execute(stmt)
        return [
            {"type": "citation", "data": self._reference_dict(ref)}
            for ref in result.scalars().all()
        ]

    async def _jsonl_experiments(
        self,
        paper_ids: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        stmt = select(Experiment).order_by(Experiment.created_at.desc()).limit(limit)
        if paper_ids:
            stmt = stmt.where(Experiment.paper_id.in_(paper_ids))
        result = await self.db.execute(stmt)
        return [
            {
                "type": "experiment",
                "data": {
                    "id": str(exp.id),
                    "paper_id": str(exp.paper_id) if exp.paper_id else None,
                    "name": exp.name,
                    "description": exp.description,
                    "setup": exp.setup,
                    "parameters": exp.parameters,
                    "results": exp.results,
                    "metrics": exp.metrics,
                    "status": exp.status,
                },
            }
            for exp in result.scalars().all()
        ]

    async def _papers_for_topic(
        self,
        topic: str | None,
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[Paper]:
        if paper_ids:
            return await self._paper_candidates(paper_ids, limit=limit)
        terms = self._terms(topic)
        stmt = select(Paper).where(Paper.deleted_at.is_(None)).order_by(desc(Paper.created_at))
        if terms:
            clauses = []
            for term in terms[:8]:
                like = f"%{term}%"
                clauses.extend([Paper.title.ilike(like), Paper.abstract.ilike(like)])
            stmt = stmt.where(or_(*clauses))
        result = await self.db.execute(stmt.limit(limit))
        return list(result.scalars().all())

    def _paper_node(self, paper: Paper) -> dict[str, Any]:
        summary = self._paper_summary(paper)
        summary["year"] = paper.published_at.year if paper.published_at else None
        summary["summary"] = paper.summary
        summary["contributions"] = paper.contributions or []
        summary["limitations"] = paper.limitations or []
        return summary

    @staticmethod
    def _keyword_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        edges = []
        for idx, left in enumerate(nodes):
            left_keywords = set(str(kw).lower() for kw in left.get("keywords") or [])
            for right in nodes[idx + 1 :]:
                right_keywords = set(str(kw).lower() for kw in right.get("keywords") or [])
                overlap = sorted(left_keywords & right_keywords)
                if overlap:
                    edges.append(
                        {
                            "source": left["paper_id"],
                            "target": right["paper_id"],
                            "type": "keyword_overlap",
                            "weight": len(overlap),
                            "evidence": overlap[:8],
                        }
                    )
        return edges

    @staticmethod
    def _themes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = Counter(
            str(keyword).lower()
            for node in nodes
            for keyword in (node.get("keywords") or [])
            if keyword
        )
        return [
            {"theme": theme, "paper_count": count}
            for theme, count in counts.most_common(12)
        ]

    @staticmethod
    def _claim_like_statements(papers: list[Paper]) -> list[dict[str, Any]]:
        claims = []
        for paper in papers:
            for field_name in ("contributions", "highlights", "limitations"):
                values = getattr(paper, field_name) or []
                if isinstance(values, list):
                    for value in values[:5]:
                        claims.append(
                            {
                                "paper_id": str(paper.id),
                                "paper_title": paper.title,
                                "type": field_name.rstrip("s"),
                                "text": str(value),
                            }
                        )
        return claims[:50]

    async def _reproduction_attempts(self, paper_id: str) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(ReproductionAttempt)
            .where(ReproductionAttempt.paper_id == paper_id)
            .order_by(ReproductionAttempt.created_at.desc())
        )
        return [
            {
                "id": str(attempt.id),
                "status": attempt.status,
                "notes": attempt.notes,
                "code_url": attempt.code_url,
                "created_at": str(attempt.created_at),
            }
            for attempt in result.scalars().all()
        ]

    @staticmethod
    def _reproducibility_flags(
        assets: dict[str, Any],
        attempts: list[dict[str, Any]],
    ) -> list[str]:
        flags = []
        code_data = assets.get("code_and_data") or {}
        if not code_data.get("code_urls"):
            flags.append("missing_code_url")
        if not code_data.get("dataset_urls"):
            flags.append("missing_dataset_url")
        if any(attempt.get("status") == "failed" for attempt in attempts):
            flags.append("failed_reproduction_attempt")
        return flags
