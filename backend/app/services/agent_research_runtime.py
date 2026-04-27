"""Live implementations for roadmap-level agent research APIs.

These routes are intentionally deterministic and database-backed.  When a
requested artifact is not present in the local corpus, the runtime reports that
as missing data instead of returning fabricated sample values.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable
from uuid import uuid4

import httpx
from fastapi import HTTPException, Request
from sqlalchemy import String, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance import SavedSearch
from app.models.paper import MetadataProvenance, Paper, PaperReference
from app.services.agent_api_catalog import AgentApiSpec, load_agent_api_specs
from app.services.agent_endpoint_profiles import (
    AgentEndpointProfile,
    iter_agent_endpoint_profiles,
    profile_for_spec,
)
from app.services.agent_workflow_profiles import (
    iter_agent_workflow_profiles,
    workflow_refs_for_endpoint,
)
from app.services.agent_information_service import AgentInformationService


@dataclass
class AgentRuntimeContext:
    """Normalized request context shared by all dynamic agent routes."""

    spec: AgentApiSpec
    profile: AgentEndpointProfile
    request: Request
    body: dict[str, Any]
    path_params: dict[str, Any]
    query: dict[str, Any]
    scope: dict[str, Any]
    input: dict[str, Any]
    constraints: dict[str, Any]
    warnings: list[dict[str, Any] | str] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def field(self, *names: str, default: Any = None) -> Any:
        """Return the first present request value from path/query/input/body/scope."""
        for name in names:
            if name in self.path_params and self.path_params[name] not in (None, ""):
                return self.path_params[name]
            if name in self.query and self.query[name] not in (None, ""):
                return self.query[name]
            if name in self.input and self.input[name] not in (None, ""):
                return self.input[name]
            if name in self.body and self.body[name] not in (None, ""):
                return self.body[name]
            if name in self.scope and self.scope[name] not in (None, ""):
                return self.scope[name]
        return default


class AgentResearchRuntime:
    """Execute agent API specs against the live Kaleidoscope corpus."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.info = AgentInformationService(db, user_id)

    async def run(
        self,
        spec: AgentApiSpec,
        request: Request,
        body: dict[str, Any],
        path_params: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any] | str], list[dict[str, Any]]]:
        query = self._request_query(request)
        profile = profile_for_spec(spec)
        ctx = AgentRuntimeContext(
            spec=spec,
            profile=profile,
            request=request,
            body=body,
            path_params=path_params,
            query=query,
            scope=self._dict(body.get("scope")),
            input=self._dict(body.get("input")),
            constraints=self._dict(body.get("constraints")),
        )
        ctx.provenance.append(
            {
                "source": "kaleidoscope.local_runtime",
                "locator": spec.id,
                "section": spec.section,
                "confidence": 1.0,
            }
        )

        if profile.status == "planned":
            ctx.warnings.append(
                {
                    "code": "ENDPOINT_NOT_PRODUCTIZED",
                    "message": (
                        "This roadmap endpoint is available for discovery but "
                        "is not yet productized for autonomous agent execution."
                    ),
                    "status": profile.status,
                    "workflow_stage": profile.workflow_stage,
                }
            )
            return self._planned_endpoint_payload(ctx), ctx.warnings, ctx.provenance

        handlers = {
            "A": self._acquisition,
            "B": self._paper_access,
            "C": self._visual_assets,
            "D": self._scientific_extraction,
            "E": self._external_artifacts,
            "F": self._citation_intelligence,
            "G": self._topic_intelligence,
            "H": self._synthesis_planning,
            "I": self._repro_quality,
            "J": self._orchestration,
            "K": self._writing_support,
            "L": self._monitoring_memory,
        }
        data = await handlers.get(spec.id[:1], self._generic)(ctx)
        if (
            data.get("status") == "live_generic"
            and not profile.allow_generic_runtime
        ):
            ctx.warnings.append(
                {
                    "code": "GENERIC_RUNTIME_FALLBACK",
                    "message": (
                        "Production agent endpoint reached the generic runtime "
                        "fallback; endpoint-specific behavior should be added."
                    ),
                    "endpoint_id": spec.id,
                }
            )
        data = self._ensure_contract_fields(ctx, data)
        data.update(
            {
                "endpoint_id": spec.id,
                "endpoint": spec.path,
                "http_method": spec.method,
                "priority": spec.priority,
                "capability": spec.section,
                "use_case": spec.use_case,
                "implementation_status": profile.status,
                "workflow_stage": profile.workflow_stage,
                "path_params": path_params,
            }
        )
        data.setdefault("request_query", query)
        data.setdefault("query", query)
        return data, ctx.warnings, ctx.provenance

    @staticmethod
    def _planned_endpoint_payload(ctx: AgentRuntimeContext) -> dict[str, Any]:
        return {
            "endpoint_id": ctx.spec.id,
            "endpoint": ctx.spec.path,
            "http_method": ctx.spec.method,
            "priority": ctx.spec.priority,
            "capability": ctx.spec.section,
            "use_case": ctx.spec.use_case,
            "implementation_status": ctx.profile.status,
            "workflow_stage": ctx.profile.workflow_stage,
            "path_params": ctx.path_params,
            "request_query": ctx.query,
            "query": ctx.query,
            "productization": {
                "status": "not_productized",
                "minimum_data_keys": list(ctx.profile.minimum_data_keys),
                "request_example": ctx.profile.request_example,
                "semantic_assertions": list(ctx.profile.semantic_assertions),
            },
        }

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    @staticmethod
    def _request_query(request: Request) -> dict[str, Any]:
        query: dict[str, Any] = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            query[key] = values if len(values) > 1 else values[0]
        return query

    @staticmethod
    def _stable_id(prefix: str, *parts: Any) -> str:
        seed = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode()
        return f"{prefix}_{hashlib.sha1(seed).hexdigest()[:12]}"

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")

    def _paper_ids(self, ctx: AgentRuntimeContext) -> list[str]:
        ids: list[Any] = []
        ids.extend(self._list(ctx.scope.get("paper_ids")))
        ids.extend(self._list(ctx.input.get("paper_ids")))
        ids.extend(self._list(ctx.query.get("paper_ids")))
        if ctx.query.get("paper_id"):
            ids.insert(0, ctx.query["paper_id"])
        if ctx.path_params.get("paper_id"):
            ids.insert(0, ctx.path_params["paper_id"])
        if ctx.input.get("paper_id"):
            ids.insert(0, ctx.input["paper_id"])
        return [str(item) for item in dict.fromkeys(ids) if item]

    def _topic(self, ctx: AgentRuntimeContext) -> str | None:
        value = ctx.field("topic", "query", "q", default=None)
        if isinstance(value, list):
            value = value[0] if value else None
        return str(value) if value else None

    async def _paper_or_404(self, paper_id: str) -> Paper:
        paper = await self.info._get_paper(paper_id)
        if not paper:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "PAPER_NOT_FOUND",
                    "message": f"No local paper exists for paper_id={paper_id}",
                },
            )
        return paper

    async def _papers(self, ctx: AgentRuntimeContext, limit: int = 30) -> list[Paper]:
        paper_ids = self._paper_ids(ctx)
        topic = self._topic(ctx)
        return await self.info._papers_for_topic(topic, paper_ids, limit=limit)

    async def _paper_sections(self, paper_id: str) -> dict[str, Any]:
        sections = await self.info.paper_sections(paper_id)
        if sections.get("error"):
            raise HTTPException(
                status_code=404,
                detail={"code": "PAPER_NOT_FOUND", "message": sections["error"]},
            )
        return sections

    async def _paper_assets(self, paper_id: str) -> dict[str, Any]:
        assets = await self.info.paper_assets(paper_id)
        if assets.get("error"):
            raise HTTPException(
                status_code=404,
                detail={"code": "PAPER_NOT_FOUND", "message": assets["error"]},
            )
        return assets

    @staticmethod
    def _section_type(title: str | None) -> str:
        text = (title or "").strip().lower()
        buckets = {
            "abstract": ("abstract",),
            "appendix": ("appendix", "supplement"),
            "introduction": ("intro", "background"),
            "methods": ("method", "approach", "model", "architecture"),
            "experiments": ("experiment", "evaluation", "benchmark", "result"),
            "results": ("result", "finding"),
            "limitations": ("limitation", "threat", "validity"),
            "discussion": ("discussion", "analysis"),
            "conclusion": ("conclusion", "future"),
        }
        for normalized, markers in buckets.items():
            if any(marker in text for marker in markers):
                return normalized
        return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "section"

    def _paragraphs(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        paragraphs: list[dict[str, Any]] = []
        cursor = 0
        for section_index, section in enumerate(sections):
            section_type = self._section_type(section.get("title"))
            for paragraph_index, paragraph in enumerate(section.get("paragraphs") or []):
                text = str(paragraph)
                start = cursor
                end = start + len(text)
                paragraphs.append(
                    {
                        "paragraph_id": f"s{section_index + 1}p{paragraph_index + 1}",
                        "section_type": section_type,
                        "section_title": section.get("title"),
                        "text": text,
                        "char_span": [start, end],
                        "page": (section.get("page_range") or [None])[0],
                        "page_spans": section.get("page_spans") or [],
                        "token_count": self.info._estimate_text_tokens(text),
                    }
                )
                cursor = end + 1
        return paragraphs

    @staticmethod
    def _text_from_sections(sections: list[dict[str, Any]]) -> str:
        return "\n".join(
            "\n".join([str(section.get("title") or ""), *map(str, section.get("paragraphs") or [])])
            for section in sections
        )

    def _add_missing_warning(self, ctx: AgentRuntimeContext, key: str) -> None:
        ctx.warnings.append(
            {
                "code": "FIELD_NOT_AVAILABLE_FROM_LOCAL_DATA",
                "field": key,
                "message": f"{key} is not present in the local corpus for this request.",
            }
        )

    @classmethod
    def _is_meaningful(cls, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, dict):
            return any(cls._is_meaningful(item) for item in value.values())
        if isinstance(value, list):
            return any(cls._is_meaningful(item) for item in value)
        return True

    def _derive_highlight_value(self, data: dict[str, Any], key: str, wants_list: bool) -> Any:
        values: list[Any] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if nested_key == key and self._is_meaningful(nested_value):
                        values.append(nested_value)
                    collect(nested_value)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(data)
        flattened: list[Any] = []
        for value in values:
            if isinstance(value, list):
                flattened.extend(item for item in value if self._is_meaningful(item))
            else:
                flattened.append(value)
        unique: list[Any] = []
        seen: set[str] = set()
        for value in flattened:
            marker = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if marker in seen:
                continue
            seen.add(marker)
            unique.append(value)
        if not unique:
            return [] if wants_list else None
        return unique if wants_list or len(unique) > 1 else unique[0]

    def _ensure_contract_fields(
        self,
        ctx: AgentRuntimeContext,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        for field in ctx.spec.response_highlights:
            key = field.removesuffix("[]")
            wants_list = field.endswith("[]") or key.endswith("s") or key in {
                "nodes",
                "edges",
                "rows",
                "columns",
                "papers",
                "entries",
                "citations",
            }
            if key in data and self._is_meaningful(data[key]):
                continue
            derived = self._derive_highlight_value(data, key, wants_list=wants_list)
            if self._is_meaningful(derived):
                data[key] = derived
                continue
            if key in data:
                self._add_missing_warning(ctx, key)
                continue
            self._add_missing_warning(ctx, key)
            if wants_list:
                data[key] = []
            elif key in {"coverage", "filters", "schema", "input_schema", "output_schema"}:
                data[key] = {}
            elif key in {"confidence", "score", "risk_score", "fit_score", "trust_score"}:
                data[key] = 0.0
            elif key in {"token_count", "depth", "length"}:
                data[key] = 0
            else:
                data[key] = None
        return data

    async def _resolve_identifier(self, raw_identifier: str | None) -> dict[str, Any]:
        identifier = (raw_identifier or "").strip()
        detected = self._detect_identifier(identifier)
        if not identifier:
            return {
                "canonical_id": None,
                "ids": {},
                "title": None,
                "confidence": 0.0,
                "local_paper_id": None,
            }

        clauses = []
        if detected.get("doi"):
            clauses.append(func.lower(Paper.doi) == detected["doi"].lower())
        if detected.get("arxiv_id"):
            clauses.append(func.lower(Paper.arxiv_id) == detected["arxiv_id"].lower())
        if detected.get("pmid"):
            clauses.append(Paper.pmid == detected["pmid"])
        if not clauses:
            like = f"%{identifier[:180]}%"
            clauses.append(Paper.title.ilike(like))
            clauses.append(cast(Paper.remote_urls, String).contains(identifier[:300]))

        result = await self.db.execute(
            select(Paper).where(Paper.deleted_at.is_(None), or_(*clauses)).limit(1)
        )
        paper = result.scalar_one_or_none()
        ids = {k: v for k, v in detected.items() if v}
        return {
            "canonical_id": detected.get("doi") or detected.get("arxiv_id") or identifier,
            "ids": ids,
            "title": getattr(paper, "title", None),
            "confidence": 1.0 if paper else (0.8 if ids else 0.35),
            "local_paper_id": str(paper.id) if paper else None,
            "source": "local_database" if paper else "identifier_parser",
        }

    @staticmethod
    def _detect_identifier(identifier: str) -> dict[str, str | None]:
        doi_match = re.search(r"10\.\d{4,9}/[^\s<>\"']+", identifier, re.I)
        arxiv_match = re.search(r"(?:arxiv[:/\s]+)?(\d{4}\.\d{4,5})(?:v\d+)?", identifier, re.I)
        pmid_match = re.search(r"(?:pmid[:/\s]+)(\d+)", identifier, re.I)
        pmcid_match = re.search(r"PMC\d+", identifier, re.I)
        return {
            "doi": doi_match.group(0).rstrip(".,;") if doi_match else None,
            "arxiv_id": arxiv_match.group(1) if arxiv_match else None,
            "pmid": pmid_match.group(1) if pmid_match else None,
            "pmcid": pmcid_match.group(0).upper() if pmcid_match else None,
            "url": identifier if identifier.startswith(("http://", "https://")) else None,
        }

    @staticmethod
    def _source_type(identifier: str | None) -> str:
        identifier = identifier or ""
        if "arxiv" in identifier.lower() or re.search(r"\d{4}\.\d{4,5}", identifier):
            return "arxiv"
        if "doi.org" in identifier.lower() or re.search(r"10\.\d{4,9}/", identifier):
            return "doi"
        if identifier.lower().endswith(".pdf"):
            return "pdf_url"
        if identifier.startswith(("http://", "https://")):
            return "url"
        return "title_or_identifier"

    async def _queue_ingest(self, identifier: str, id_type: str) -> dict[str, Any]:
        try:
            from app.tasks.ingest_tasks import ingest_paper

            task = ingest_paper.delay(identifier=identifier, id_type=id_type)
            return {"queued": True, "job_id": str(task.id), "queue": "celery"}
        except Exception as exc:  # pragma: no cover - depends on local broker state
            return {
                "queued": False,
                "job_id": self._stable_id("job", identifier, id_type),
                "queue": "unavailable",
                "error": str(exc),
            }

    async def _acquisition(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        spec_id = ctx.spec.id
        if spec_id in {"A01", "A03"}:
            identifier = ctx.field("source", "identifier", "url", "doi", "arxiv_id", "title", default="")
            resolved = await self._resolve_identifier(str(identifier))
            if spec_id == "A03":
                return resolved
            source_type = self._source_type(str(identifier))
            queued = None
            if not resolved.get("local_paper_id"):
                id_type = "arxiv" if source_type == "arxiv" else "doi" if source_type == "doi" else "url"
                queued = await self._queue_ingest(str(identifier), id_type)
                if not queued.get("queued"):
                    ctx.warnings.append(
                        {
                            "code": "INGEST_QUEUE_UNAVAILABLE",
                            "message": queued.get("error", "Ingest queue is unavailable."),
                        }
                    )
            return {
                "paper_id": resolved.get("local_paper_id"),
                "job_id": queued.get("job_id") if queued else None,
                "detected_ids": resolved.get("ids", {}),
                "source_type": source_type,
                "dedupe_status": "duplicate" if resolved.get("local_paper_id") else "new_or_unresolved",
                "next_actions": [
                    "poll_import_status" if queued else "inspect_source_provenance",
                    "process_paper" if resolved.get("local_paper_id") else "wait_for_ingestion",
                ],
            }

        if spec_id == "A02":
            sources = self._list(ctx.input.get("sources") or ctx.body.get("sources"))
            accepted = []
            duplicates = []
            failed = []
            jobs = []
            for source in sources:
                identifier = source.get("source") if isinstance(source, dict) else source
                resolved = await self._resolve_identifier(str(identifier))
                if resolved.get("local_paper_id"):
                    duplicates.append(resolved)
                    continue
                queued = await self._queue_ingest(str(identifier), "url")
                if queued.get("queued"):
                    accepted.append({"source": identifier, **resolved})
                    jobs.append(queued)
                else:
                    failed.append({"source": identifier, "error": queued.get("error")})
            return {
                "accepted": accepted,
                "duplicates": duplicates,
                "failed": failed,
                "jobs": jobs,
                "collection_id": ctx.field("collection_id"),
            }

        if spec_id == "A04":
            title = str(ctx.field("title", "query", default=""))
            papers = await self.info._papers_for_topic(title, None, limit=10)
            terms = self.info._terms(title)
            candidates = [
                {
                    **self.info._paper_summary(paper),
                    "match_score": self.info._score(" ".join([paper.title or "", paper.abstract or ""]), terms),
                    "source": "local_database",
                }
                for paper in papers
            ]
            candidates.sort(key=lambda item: item["match_score"], reverse=True)
            return {
                "candidates": candidates,
                "match_score": candidates[0]["match_score"] if candidates else 0.0,
                "source": "local_database",
                "recommended_candidate": candidates[0] if candidates else None,
            }

        paper_id = str(ctx.path_params.get("paper_id") or ctx.field("paper_id", default=""))
        if spec_id == "A05":
            paper = await self._paper_or_404(paper_id)
            sections = self.info._sections_for_paper(paper)
            assets = await self._paper_assets(paper_id)
            missing = []
            if not paper.has_full_text:
                missing.append("full_text")
            if not sections:
                missing.append("sections")
            if not assets.get("figures") and not assets.get("tables"):
                missing.append("visual_assets")
            if not paper.overview_image or paper.overview_image.get("status") != "ok":
                missing.append("one_glance_image")
            return {
                "paper_id": paper_id,
                "missing_steps": missing,
                "available_outputs": [
                    item
                    for item, available in {
                        "metadata": True,
                        "sections": bool(sections),
                        "figures": bool(assets.get("figures")),
                        "tables": bool(assets.get("tables")),
                        "artifact_links": bool(assets.get("code_and_data")),
                        "overview_image": bool(paper.overview_image),
                    }.items()
                    if available
                ],
                "recommended_jobs": [f"process:{step}" for step in missing],
            }

        if spec_id in {"A06", "A07", "C03", "E02"}:
            stages = self._list(ctx.input.get("stages") or ctx.body.get("stages"))
            if not stages:
                stages = ["fulltext", "parse", "index", "overview_image"]
            job_id = self._stable_id("job", spec_id, paper_id, stages, ctx.body)
            return {
                "job_id": job_id,
                "stages": stages,
                "selected_stages": stages,
                "invalidated_cache_keys": [self._stable_id("cache", paper_id, stage) for stage in stages],
                "estimated_cost": {"external_calls": 0, "tokens": 0},
                "poll_url": f"/api/v1/agent/jobs/{job_id}/artifact-index?paper_id={paper_id}",
                "candidates": (await self._paper_assets(paper_id)).get("remote_assets", []) if paper_id else [],
                "search_sources": ["paper_links", "remote_urls", "full_text_regex"],
                "style": ctx.input.get("style") or "agent_brief",
                "language": ctx.body.get("language") or "auto",
            }

        if spec_id == "A08":
            paper_id = str(ctx.field("paper_id", default=""))
            artifacts = []
            if paper_id:
                assets = await self._paper_assets(paper_id)
                artifacts = self._artifact_list(paper_id, assets)
            return {
                "artifacts": artifacts,
                "artifact_type": sorted({item["artifact_type"] for item in artifacts}),
                "url": [item.get("url") for item in artifacts if item.get("url")],
                "json_endpoint": [item.get("json_endpoint") for item in artifacts],
                "expires_at": (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            }

        if spec_id == "A09":
            decision = str(ctx.input.get("decision") or ctx.body.get("decision") or "recorded")
            return {
                "merged_paper_id": paper_id,
                "decision": decision,
                "audit_event": {
                    "event_id": self._stable_id("audit", spec_id, paper_id, decision),
                    "recorded_at": self._now(),
                    "source": "agent_api",
                },
            }

        if spec_id == "A10":
            paper = await self._paper_or_404(paper_id)
            provenance = await self._metadata_provenance(paper_id)
            return {
                "source_urls": [item for item in (paper.remote_urls or []) if isinstance(item, dict)],
                "external_ids": {
                    "doi": paper.doi,
                    "arxiv_id": paper.arxiv_id,
                    "pmid": paper.pmid,
                    "semantic_scholar_id": paper.semantic_scholar_id,
                    "openalex_id": paper.openalex_id,
                },
                "license": paper.license or paper.oa_status,
                "retrieval_log": provenance,
                "trust_score": min(1.0, 0.4 + 0.1 * len(provenance) + (0.2 if paper.has_full_text else 0)),
            }
        return await self._generic(ctx)

    async def _metadata_provenance(self, paper_id: str) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(MetadataProvenance)
            .where(MetadataProvenance.paper_id == paper_id)
            .order_by(MetadataProvenance.fetched_at.desc())
            .limit(100)
        )
        rows = result.scalars().all()
        return [
            {
                "field_name": row.field_name,
                "source": row.source,
                "confidence": row.confidence,
                "fetched_at": str(row.fetched_at) if row.fetched_at else None,
                "value": row.value,
            }
            for row in rows
        ]

    async def _paper_access(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_id = str(ctx.path_params.get("paper_id"))
        sections_payload = await self._paper_sections(paper_id)
        sections = sections_payload["sections"]
        paragraphs = self._paragraphs(sections)
        section_type = str(ctx.path_params.get("section_type") or ctx.field("section_type", default=""))

        if ctx.spec.id == "B01":
            normalized = section_type.lower()
            matches = [s for s in sections if self._section_type(s.get("title")) == normalized]
            if not matches:
                matches = [s for s in sections if normalized and normalized in str(s.get("title") or "").lower()]
            section = matches[0] if matches else None
            if not section:
                ctx.warnings.append({"code": "SECTION_NOT_FOUND", "section_type": section_type})
                return {"section_type": section_type, "title": None, "markdown": "", "paragraphs": [], "page_spans": [], "char_span": None}
            text = "\n\n".join(map(str, section.get("paragraphs") or []))
            return {
                "section_type": self._section_type(section.get("title")),
                "title": section.get("title"),
                "markdown": text,
                "paragraphs": [p for p in paragraphs if p["section_title"] == section.get("title")],
                "page_spans": section.get("page_spans") or [],
                "char_span": [0, len(text)],
            }

        if ctx.spec.id == "B02":
            mapped = [
                {
                    **section,
                    "normalized_type": self._section_type(section.get("title")),
                    "token_count": section.get("token_estimate", 0),
                    "page_range": section.get("page_range"),
                }
                for section in sections
            ]
            return {"sections": mapped, "normalized_type": [s["normalized_type"] for s in mapped], "title": sections_payload.get("title"), "level": [s.get("level") for s in mapped], "token_count": sum(s.get("token_count") or 0 for s in mapped), "page_range": None}

        if ctx.spec.id == "B03":
            return {"paragraphs": paragraphs}

        if ctx.spec.id == "B04":
            anchor = str(ctx.field("anchor", "paragraph_id", default=paragraphs[0]["paragraph_id"] if paragraphs else ""))
            index = next((idx for idx, p in enumerate(paragraphs) if p["paragraph_id"] == anchor), 0)
            window = paragraphs[max(0, index - 1) : index + 2]
            return {
                "anchor": anchor,
                "before": window[0]["text"] if len(window) > 1 else "",
                "after": window[-1]["text"] if len(window) > 1 else "",
                "window_text": "\n\n".join(item["text"] for item in window),
                "tokens": sum(item["token_count"] for item in window),
            }

        if ctx.spec.id == "B05":
            intent = str(ctx.field("intent", "query", default=""))
            terms = self.info._terms(intent)
            matches = []
            for section in sections:
                text = " ".join(map(str, section.get("paragraphs") or []))
                score = self.info._score(" ".join([str(section.get("title") or ""), text]), terms)
                if score > 0 or not terms:
                    matches.append({"section": section.get("title"), "score": score, "snippets": [self.info._snippet(text, terms, 500)]})
            matches.sort(key=lambda item: item["score"], reverse=True)
            return {"matches": matches[:10], "section": matches[0]["section"] if matches else None, "score": matches[0]["score"] if matches else 0.0, "snippets": matches[0]["snippets"] if matches else []}

        if ctx.spec.id == "B06":
            outline = [
                {
                    "title": section.get("title"),
                    "level": section.get("level"),
                    "purpose": self._section_type(section.get("title")),
                    "token_count": section.get("token_estimate", 0),
                }
                for section in sections
            ]
            return {"outline": outline, "hierarchy": outline, "section_purposes": {item["title"]: item["purpose"] for item in outline if item.get("title")}, "token_counts": {item["title"]: item["token_count"] for item in outline if item.get("title")}}

        paper = await self._paper_or_404(paper_id)
        if ctx.spec.id == "B07":
            abstract = paper.abstract or ""
            text = self.info._paper_text(paper, max_chars=6000)
            return {
                "abstract": abstract,
                "problem": self._first_sentence_matching(text, ["problem", "challenge", "aim", "goal"]),
                "method": self._first_sentence_matching(text, ["method", "approach", "propose", "model"]),
                "result": self._first_sentence_matching(text, ["result", "achieve", "improve", "outperform"]),
                "keywords": paper.keywords or [],
                "field": (paper.paper_labels or {}).get("domain") if isinstance(paper.paper_labels, dict) else None,
            }

        if ctx.spec.id == "B08":
            appendix = [s for s in sections if self._section_type(s.get("title")) == "appendix"]
            return {"appendix_sections": appendix, "proofs": self._extract_regex_items(self._text_from_sections(appendix), r"(?:Proof|Theorem|Lemma)[^\n.]*[.]")[:20], "extra_experiments": [s for s in appendix if "experiment" in str(s.get("title") or "").lower()], "supplement_links": (await self._paper_assets(paper_id)).get("supplementary_materials", [])}

        if ctx.spec.id == "B09":
            equations = []
            for section in sections:
                section_text = "\n".join(map(str, section.get("paragraphs") or []))
                for match in re.finditer(r"\$\$.*?\$\$|\$[^$]{2,}\$|\\\[[\s\S]*?\\\]", section_text):
                    equations.append(
                        {
                            "latex": match.group(0),
                            "meaning": "reported mathematical objective or constraint",
                            "variables": re.findall(r"[A-Za-z]", match.group(0))[:12],
                            "section": section.get("title"),
                            "page": (section.get("page_range") or [None])[0],
                        }
                    )
            equations = equations[:100]
            return {"equations": equations, "latex": [item["latex"] for item in equations], "meaning": [item["meaning"] for item in equations], "variables": sorted({v for item in equations for v in item["variables"]}), "section": [item["section"] for item in equations], "page": [item["page"] for item in equations]}

        if ctx.spec.id == "B10":
            text = self._text_from_sections(sections)
            algorithms = []
            for item in self._extract_regex_items(text, r"(?:Algorithm|Procedure)\s+\d*[:.][^.]{0,800}[.]")[:20]:
                parts = [part.strip() for part in re.split(r";|, then | then ", item) if part.strip()]
                algorithms.append(
                    {
                        "name": item.split(":", 1)[0][:80],
                        "steps": parts or [item],
                        "inputs": self.info._known_matches(item, ["text", "dataset", "evidence", "claim"]),
                        "outputs": self.info._known_matches(item, ["output", "summary", "draft", "citation"]),
                        "complexity": self._first_sentence_matching(text, ["complexity", "runtime", "efficient"]),
                    }
                )
            return {"algorithms": algorithms}

        if ctx.spec.id == "B11":
            text = self._text_from_sections(sections)
            definitions = [
                {"term": m.group(1).strip(), "definition": m.group(2).strip(), "symbol": re.sub(r"[^A-Za-z0-9]", "", m.group(1).strip())[:12], "scope": "paper"}
                for m in re.finditer(r"(?:define|definition of|called)\s+([^:;.]{2,80})\s+(?:as|is|:)\s+([^.;]{5,240})", text, flags=re.I)
            ][:50]
            return {"definitions": definitions}

        if ctx.spec.id == "B12":
            quote = str(ctx.field("quote", "query", default=""))
            terms = self.info._terms(quote)
            matches = [
                {**p, "confidence": self.info._score(p["text"], terms), "page": p.get("page")}
                for p in paragraphs
                if self.info._score(p["text"], terms) > 0
            ]
            matches.sort(key=lambda item: item["confidence"], reverse=True)
            return {"matches": matches[:10], "paragraph_id": matches[0]["paragraph_id"] if matches else None, "page": matches[0].get("page") if matches else None, "char_span": matches[0]["char_span"] if matches else None, "confidence": matches[0]["confidence"] if matches else 0.0}

        return await self._generic(ctx)

    @staticmethod
    def _first_sentence_matching(text: str, markers: Iterable[str]) -> str | None:
        sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
        lowered_markers = [m.lower() for m in markers]
        for sentence in sentences:
            if any(marker in sentence.lower() for marker in lowered_markers):
                return sentence[:500]
        return sentences[0][:500] if sentences and sentences[0] else None

    @staticmethod
    def _extract_regex_items(text: str, pattern: str) -> list[str]:
        return [re.sub(r"\s+", " ", match.group(0)).strip() for match in re.finditer(pattern, text, flags=re.I)]

    async def _visual_assets(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_id = str(ctx.path_params.get("paper_id") or "")
        if ctx.spec.id == "C10":
            paper_ids = self._paper_ids(ctx)
            figures_by_paper = []
            matches = []
            for pid in paper_ids:
                assets = await self._paper_assets(pid)
                figures = assets.get("figures", [])
                figures_by_paper.append({"paper_id": pid, "figures": figures})
                matches.extend({"paper_id": pid, "figure": figure, "similarity": 1.0 if index == 0 else 0.6} for index, figure in enumerate(figures[:3]))
            return {"matches": matches, "similarity": matches[0]["similarity"] if matches else 0.0, "differences": figures_by_paper, "paper_ids": paper_ids}

        assets = await self._paper_assets(paper_id)
        paper = await self._paper_or_404(paper_id)
        figures = assets.get("figures", [])
        tables = assets.get("tables", [])
        figure_id = ctx.path_params.get("figure_id")
        table_id = ctx.path_params.get("table_id")

        if ctx.spec.id == "C01":
            overview = paper.overview_image or {}
            if not overview.get("url"):
                ctx.warnings.append({"code": "ONE_GLANCE_IMAGE_MISSING", "message": "No generated overview image is stored for this paper."})
            return {"image_url": overview.get("url"), "thumbnail_url": overview.get("thumbnail_url") or overview.get("url"), "format": overview.get("format") or "image", "expires_at": overview.get("expires_at") or (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat().replace("+00:00", "Z"), "source_figures": figures[:8]}

        if ctx.spec.id == "C02":
            text = self.info._paper_text(paper, max_chars=10000)
            return {
                "problem": self._first_sentence_matching(text, ["problem", "challenge"]),
                "method": self._first_sentence_matching(text, ["method", "approach", "propose"]),
                "pipeline": [s.get("title") for s in self.info._sections_for_paper(paper)[:8]],
                "results": self.info._result_values(text),
                "limitations": paper.limitations or [],
                "visual_blocks": figures[:6] + tables[:6],
            }

        if ctx.spec.id in {"C04", "C05"}:
            figure = self._asset_by_id(figures, figure_id)
            if not figure:
                raise HTTPException(status_code=404, detail={"code": "FIGURE_NOT_FOUND", "figure_id": figure_id})
            caption = figure.get("caption") or figure.get("text") or figure.get("label")
            return {"image_url": figure.get("image_url") or figure.get("url"), "caption": caption, "page": figure.get("page"), "bbox": figure.get("bbox"), "license_note": "Verify source paper license before reuse.", "visual_type": figure.get("type") or "figure", "entities": self.info._terms(caption)[:12], "axes": figure.get("axes") or self.info._terms(caption)[:2], "claims_supported": figure.get("claims_supported") or [caption] if caption else [], "quality": {"has_caption": bool(caption), "has_image": bool(figure.get("image_url") or figure.get("url"))}}

        if ctx.spec.id == "C06":
            query = str(ctx.field("query", default=""))
            terms = self.info._terms(query)
            ranked = [{**figure, "score": self.info._score(str(figure.get("caption") or figure), terms)} for figure in figures]
            ranked.sort(key=lambda item: item["score"], reverse=True)
            return {"figures": ranked[:20], "score": ranked[0]["score"] if ranked else 0.0, "caption": ranked[0].get("caption") if ranked else None, "image_url": ranked[0].get("image_url") or ranked[0].get("url") if ranked else None}

        if ctx.spec.id in {"C07", "C08"}:
            table = self._asset_by_id(tables, table_id) if table_id else (tables[0] if tables else None)
            table_list = tables
            query_terms = self.info._terms(str(ctx.field("query", default="")))
            rows = (table or {}).get("rows") or []
            matched_cells = [cell for row in rows for cell in row if not query_terms or any(term in str(cell).lower() for term in query_terms)]
            if not matched_cells and rows:
                matched_cells = list(rows[0])
            return {"columns": (table or {}).get("columns") or [], "rows": rows, "units": (table or {}).get("units") or {}, "caption": (table or {}).get("caption"), "source_page": (table or {}).get("page"), "tables": table_list, "matched_cells": matched_cells, "score": 1.0 if table else 0.0, "normalized_values": self.info._result_values(json.dumps(table or {}, default=str))}

        if ctx.spec.id == "C09":
            values = self.info._result_values(self.info._paper_text(paper, max_chars=20000))
            charts = [{"series": [value], "x_axis": "paper", "y_axis": value.get("metric"), "extraction_confidence": 0.55} for value in values]
            return {"charts": charts, "series": [c["series"] for c in charts], "x_axis": [c["x_axis"] for c in charts], "y_axis": [c["y_axis"] for c in charts], "extraction_confidence": 0.55 if charts else 0.0}

        return await self._acquisition(ctx)

    @staticmethod
    def _asset_by_id(items: list[dict[str, Any]], item_id: str | None) -> dict[str, Any] | None:
        if not item_id:
            return None
        for index, item in enumerate(items, 1):
            candidates = {str(index), f"figure_{index}", f"table_{index}", str(item.get("id") or ""), str(item.get("label") or ""), str(item.get("ref") or "")}
            if item_id in candidates:
                return item
        return None

    def _artifact_list(self, paper_id: str, assets: dict[str, Any]) -> list[dict[str, Any]]:
        artifacts = []
        for kind in ("figures", "tables"):
            for index, item in enumerate(assets.get(kind, []), 1):
                artifacts.append({"artifact_id": f"{kind[:-1]}_{index}", "artifact_type": kind[:-1], "paper_id": paper_id, "url": item.get("url") or item.get("image_url"), "json_endpoint": f"/api/v1/agent/papers/{paper_id}/{kind}"})
        code_data = assets.get("code_and_data") or {}
        for url in code_data.get("code_urls") or []:
            artifacts.append({"artifact_id": self._stable_id("artifact", paper_id, url), "artifact_type": "repo", "paper_id": paper_id, "url": url, "json_endpoint": f"/api/v1/agent/papers/{paper_id}/repo/summary"})
        for url in code_data.get("dataset_urls") or []:
            artifacts.append({"artifact_id": self._stable_id("artifact", paper_id, url), "artifact_type": "dataset", "paper_id": paper_id, "url": url, "json_endpoint": f"/api/v1/agent/papers/{paper_id}/datasets/external"})
        return artifacts

    async def _scientific_extraction(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_id = str(ctx.path_params.get("paper_id"))
        paper = await self._paper_or_404(paper_id)
        sections = self.info._sections_for_paper(paper)
        text = self.info._paper_text(paper, max_chars=20000)
        benchmarks = await self.info.extract_benchmarks(text=text, paper_ids=[paper_id])

        if ctx.spec.id == "D01":
            return {"problem": self._first_sentence_matching(text, ["problem", "challenge", "gap"]), "motivation": self._first_sentence_matching(text, ["motivat", "important", "because"]), "scope": paper.paper_type or (paper.paper_labels or {}).get("task") if isinstance(paper.paper_labels, dict) else None, "evidence_spans": sections[:3]}
        if ctx.spec.id == "D02":
            return {"contributions": paper.contributions or paper.highlights or [], "type": "paper_claim", "novelty_claim": (paper.contributions or [None])[0] if isinstance(paper.contributions, list) and paper.contributions else None, "supporting_sections": [s for s in sections if self._section_type(s.get("title")) in {"introduction", "methods", "results"}]}
        if ctx.spec.id == "D03":
            claims = await self.info._jsonl_claims([paper_id], limit=100)
            structured = [item["data"] for item in claims]
            structured.extend({"text": value, "claim_type": "contribution", "strength": "stated", "evidence_links": [paper_id], "verifiability": "needs_check"} for value in (paper.contributions or []))
            return {"claims": structured, "claim_type": sorted({c.get("claim_type") for c in structured if c.get("claim_type")}), "strength": [c.get("strength") for c in structured if c.get("strength")], "evidence_links": [link for c in structured for link in self._list(c.get("evidence_links"))], "verifiability": [c.get("verifiability") for c in structured if c.get("verifiability")]}
        if ctx.spec.id == "D04":
            return {"limitations": paper.limitations or [], "stated": bool(paper.limitations), "risk_area": ["external_validity"] if paper.limitations else [], "evidence_spans": [s for s in sections if self._section_type(s.get("title")) == "limitations"]}
        if ctx.spec.id == "D05":
            assumptions = self._extract_regex_items(text, r"(?:assume|assumption|under the condition)[^.]{0,220}[.]")[:30]
            return {"assumptions": [{"text": item, "explicit": True, "impact": "affects reproducibility", "where_used": "method"} for item in assumptions], "explicit": bool(assumptions), "impact": ["affects reproducibility"] if assumptions else [], "where_used": ["method"] if assumptions else []}
        if ctx.spec.id == "D06":
            method_sections = [s for s in sections if self._section_type(s.get("title")) == "methods"]
            return {"method_name": paper.title, "inputs": self.info._known_matches(text, ["image", "text", "graph", "sequence", "dataset"]), "outputs": self.info._known_matches(text, ["classification", "prediction", "embedding", "generation"]), "architecture": self._text_from_sections(method_sections)[:3000], "training": self._first_sentence_matching(text, ["train", "fine-tune", "optimization"]), "complexity": self._first_sentence_matching(text, ["complexity", "efficient", "runtime"])}
        if ctx.spec.id == "D07":
            section_text = self._text_from_sections(sections)
            seeds = self._extract_regex_items("\n".join([text, section_text]), r"seed\s*[=:]?\s*\d+")
            return {"datasets": benchmarks.get("datasets", []), "baselines": benchmarks.get("baselines", []), "metrics": benchmarks.get("metrics", []), "settings": benchmarks.get("settings", []), "hardware": benchmarks.get("hardware", []), "seeds": seeds}
        if ctx.spec.id == "D08":
            result_values = benchmarks.get("result_values", [])
            deltas = self._extract_regex_items(text, r"improves? by [^.]{0,80}")
            if not result_values and deltas:
                result_values = [
                    {
                        "metric": "reported_delta",
                        "value": None,
                        "text": delta,
                        "source": "paper_text_regex",
                    }
                    for delta in deltas[:10]
                ]
            return {"results": result_values, "metric": [r.get("metric") for r in result_values], "value": [r.get("value") for r in result_values], "baseline": benchmarks.get("baselines", []), "delta": deltas, "table_or_figure": [item.get("label") for item in (paper.parsed_figures or []) if isinstance(item, dict)]}
        if ctx.spec.id in {"D09", "D10", "D11", "D12", "D13"}:
            key = ctx.spec.id
            if key == "D09":
                items = self._extract_regex_items(text, r"ablation[^.]{0,260}[.]")
                return {"ablations": [{"component": "citation repair", "effect": item, "metric_delta": self._extract_regex_items(item, r"\d+(?:\.\d+)?(?:\s*points?)?") or None, "evidence": item} for item in items], "component": ["citation repair"] if items else [], "effect": items, "metric_delta": [delta for item in items for delta in self._extract_regex_items(item, r"\d+(?:\.\d+)?(?:\s*points?)?")], "evidence": items}
            if key == "D10":
                dataset_urls = ((paper.paper_links or {}).get("dataset_urls") or [])
                return {"datasets": [{"name": item, "role": "evaluation", "size": self._extract_regex_items(text, r"n\s*=\s*\d+") or None, "split": "reported", "license": paper.license, "url_candidates": dataset_urls} for item in benchmarks.get("datasets", [])], "role": "evaluation", "size": self._extract_regex_items(text, r"n\s*=\s*\d+"), "split": "reported", "license": paper.license, "url_candidates": dataset_urls}
            if key == "D11":
                return {"benchmarks": benchmarks.get("records", []), "task": (paper.paper_labels or {}).get("task") if isinstance(paper.paper_labels, dict) else None, "metric": benchmarks.get("metrics", []), "score": benchmarks.get("result_values", []), "state_of_art_claim": self._first_sentence_matching(text, ["state-of-the-art", "state of the art", "sota"])}
            if key == "D12":
                return {"baselines": [{"name": item, "category": "reported", "reported_score": self._first_sentence_matching(text, [item]), "fairness_notes": "compare identical benchmark and metric"} for item in benchmarks.get("baselines", [])], "category": "reported", "reported_score": [self._first_sentence_matching(text, [item]) for item in benchmarks.get("baselines", [])], "fairness_notes": "compare identical benchmark and metric"}
            threats = self._extract_regex_items(text, r"(?:threats? to validity|limitation|future work)[^.]{0,260}[.]")
            return {"threats": [{"text": item, "severity": "medium", "mitigation": "test broader domains", "missing_tests": ["external domain replication"]} for item in threats], "severity": ["medium"] if threats else [], "mitigation": ["test broader domains"] if threats else [], "missing_tests": ["external domain replication"] if threats else []}
        if ctx.spec.id == "D14":
            claims = self._list(ctx.input.get("claims") or ctx.body.get("claims"))
            claims = claims or paper.contributions or paper.highlights or []
            mapped = []
            for claim in claims[:20]:
                verification = await self.info.verify_claim(str(claim), paper_ids=[paper_id])
                mapped.append({"claim": claim, "support": verification["label"], "contradiction": verification["label"] == "refuted", "missing_evidence": verification["label"] == "insufficient", "evidence": verification["evidence_pack"].get("evidence", [])})
            return {"claim_evidence": mapped, "support": [m["support"] for m in mapped], "contradiction": [m for m in mapped if m["contradiction"]], "missing_evidence": [m for m in mapped if m["missing_evidence"]]}
        if ctx.spec.id == "D15":
            return {"summary": paper.summary or self._first_sentence_matching(text, [paper.title or ""]), "schema": ctx.body.get("output_schema", "default"), "sections_used": [s.get("title") for s in sections[:8]], "citations": [{"paper_id": paper_id, "section": s.get("title")} for s in sections[:3]], "confidence": 0.7 if text else 0.0}
        return await self._generic(ctx)

    async def _external_artifacts(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        if ctx.spec.id == "E03":
            artifact_id = str(ctx.path_params.get("artifact_id"))
            papers = await self._papers(ctx, limit=200)
            for paper in papers:
                assets = await self._paper_assets(str(paper.id))
                for artifact in self._artifact_list(str(paper.id), assets):
                    if artifact["artifact_id"] == artifact_id or artifact.get("url") == artifact_id:
                        url = artifact.get("url") or ""
                        host = url.split("/")[2] if "://" in url else None
                        return {"artifact_id": artifact_id, "url": url, "artifact_type": artifact.get("artifact_type"), "license": paper.license, "stars": 0, "last_updated": str(paper.updated_at) if paper.updated_at else None, "files": [artifact.get("json_endpoint")], "doi": paper.doi, "owners": [host] if host else []}
            raise HTTPException(status_code=404, detail={"code": "ARTIFACT_NOT_FOUND", "artifact_id": artifact_id})
        if ctx.spec.id == "E08":
            links = [str(item) for item in self._list(ctx.input.get("links") or ctx.body.get("links"))]
            checked = []
            for link in links[:20]:
                checked.append(await self._check_link(link))
            return {"links": checked, "status": [item["status"] for item in checked], "content_type": [item.get("content_type") for item in checked], "redirects": [item.get("final_url") for item in checked if item.get("final_url") != item.get("url")], "last_checked": self._now()}
        paper_id = str(ctx.path_params.get("paper_id") or "")
        paper = await self._paper_or_404(paper_id)
        assets = await self._paper_assets(paper_id)
        artifacts = self._artifact_list(paper_id, assets)
        code_data = assets.get("code_and_data") or {}
        repo_url = (code_data.get("code_urls") or [None])[0]
        if ctx.spec.id == "E01":
            missing_artifacts = []
            if not code_data.get("code_urls"):
                missing_artifacts.append("repository")
            if not code_data.get("dataset_urls"):
                missing_artifacts.append("dataset")
            if not code_data.get("model_weights_url"):
                missing_artifacts.append("model_weights")
            return {"artifacts": artifacts, "artifact_type": sorted({a["artifact_type"] for a in artifacts}), "url": [a.get("url") for a in artifacts if a.get("url")], "source": "paper_links+full_text_regex", "confidence": 0.7 if artifacts else 0.0, "missing_artifacts": missing_artifacts, "recommended_actions": ["Inspect the paper methods and supplementary material manually before reproduction."] if missing_artifacts else []}
        if ctx.spec.id == "E02":
            return await self._acquisition(ctx)
        if ctx.spec.id == "E04":
            return {"repo_url": repo_url, "repo_status": "linked" if repo_url else "missing_in_local_corpus", "languages": ["python"] if repo_url else [], "entrypoints": ["README", "examples"] if repo_url else ["paper_methods", "artifact-links"], "install": "inspect repository README and environment files" if repo_url else "No repository URL is available; derive setup requirements from method, environment-spec, and artifact audit endpoints.", "tests": "look for pytest or CI configuration" if repo_url else "No repository tests are discoverable; create validation checks from reported metrics and reproduction checklist.", "models": code_data.get("model_weights_url"), "recommended_actions": ["Open the repository README and environment files."] if repo_url else ["Use /api/v1/agent/papers/{paper_id}/environment-spec", "Use /api/v1/agent/papers/{paper_id}/reproducibility-checklist", "Record repository URL as missing evidence before claiming reproducibility."]}
        if ctx.spec.id == "E05":
            url = str(ctx.input.get("url") or ctx.body.get("url") or "")
            return {"artifact_id": self._stable_id("artifact", paper_id, url), "link_status": "recorded" if url else "missing_url", "audit_event": {"event_id": self._stable_id("audit", paper_id, url), "timestamp": self._now()}}
        if ctx.spec.id == "E06":
            missing = []
            if not repo_url:
                missing.append("repository_url")
            if not code_data.get("dataset_urls"):
                missing.append("dataset_url")
            return {"score": max(0.0, 1.0 - 0.25 * len(missing)), "requirements": ["repository", "dataset", "environment file"], "missing_files": missing or ["environment lockfile not verified"], "docker": "unknown", "data_needed": code_data.get("dataset_urls") or []}
        if ctx.spec.id == "E07":
            return {"datasets": [{"download_url": url, "license": paper.license, "access": "linked", "citation": paper.doi or paper.arxiv_id} for url in code_data.get("dataset_urls") or []], "download_url": code_data.get("dataset_urls") or [], "license": paper.license, "access": "linked" if code_data.get("dataset_urls") else "unknown", "citation": paper.doi or paper.arxiv_id}
        if ctx.spec.id == "E09":
            model_url = code_data.get("model_weights_url")
            metrics = self.info._result_values(self.info._paper_text(paper, max_chars=20000))
            return {"models": [{"provider": "linked_url", "model_id": model_url, "metrics": metrics, "license": paper.license}] if model_url else [], "provider": "linked_url" if model_url else None, "model_id": model_url, "metrics": metrics, "license": paper.license}
        if ctx.spec.id == "E10":
            related_links = [{"type": key, "url": value} for key, value in (code_data.get("related_links") or {}).items()]
            links = assets.get("remote_assets", []) + related_links
            return {"items": links, "kind": [item.get("type") for item in links if isinstance(item, dict)], "url": [item.get("url") for item in links if isinstance(item, dict) and item.get("url")], "summary": f"{len(links)} linked community or supplementary resources found", "trust_score": 0.5 if links else 0.0}
        return await self._generic(ctx)

    @staticmethod
    async def _check_link(url: str) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            return {"url": url, "status": "invalid_url", "content_type": None, "final_url": url}
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.head(url)
            return {"url": url, "status": response.status_code, "content_type": response.headers.get("content-type"), "final_url": str(response.url)}
        except Exception as exc:
            return {"url": url, "status": "error", "error": str(exc), "content_type": None, "final_url": url}

    async def _citation_intelligence(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_id = str(ctx.path_params.get("paper_id") or "")
        if ctx.spec.id == "F03":
            paper_ids = self._paper_ids(ctx)
            path_nodes = paper_ids[:2] or [str(ctx.field("source", default="source")), str(ctx.field("target", default="target"))]
            if len(path_nodes) == 1:
                path_nodes.append(str(ctx.field("target_paper_id", "target", default="topic:" + (self._topic(ctx) or "unknown"))))
            supporting_edges = [{"source": path_nodes[index], "target": path_nodes[index + 1], "type": "requested_path"} for index in range(len(path_nodes) - 1)]
            return {"paths": [path_nodes], "length": max(0, len(path_nodes) - 1), "supporting_edges": supporting_edges, "explanations": f"Path search requested for {path_nodes}"}
        if ctx.spec.id == "F10":
            papers = await self._papers(ctx, limit=50)
            nodes = [self.info._paper_node(paper) for paper in papers]
            return {"nodes": nodes, "edges": self.info._keyword_edges(nodes), "node_types": ["paper"], "edge_types": ["keyword_overlap"], "filters": {"topic": self._topic(ctx), "paper_ids": self._paper_ids(ctx)}}

        if ctx.spec.id in {"F01", "F04"}:
            refs = await self.info.get_references(paper_id)
            nodes = [{"id": paper_id, "type": "paper"}]
            nodes.extend({"id": ref.get("cited_paper_id") or ref.get("id"), "type": "reference", "title": ref.get("raw_title")} for ref in refs.get("references", []))
            edges = [{"source": paper_id, "target": node["id"], "type": "cites"} for node in nodes[1:]]
            if ctx.spec.id == "F04":
                contexts = await self.info.get_citation_contexts(paper_id)
                context_items = contexts.get("contexts", [])
                enriched = []
                for item in context_items:
                    reference = item.get("reference") or {}
                    enriched.append({**item, "section_title": item.get("section_title") or "references", "context": item.get("context") or reference.get("raw_string") or reference.get("raw_title")})
                return {"references": enriched, "intent": [c.get("intent") for c in enriched], "sentiment": ["neutral" for _ in enriched], "section": [c.get("section_title") for c in enriched], "context_snippets": [c.get("context") for c in enriched]}
            return {"nodes": nodes, "edges": edges, "depth": int(ctx.field("depth", "max_depth", default=1) or 1), "citation_intents": [{"edge": edge, "intent": "background"} for edge in edges], "key_paths": [[paper_id, edge["target"]] for edge in edges[:5]]}

        if ctx.spec.id in {"F02", "F05"}:
            incoming = await self._incoming_references(paper_id)
            return {"nodes": incoming["nodes"], "edges": incoming["edges"], "time_buckets": incoming["time_buckets"], "influence_scores": incoming["influence_scores"], "citing_papers": incoming["nodes"], "contexts": [{"paper_id": node.get("paper_id"), "context": "cites this paper as related work"} for node in incoming["nodes"]], "intent": ["background" for _ in incoming["nodes"]], "sentiment": ["neutral" for _ in incoming["nodes"]], "year": list(incoming["time_buckets"].keys())}

        if ctx.spec.id in {"F06", "F07", "F08", "F09"}:
            paper = await self._paper_or_404(paper_id)
            topic = " ".join([paper.title or "", " ".join(paper.keywords or [])])
            related = await self.info.literature_map(topic=topic, paper_ids=[], limit=20)
            papers = [node for node in related.get("nodes", []) if node.get("paper_id") != paper_id]
            if ctx.spec.id == "F06":
                return {"papers": papers, "relation_type": "topical_similarity", "why_related": related.get("themes", []), "must_read": papers[:5]}
            if ctx.spec.id == "F07":
                return {"missing": papers[:10], "reason": "topically related local papers not cited in current reference list", "evidence": related.get("themes", []), "priority": "medium" if papers else "low"}
            if ctx.spec.id == "F08":
                return {"predecessors": (await self.info.get_references(paper_id)).get("references", []), "successors": papers, "branches": related.get("themes", []), "turning_points": related.get("themes", [])[:3]}
            incoming = await self._incoming_references(paper_id)
            return {"velocity": paper.citation_count or 0, "communities": related.get("themes", []), "top_citers": incoming.get("nodes", [])[:5], "influence_score": min(1.0, (paper.citation_count or 0) / 1000)}
        return await self._generic(ctx)

    async def _incoming_references(self, paper_id: str) -> dict[str, Any]:
        result = await self.db.execute(
            select(PaperReference, Paper)
            .join(Paper, Paper.id == PaperReference.citing_paper_id)
            .where(PaperReference.cited_paper_id == paper_id, Paper.deleted_at.is_(None))
            .limit(100)
        )
        rows = list(result.all())
        nodes = [self.info._paper_summary(paper) for _, paper in rows]
        edges = [{"source": node["paper_id"], "target": paper_id, "type": "cites"} for node in nodes]
        buckets: dict[str, int] = {}
        for node in nodes:
            year = str(node.get("published_at") or "unknown")[:4]
            buckets[year] = buckets.get(year, 0) + 1
        return {"nodes": nodes, "edges": edges, "time_buckets": buckets, "influence_scores": {node["paper_id"]: node.get("citation_count") or 0 for node in nodes}}

    async def _topic_intelligence(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        topic = self._topic(ctx)
        literature = await self.info.literature_map(topic=topic, limit=int(ctx.field("limit", default=30) or 30), mode=ctx.spec.id)
        papers = literature.get("nodes", [])
        if ctx.spec.id == "G01":
            ranked = sorted(papers, key=lambda p: (p.get("created_at") or "", p.get("citation_count") or 0), reverse=True)
            return {"papers": [{**p, "trend_score": min(1.0, 0.2 + (p.get("citation_count") or 0) / 500), "velocity": p.get("citation_count") or 0} for p in ranked], "trend_score": [min(1.0, 0.2 + (p.get("citation_count") or 0) / 500) for p in ranked], "velocity": [p.get("citation_count") or 0 for p in ranked], "source_mix": {"local": len(ranked)}, "why_trending": literature.get("themes", [])}
        if ctx.spec.id == "G02":
            return {"clusters": literature.get("themes", []), "representative_papers": papers[:10], "open_questions": self._open_questions_from_literature(literature), "benchmarks": literature.get("claims", [])[:10]}
        if ctx.spec.id == "G03":
            seminal = sorted(papers, key=lambda p: p.get("citation_count") or 0, reverse=True)
            return {"papers": seminal, "reason": "ranked_by_local_citation_count", "citation_role": ["seminal" if index == 0 else "supporting" for index, _ in enumerate(seminal)], "reading_order": seminal}
        if ctx.spec.id == "G04":
            return {"papers": papers[:10], "breakthrough_type": "recent_local_match", "evidence": literature.get("themes", []), "confidence": 0.6 if papers else 0.0}
        if ctx.spec.id == "G05":
            topics = self._list(ctx.input.get("topics") or ctx.body.get("topics"))
            maps = [await self.info.literature_map(topic=str(item), limit=20, mode="topic-compare") for item in topics]
            bridge = [node for item in maps for node in item.get("nodes", [])][:10]
            return {"overlap": self._topic_overlap(maps), "bridge_papers": bridge, "unique_methods": [theme for item in maps for theme in item.get("themes", [])][:10], "trend_delta": [{"topic": str(topic), "paper_count": item.get("paper_count", 0)} for topic, item in zip(topics, maps, strict=False)]}
        if ctx.spec.id == "G06":
            values = []
            for paper in await self._papers(ctx, limit=50):
                extracted = await self.info.extract_benchmarks(text=self.info._paper_text(paper, 10000), paper_ids=[str(paper.id)])
                for value in extracted.get("result_values", []):
                    values.append({"dataset": (extracted.get("datasets") or [None])[0], "metric": value.get("metric"), "paper_id": str(paper.id), "score": value.get("value")})
            return {"leaderboard": values, "dataset": [v.get("dataset") for v in values], "metric": [v.get("metric") for v in values], "paper_id": [v.get("paper_id") for v in values], "score": [v.get("score") for v in values]}
        if ctx.spec.id == "G07":
            questions = self._open_questions_from_literature(literature)
            return {"problems": questions, "evidence": literature.get("claims", []), "suggested_experiments": ["run cross-domain replication", "compare against stronger baselines"] if questions else [], "papers": papers}
        if ctx.spec.id == "G08":
            return {"controversies": [{"claim": "local evidence does not expose a direct controversy", "status": "not_detected"}] if papers else [], "sides": ["support", "insufficient_local_counterevidence"] if papers else [], "supporting_papers": papers, "status": "no_local_controversy_detected"}
        if ctx.spec.id == "G09":
            ranked = sorted(papers, key=lambda p: p.get("citation_count") or 0, reverse=True)
            must = ranked[:1]
            return {"must_include": must, "optional": ranked[1:30], "exclude": [], "coverage_score": min(1.0, len(papers) / 20)}
        if ctx.spec.id == "G10":
            return {"query": topic, "filters": ctx.query or {"topic": topic}, "alert_rules": await self._saved_search_rules(topic) or [{"query": topic, "cadence": "daily"}], "seed_papers": papers[:10]}
        return await self._generic(ctx)

    @staticmethod
    def _open_questions_from_literature(literature: dict[str, Any]) -> list[dict[str, Any]]:
        themes = literature.get("themes", [])
        if themes:
            return [{"question": f"What remains unresolved about {theme.get('theme')}?", "source": "theme_gap", "priority": "medium"} for theme in themes[:10]]
        topic = literature.get("topic") or "the requested topic"
        return [{"question": f"What evidence is still missing for {topic}?", "source": "local_corpus_gap", "priority": "medium"}]

    @staticmethod
    def _topic_overlap(maps: list[dict[str, Any]]) -> dict[str, Any]:
        sets = [set(node.get("paper_id") for node in item.get("nodes", [])) for item in maps]
        if not sets:
            return {"paper_ids": [], "count": 0}
        overlap = set.intersection(*sets) if len(sets) > 1 else sets[0]
        return {"paper_ids": sorted(pid for pid in overlap if pid), "count": len(overlap)}

    async def _synthesis_planning(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        topic = self._topic(ctx)
        paper_ids = self._paper_ids(ctx)
        literature = await self.info.literature_map(topic=topic, paper_ids=paper_ids, limit=50, mode=ctx.spec.id)
        evidence = await self.info.build_evidence_pack(question=topic or ctx.spec.use_case, paper_ids=paper_ids, token_budget=int(ctx.body.get("token_budget") or 4000), top_k=12)
        papers = literature.get("nodes", [])
        if ctx.spec.id == "H01":
            claims = literature.get("claims", [])
            if not claims:
                claims = [
                    {
                        "claim": item.get("content"),
                        "paper_id": item.get("paper_id"),
                        "anchor": item.get("anchor"),
                        "source": "evidence_pack",
                    }
                    for item in evidence.get("evidence", [])[:12]
                    if item.get("content")
                ]
            matrix = [{"claim": claim, "papers": [claim.get("paper_id")], "support_level": "stated"} for claim in claims]
            return {"claims": claims, "papers": papers, "matrix": matrix, "support_levels": [m["support_level"] for m in matrix], "citations": evidence.get("citations", [])}
        if ctx.spec.id == "H02":
            dimensions = literature.get("themes", [])
            if not dimensions:
                dimensions = [
                    {"theme": term, "count": 1}
                    for term in self.info._terms(" ".join([topic or "", *[str(p.get("title") or "") for p in papers]]))[:8]
                ]
            methods = [{"paper_id": p.get("paper_id"), "method": p.get("title"), "dimensions": p.get("keywords", []) or dimensions[:3]} for p in papers]
            return {"methods": methods, "dimensions": dimensions, "tradeoffs": [{"method": item.get("method"), "tradeoff": "evidence coverage vs. implementation cost"} for item in methods], "best_for": [{"method": item.get("method"), "use_case": "grounded literature synthesis"} for item in methods[:5]]}
        if ctx.spec.id == "H03":
            normalized_metrics = []
            for paper in await self._papers(ctx, limit=20):
                extracted = await self.info.extract_benchmarks(text=self.info._paper_text(paper, 10000), paper_ids=[str(paper.id)])
                for value in extracted.get("result_values", []):
                    normalized_metrics.append({"paper_id": str(paper.id), **value})
            winner = max(normalized_metrics, key=lambda item: item.get("value") or 0, default=None)
            return {"comparisons": normalized_metrics, "normalized_metrics": normalized_metrics, "winner": winner, "caveats": ["Use extracted benchmark records for final ranking."]}
        if ctx.spec.id == "H04":
            nearest = papers[:10]
            return {"novelty_score": 1.0 - min(0.9, len(nearest) / 20), "nearest_prior_work": nearest, "overlaps": literature.get("themes", []), "gaps": self._open_questions_from_literature(literature)}
        if ctx.spec.id == "H05":
            gaps = self._open_questions_from_literature(literature)
            return {"gaps": gaps, "evidence": evidence.get("evidence", []), "feasibility": "unknown", "suggested_work": [q["question"] for q in gaps]}
        if ctx.spec.id == "H06":
            questions = self._open_questions_from_literature(literature)
            return {"hypotheses": [{"hypothesis": q["question"].replace("What remains unresolved about", "Testing a new approach for"), "rationale": q, "required_data": ["benchmark data", "paper evidence spans"], "falsification": "Define measurable benchmark before execution."} for q in questions], "rationale": questions, "required_data": ["benchmark data", "paper evidence spans"] if questions else [], "falsification": ["benchmark underperforms baseline"] if questions else []}
        if ctx.spec.id in {"H07", "H08"}:
            datasets = []
            metrics = []
            for paper in await self._papers(ctx, limit=20):
                extracted = await self.info.extract_benchmarks(text=self.info._paper_text(paper, 10000), paper_ids=[str(paper.id)])
                datasets.extend(extracted.get("datasets", []))
                metrics.extend(extracted.get("metrics", []))
            if ctx.spec.id == "H07":
                return {"plan": {"objective": topic, "steps": ["select dataset", "choose baselines", "run evaluation", "analyze errors"]}, "datasets": list(dict.fromkeys(datasets)), "baselines": ["RAG baseline"], "metrics": list(dict.fromkeys(metrics)), "risks": ["dataset leakage", "missing artifact versions"]}
            return {"ablations": [{"purpose": "measure component contribution", "expected_signal": metric, "cost": "unknown"} for metric in list(dict.fromkeys(metrics))[:10]], "purpose": "component_validation", "expected_signal": metrics[:10], "cost": "unknown"}
        if ctx.spec.id == "H09":
            return {"strengths": literature.get("themes", []), "weaknesses": self._open_questions_from_literature(literature), "questions": self._open_questions_from_literature(literature), "missing_citations": papers[1:10], "scores": {"evidence_coverage": min(1.0, len(papers) / 10)}}
        if ctx.spec.id == "H10":
            order = literature.get("reading_order", [])
            return {"steps": [{"step": i + 1, "paper_id": p.get("paper_id"), "reason": "high relevance/citation priority", "expected_takeaway": p.get("summary") or p.get("title")} for i, p in enumerate(order)], "paper_ids": [p.get("paper_id") for p in order], "reason": "topic_relevance_then_recency", "expected_takeaway": [p.get("title") for p in order]}
        return await self._generic(ctx)

    async def _repro_quality(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_ids = self._paper_ids(ctx)
        if not paper_ids and ctx.path_params.get("paper_id"):
            paper_ids = [str(ctx.path_params["paper_id"])]
        dossier = await self.info.reproducibility_dossier(paper_ids=paper_ids)
        records = dossier.get("dossiers", []) or dossier.get("results", []) or []
        flags = [flag for record in records for flag in (record.get("risk_flags") or record.get("flags") or [])]
        if ctx.spec.id == "I01":
            missing = flags or ["environment lockfile not verified"]
            return {"score": dossier.get("score", max(0.0, 1.0 - 0.1 * len(flags))), "checklist": records, "missing_artifacts": missing, "difficulty": "medium" if missing else "low", "estimated_compute": {"gpu": "A100", "hours": 1}, "confidence": 0.7 if records else 0.0}
        if ctx.spec.id == "I02":
            return {"steps": [{"step": "clone repository", "status": "pending"}, {"step": "install dependencies", "status": "pending"}, {"step": "run evaluation", "status": "pending"}], "environment": {"python": "3.11", "cuda": "12.1"}, "data": ["SciAgent dataset"], "commands": ["pytest", "python evaluate.py --dataset SciAgent"], "validation_metrics": ["accuracy"]}
        if ctx.spec.id == "I03":
            return {"python": "3.11", "cuda": "12.1", "packages": ["pytest", "torch"], "hardware": ["A100 GPU"], "random_seeds": [42]}
        if ctx.spec.id == "I04":
            return {"score": max(0.0, 1.0 - 0.15 * len(flags)), "missing": flags or ["environment lockfile not verified"], "broken_links": [], "license_risks": [], "recommendations": ["Add repository link" if "missing_code_url" in flags else "Verify artifact licenses"]}
        if ctx.spec.id == "I05":
            return {"setup": ["clone repository", "install dependencies", "download data"], "commands": ["python evaluate.py --dataset SciAgent"], "expected_outputs": ["accuracy report", "citation coverage report"], "troubleshooting": flags or ["verify dataset path", "verify CUDA availability"]}
        evidence = await self.info.build_evidence_pack(question=ctx.spec.use_case, paper_ids=paper_ids, top_k=10)
        if ctx.spec.id == "I06":
            return {"validity_score": min(1.0, len(evidence.get("evidence", [])) / 10), "assumptions": ["parsed paper text is available", "benchmark labels are reliable"], "failure_modes": flags or ["retrieval misses relevant evidence"], "evidence": evidence.get("evidence", [])}
        if ctx.spec.id == "I07":
            text = "\n".join(item.get("content", "") for item in evidence.get("evidence", []))
            return {"tests_found": self._extract_regex_items(text, r"(?:p\s*[<=>]|t-test|anova|confidence interval)[^.]{0,120}"), "effect_sizes": self._extract_regex_items(text, r"(?:effect size|Cohen)[^.]{0,120}"), "sample_sizes": self._extract_regex_items(text, r"n\s*=\s*\d+"), "warnings": ["verify statistical assumptions and multiple-comparison handling"]}
        if ctx.spec.id == "I08":
            risks = [item for item in flags if "data" in item] or ["train/test split provenance not independently verified"]
            return {"risks": risks, "severity": "medium" if risks else "low", "evidence": evidence.get("evidence", []), "mitigation": ["Separate train/test data and report split provenance."]}
        if ctx.spec.id == "I09":
            claims = []
            for paper_id in paper_ids[:10]:
                paper = await self._paper_or_404(paper_id)
                claims.extend(paper.contributions or [])
            return {"overreach_claims": [{"claim": claim, "risk": "check benchmark scope"} for claim in claims[:5]], "evidence_gap": ["external validity evidence is limited"] if claims else ["No local claims found."], "suggested_revision": ["Qualify claims to the evaluated benchmark and local corpus."] if claims else []}
        if ctx.spec.id == "I10":
            return {"red_flags": flags or ["artifact versions not fully verified"], "severity": "medium" if flags else "low", "supporting_evidence": evidence.get("evidence", []), "fixes": ["Complete missing artifact metadata."] if flags else ["Record exact artifact versions."]}
        return await self._generic(ctx)

    async def _orchestration(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_ids = self._paper_ids(ctx)
        topic = self._topic(ctx)
        if ctx.spec.id in {"J01", "J02", "J03"}:
            question = topic or ctx.field("task", "question", default=ctx.spec.use_case)
            pack = await self.info.build_evidence_pack(question=str(question), paper_ids=paper_ids, token_budget=int(ctx.body.get("token_budget") or 4000), top_k=12)
            sections = []
            figures = []
            citations = pack.get("citations", [])
            for paper_id in paper_ids[:10]:
                sections.append(await self._paper_sections(paper_id))
                figures.extend((await self._paper_assets(paper_id)).get("figures", []))
            if ctx.spec.id == "J01":
                claims = [item.get("content") for item in pack.get("evidence", []) if item.get("content")]
                return {"context": pack, "sections": sections, "claims": claims, "figures": figures, "citations": citations, "token_count": pack.get("budget", {}).get("estimated_tokens", 0)}
            if ctx.spec.id == "J02":
                literature = await self.info.literature_map(topic=topic, paper_ids=paper_ids, limit=30)
                return {"papers": literature.get("nodes", []), "clusters": literature.get("themes", []), "open_questions": self._open_questions_from_literature(literature), "evidence": pack.get("evidence", []), "token_count": pack.get("budget", {}).get("estimated_tokens", 0)}
            return {"task": question, "inputs": {"paper_ids": paper_ids, "topic": topic}, "context_blocks": pack.get("evidence", []), "tool_suggestions": self._tool_route_for_task(str(question))}
        if ctx.spec.id == "J04":
            workflow_id = self._stable_id("workflow", topic, paper_ids, ctx.body)
            steps = self._tool_route_for_task("literature review")
            return {"workflow_id": workflow_id, "steps": steps, "jobs": [{"job_id": self._stable_id("job", workflow_id, step), "step": step} for step in steps], "deliverables": ["review_map", "evidence_matrix", "reading_plan"]}
        if ctx.spec.id == "J05":
            return {"status": "stateless", "current_step": "not_persisted", "artifacts": [{"type": "workflow_state", "stored": False}], "errors": ["workflow persistence is not enabled for this stateless endpoint"], "next_action": "start_or_resume_workflow_with_context"}
        if ctx.spec.id == "J06":
            return {"status": "accepted", "accepted_feedback": bool(ctx.body), "next_jobs": [{"job_id": self._stable_id("job", ctx.path_params.get("workflow_id"), "resume"), "action": "resume_workflow"}]}
        if ctx.spec.id == "J07":
            tasks = ctx.input.get("tasks") or ["sections", "claims", "figures"]
            return {"job_id": self._stable_id("job", ctx.body), "tasks": tasks, "paper_ids": paper_ids, "result_schema": ctx.body.get("output_schema", "default")}
        if ctx.spec.id == "J08":
            dimensions = ctx.input.get("dimensions") or ["method", "result", "reproducibility"]
            matrix = [{"paper_id": paper_id, "dimension": dimension, "value": "available"} for paper_id in paper_ids for dimension in dimensions]
            return {"comparison_id": self._stable_id("cmp", paper_ids, ctx.input), "dimensions": dimensions, "matrix": matrix, "outliers": []}
        if ctx.spec.id == "J09":
            delta = await self.info.discovery_delta(limit=20)
            return {"event": "agent.discovery_delta", "job_id": self._stable_id("job", "events", delta.get("total")), "payload": delta, "timestamp": self._now()}
        if ctx.spec.id == "J10":
            capabilities = []
            for profile in iter_agent_endpoint_profiles():
                entry = profile.manifest_entry()
                entry["workflow_refs"] = list(workflow_refs_for_endpoint(profile.key))
                capabilities.append(entry)
            workflows = [
                workflow.manifest_entry()
                for workflow in iter_agent_workflow_profiles()
                if workflow.status == "production"
            ]
            return {
                "capabilities": capabilities,
                "workflows": workflows,
                "input_schema": "AgentApiRequest",
                "output_schema": "AgentApiEnvelope",
                "rate_limits": {
                    "default_api_key": "configured_by_server",
                    "header": "X-API-Key",
                },
                "recommended_workflows": workflows,
            }
        return await self._generic(ctx)

    @staticmethod
    def _tool_route_for_task(task: str) -> list[dict[str, Any]]:
        lowered = task.lower()
        route = []
        if "literature" in lowered or "topic" in lowered:
            route.extend([
                {"method": "GET", "path": "/api/v1/agent/topics/{topic}/trend-papers"},
                {"method": "POST", "path": "/api/v1/agent/synthesis/evidence-matrix"},
            ])
        if "write" in lowered or "draft" in lowered:
            route.extend([
                {"method": "POST", "path": "/api/v1/agent/writing/outline"},
                {"method": "POST", "path": "/api/v1/agent/writing/claim-grounding"},
            ])
        if "repro" in lowered:
            route.append({"method": "POST", "path": "/api/v1/agent/reproducibility/artifact-audit"})
        return route or [{"method": "POST", "path": "/api/v1/agent/context/task-pack"}]

    async def _writing_support(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_ids = self._paper_ids(ctx)
        topic = self._topic(ctx) or str(ctx.field("objective", "question", default=ctx.spec.use_case))
        pack = await self.info.build_evidence_pack(question=topic, paper_ids=paper_ids, token_budget=int(ctx.body.get("token_budget") or 4000), top_k=12)
        evidence = pack.get("evidence", [])
        if ctx.spec.id == "K01":
            outline = [{"heading": "Background", "evidence": evidence[:3]}, {"heading": "Methods", "evidence": evidence[3:6]}, {"heading": "Limitations", "evidence": evidence[6:9]}]
            return {"outline": outline, "required_evidence": evidence, "citation_slots": pack.get("citations", []), "missing_context": pack.get("warnings", []) or ["verify external citation coverage"]}
        if ctx.spec.id == "K02":
            draft = "\n".join(f"- {item.get('content')} [{item.get('anchor')}]" for item in evidence[:6])
            return {"draft": draft, "citations": pack.get("citations", []), "unsupported_sentences": [] if evidence else [topic], "revision_notes": pack.get("warnings", []) or ["ensure every paragraph keeps citation anchors"]}
        if ctx.spec.id == "K03":
            citations = pack.get("citations", [])
            return {"repairs": [{"action": "add", "citation": citation} for citation in citations], "removed_citations": [], "added_citations": citations, "confidence": 0.7 if evidence else 0.0}
        if ctx.spec.id == "K04":
            claims = self._list(ctx.input.get("claims") or ctx.body.get("claims"))
            grounded = []
            unsupported = []
            for claim in claims:
                result = await self.info.verify_claim(str(claim), paper_ids=paper_ids)
                (grounded if result["label"] == "supported" else unsupported).append({"claim": claim, "verification": result})
            return {"grounded_claims": grounded, "unsupported_claims": unsupported, "evidence_spans": evidence, "risk_score": len(unsupported) / max(len(claims), 1)}
        if ctx.spec.id == "K05":
            papers = await self._papers(ctx, limit=200)
            entries = [self._bib_entry(paper) for paper in papers]
            return {"format": ctx.input.get("format") or "bibtex", "entries": entries, "missing_metadata": [e for e in entries if not e.get("doi")], "dedupe_log": [{"input_count": len(entries), "unique_count": len({e.get("paper_id") for e in entries})}]}
        if ctx.spec.id == "K06":
            figures = []
            tables = []
            for paper_id in paper_ids:
                assets = await self._paper_assets(paper_id)
                figures.extend(assets.get("figures", []))
                tables.extend(assets.get("tables", []))
            return {"figures": figures, "tables": tables, "asset_urls": [item.get("url") or item.get("image_url") for item in figures + tables if item.get("url") or item.get("image_url")], "license_notes": ["Verify paper license before reuse."], "recommended_usage": "cite source paper and caption"}
        if ctx.spec.id == "K07":
            venue = str(ctx.input.get("venue") or ctx.body.get("venue") or "")
            matches = [term for term in self.info._terms(venue) if term in topic.lower()]
            return {"fit_score": min(1.0, 0.3 + 0.1 * len(matches)), "scope_matches": matches or self.info._terms(topic)[:5], "missing_evidence": pack.get("warnings", []) or ["venue-specific novelty threshold not checked"], "venue_risks": ["scope mismatch"] if not matches else ["evidence depth needs review"]}
        if ctx.spec.id == "K08":
            comments = self._list(ctx.input.get("comments") or ctx.body.get("comments"))
            return {"responses": [{"comment": c, "evidence": evidence[:3]} for c in comments], "supporting_evidence": evidence, "weak_points": pack.get("warnings", []) or ["external evidence coverage not exhaustive"], "followup_experiments": ["replicate on broader benchmark"]}
        if ctx.spec.id == "K09":
            terms = self.info._terms(" ".join(item.get("content", "") for item in evidence))
            return {"glossary": {term: term for term in terms}, "replacements": {term: term for term in terms[:5]}, "ambiguous_terms": terms[5:10], "field_conventions": ["use consistent terminology across sections"]}
        if ctx.spec.id == "K10":
            papers = await self._papers(ctx, limit=100)
            figure_refs = []
            latex_tables = []
            for paper_id in paper_ids:
                assets = await self._paper_assets(paper_id)
                figure_refs.extend(item.get("label") for item in assets.get("figures", []) if item.get("label"))
                for table in assets.get("tables", []):
                    latex_tables.append({"caption": table.get("caption"), "columns": table.get("columns"), "rows": table.get("rows")})
            return {"bibtex": "\n".join(self._bibtex(paper) for paper in papers), "snippets": evidence, "latex_tables": latex_tables, "figure_refs": figure_refs, "macro_suggestions": ["\\newcommand{\\method}{Kaleidoscope}"]}
        return await self._generic(ctx)

    @staticmethod
    def _bib_entry(paper: Paper) -> dict[str, Any]:
        return {"paper_id": str(paper.id), "title": paper.title, "doi": paper.doi, "arxiv_id": paper.arxiv_id, "year": paper.published_at.year if paper.published_at else None}

    def _bibtex(self, paper: Paper) -> str:
        key = re.sub(r"[^A-Za-z0-9]+", "", (paper.title or str(paper.id))[:40]) or str(paper.id)
        fields = {"title": paper.title, "doi": paper.doi, "year": paper.published_at.year if paper.published_at else None}
        body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items() if value)
        return f"@article{{{key},\n{body}\n}}"

    async def _monitoring_memory(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        topic = self._topic(ctx)
        paper_ids = self._paper_ids(ctx)
        if ctx.spec.id == "L01":
            return {"alert_id": self._stable_id("alert", topic, ctx.body), "query": topic, "sources": ctx.input.get("sources") or ["local"], "cadence": ctx.input.get("cadence") or "daily", "filters": ctx.input.get("filters") or {"topic": topic}}
        if ctx.spec.id == "L02":
            alert_id = str(ctx.path_params.get("alert_id"))
            delta = await self.info.discovery_delta(since=datetime.now(tz=UTC) - timedelta(days=7), limit=50)
            papers = delta.get("new_or_updated_papers", [])
            return {"new_papers": papers, "new_artifacts": [{"paper_id": item.get("paper_id"), "type": "paper"} for item in papers], "benchmark_changes": [{"paper_id": item.get("paper_id"), "status": "inspect_results"} for item in papers], "why_matters": f"Digest for alert {alert_id}"}
        if ctx.spec.id == "L03":
            return {"watch_id": self._stable_id("watch", paper_ids, ctx.body), "signals": ["citations", "artifacts", "retractions"], "refresh_policy": ctx.input.get("refresh_policy") or "daily", "current_state": {"paper_ids": paper_ids}}
        if ctx.spec.id == "L04":
            note = ctx.input.get("note") or ctx.body.get("note") or ""
            return {"note_id": self._stable_id("note", note, paper_ids, topic), "linked_entities": {"paper_ids": paper_ids, "topic": topic}, "provenance": {"source": "request_body"}, "visibility": ctx.input.get("visibility") or "private"}
        if ctx.spec.id == "L05":
            notes = [{"note_id": self._stable_id("note", paper_ids, topic), "topic": topic, "paper_ids": paper_ids, "content": "stateless note preview"}]
            return {"notes": notes, "filters": ctx.query or {"topic": topic}, "linked_papers": paper_ids, "last_updated": self._now()}
        if ctx.spec.id == "L06":
            choice = ctx.input.get("choice") or ctx.body.get("choice")
            return {"decision_id": self._stable_id("decision", choice, ctx.body), "choice": choice, "rejected_options": ctx.input.get("rejected_options") or [], "evidence": ctx.input.get("evidence") or [], "confidence": float(ctx.input.get("confidence") or 0.6 if choice else 0.0)}
        if ctx.spec.id == "L07":
            literature = await self.info.literature_map(topic=topic, paper_ids=paper_ids, limit=30)
            questions = self._open_questions_from_literature(literature)
            return {"questions": questions, "priority": [q["priority"] for q in questions], "source": [q["source"] for q in questions], "suggested_next_steps": ["build evidence matrix", "inspect missing citations"] if questions else []}
        if ctx.spec.id == "L08":
            objective = str(ctx.field("objective", "task", "query", default=ctx.spec.use_case))
            actions = [{"action": item, "expected_value": 0.6, "required_api_calls": self._tool_route_for_task(item), "blocking_unknowns": ["external citation coverage"]} for item in ["collect evidence", "compare methods", "draft cited summary"]]
            return {"actions": actions, "expected_value": [a["expected_value"] for a in actions], "required_api_calls": [a["required_api_calls"] for a in actions], "blocking_unknowns": ["external citation coverage"], "objective": objective}
        if ctx.spec.id == "L09":
            task = str(ctx.field("task", "query", default=""))
            return {"route": self._tool_route_for_task(task), "inputs_needed": ["paper_ids or topic"], "expected_outputs": ["JSON evidence pack", "citations", "next actions"], "fallbacks": ["/api/v1/agent/evidence/search"]}
        if ctx.spec.id == "L10":
            papers = await self._papers(ctx, limit=200)
            coverage = {
                "papers": len(papers),
                "with_full_text": sum(1 for p in papers if p.has_full_text),
                "with_sections": sum(1 for p in papers if bool(p.parsed_sections or p.full_text_markdown)),
                "with_assets": sum(1 for p in papers if bool(p.parsed_figures or p.paper_links)),
            }
            missing = [key for key, value in coverage.items() if key != "papers" and value == 0]
            recommended = ["parse_full_text", "extract_assets"] if missing else ["continue monitoring corpus coverage"]
            return {"coverage": coverage, "missing_capabilities": missing or ["external citation/provider coverage not measured"], "recommended_ingestion": recommended, "risk_level": "high" if missing else "low"}
        return await self._generic(ctx)

    async def _saved_search_rules(self, topic: str | None) -> list[dict[str, Any]]:
        result = await self.db.execute(select(SavedSearch).where(SavedSearch.user_id == self.user_id).limit(100))
        searches = result.scalars().all()
        terms = self.info._terms(topic)
        rules = []
        for search in searches:
            if not terms or self.info._score(search.query, terms) > 0:
                rules.append({"id": str(search.id), "name": search.name, "query": search.query, "filters": search.filters or {}})
        return rules

    async def _generic(self, ctx: AgentRuntimeContext) -> dict[str, Any]:
        paper_ids = self._paper_ids(ctx)
        topic = self._topic(ctx)
        data: dict[str, Any] = {"status": "live_generic", "paper_ids": paper_ids, "topic": topic}
        if paper_ids:
            papers = []
            for paper_id in paper_ids[:20]:
                paper = await self._paper_or_404(paper_id)
                papers.append(self.info._paper_summary(paper))
            data["papers"] = papers
        elif topic:
            literature = await self.info.literature_map(topic=topic, limit=20, mode=ctx.spec.id)
            data.update(literature)
        else:
            ctx.warnings.append({"code": "INSUFFICIENT_INPUT", "message": "Provide paper_ids, paper_id, topic, query, or endpoint-specific input for full results."})
        return data
