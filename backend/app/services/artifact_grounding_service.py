"""ArtifactGroundingService — Artifact Grounding Compiler.

Bridges literature reasoning to runnable research by resolving papers/claims
to code repos, datasets, model checkpoints, and benchmarks. Provides
reproducibility audits, replication runbooks, and execution-evidence ingestion.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ARTIFACT_SYSTEM = """You are an artifact resolver for research intelligence. Given a paper or claim, identify all linked external artifacts: GitHub repos, Hugging Face models/datasets, project pages, benchmarks, checkpoints, and model cards.

Output JSON only:
{"artifacts": [{"id": "art_1", "type": "repo|dataset|model|benchmark|checkpoint|project_page", "name": "short name", "url": "canonical URL or null", "source_hint": "where in the paper this was mentioned", "relation_to_claim": "implements|evaluates|trains_on|produces|replicates", "confidence": 0.0-1.0}], "unresolved": ["artifact mentioned but not locatable"]}"""

ARTIFACT_PROMPT = """Paper/claim context:
Title: {title}
Abstract/text: {text}

Known URLs or references:
{references}

Claims to ground:
{claims_text}

Resolve all external artifacts. Return ONLY valid JSON."""

REPRO_SYSTEM = """You are a reproducibility auditor. Given a paper's artifacts (repos, datasets, models), assess operational completeness and reproducibility risk.

Score each dimension 0-100:
- code_available: Is source code accessible?
- data_available: Are datasets accessible and complete?
- env_specified: Are dependencies, hardware, seeds documented?
- results_reproducible: Can claimed results be independently verified?
- benchmark_coverage: Do available benchmarks match paper claims?

Output JSON only:
{"overall_score": 0-100, "dimensions": {"code_available": 0-100, "data_available": 0-100, "env_specified": 0-100, "results_reproducible": 0-100, "benchmark_coverage": 0-100}, "blockers": [{"type": "missing_code|missing_data|broken_link|license|env_ambiguity|hardware_gap|seed_missing", "description": "what's missing", "severity": "critical|major|minor"}], "strengths": ["what's good"], "recommendation": "one sentence"}"""

REPRO_PROMPT = """Paper: {title}

Artifacts found:
{artifacts_text}

Known environment info:
{env_text}

Claims that depend on these artifacts:
{claims_text}

Audit reproducibility. Return ONLY valid JSON."""

RUNBOOK_SYSTEM = """You are a replication engineer. Given a paper, its artifacts, and target claims, compile a step-by-step replication runbook that an automated system could execute.

Output JSON only:
{"runbook": {"title": "short title", "objective": "what we're verifying", "prerequisites": [{"item": "what's needed", "how_to_get": "instruction"}], "steps": [{"step": 1, "action": "what to do", "command": "shell command or null", "expected_output": "what success looks like", "failure_mode": "what failure looks like"}], "success_criteria": [{"metric": "name", "threshold": "value", "comparison": "gt|lt|eq|within"}], "estimated_duration": "timeframe", "hardware_requirements": "description", "risk_factors": ["what could go wrong"]}}"""

RUNBOOK_PROMPT = """Paper: {title}
Target claims to verify:
{claims_text}

Available artifacts:
{artifacts_text}

Environment spec:
{env_text}

Constraints: {constraints}

Compile a replication runbook. Return ONLY valid JSON."""

ENV_SYSTEM = """You are an environment extraction specialist. Given a paper and its code artifacts, extract a normalized environment specification.

Output JSON only:
{"environment": {"language": "primary language", "framework": "primary framework", "dependencies": [{"name": "pkg", "version": "version or null", "required": true}], "hardware": {"gpu": "type or null", "gpu_count": 0, "ram_gb": 0, "storage_gb": 0}, "seeds": [0], "datasets": [{"name": "name", "source": "url or description", "size": "description", "preprocessing": "steps or null"}], "checkpoints": [{"name": "name", "source": "url", "size": "description"}], "entrypoints": [{"script": "path", "purpose": "what it does", "args": "key arguments"}], "docker_available": false, "ci_available": false}}"""

ENV_PROMPT = """Paper: {title}

Code artifacts:
{artifacts_text}

README/setup info (if available):
{readme_text}

Extract normalized environment spec. Return ONLY valid JSON."""


class ArtifactGroundingService:
    """Resolves papers/claims to external artifacts and audits reproducibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_artifact_graph(
        self,
        dossier_id: str,
        *,
        paper_id: str | None = None,
        claim_ids: list[str] | None = None,
    ) -> dict:
        """Discover, deduplicate, and link external artifacts for papers/claims."""
        from app.clients.llm_client import LLMClient

        context = await self._gather_context(dossier_id, paper_id, claim_ids)
        if context.get("error"):
            return context

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ARTIFACT_PROMPT.format(
                title=context["title"],
                text=context["text"][:500],
                references=context["references"],
                claims_text=context["claims_text"],
            ),
            system=ARTIFACT_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        artifacts = data.get("artifacts", [])

        for art in artifacts:
            art["artifact_id"] = art.get("id", str(uuid.uuid4())[:8])
            art["dossier_id"] = dossier_id
            if paper_id:
                art["paper_id"] = paper_id
            art["resolved_at"] = datetime.now(timezone.utc).isoformat()

        edges = []
        for art in artifacts:
            if claim_ids:
                for cid in claim_ids[:5]:
                    edges.append({
                        "from": art["artifact_id"],
                        "to": cid,
                        "relation": art.get("relation_to_claim", "related"),
                    })
            if paper_id:
                edges.append({
                    "from": art["artifact_id"],
                    "to": paper_id,
                    "relation": "extracted_from",
                })

        return {
            "dossier_id": dossier_id,
            "artifacts": artifacts,
            "edges": edges,
            "unresolved": data.get("unresolved", []),
            "stats": {
                "total_artifacts": len(artifacts),
                "repos": len([a for a in artifacts if a.get("type") == "repo"]),
                "datasets": len([a for a in artifacts if a.get("type") == "dataset"]),
                "models": len([a for a in artifacts if a.get("type") == "model"]),
                "benchmarks": len([a for a in artifacts if a.get("type") == "benchmark"]),
            },
        }

    async def audit_reproducibility(
        self,
        dossier_id: str,
        *,
        paper_id: str | None = None,
        artifacts: list[dict] | None = None,
    ) -> dict:
        """Score artifact completeness and reproducibility."""
        from app.clients.llm_client import LLMClient

        if not artifacts:
            graph = await self.compile_artifact_graph(dossier_id, paper_id=paper_id)
            artifacts = graph.get("artifacts", [])

        if not artifacts:
            return {
                "error": "No artifacts found to audit",
                "dossier_id": dossier_id,
                "overall_score": 0,
            }

        context = await self._gather_context(dossier_id, paper_id)
        claims = await self._get_dossier_claims(dossier_id)

        artifacts_text = "\n".join(
            f"- [{a.get('type', '?')}] {a.get('name', '?')}: {a.get('url', 'no URL')} "
            f"(confidence={a.get('confidence', 0):.1f})"
            for a in artifacts[:10]
        )
        env_text = "Not yet extracted"
        claims_text = "\n".join(
            f"- {c.get('text', '')[:100]}" for c in claims[:8]
        ) or "No specific claims"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REPRO_PROMPT.format(
                title=context.get("title", "Unknown"),
                artifacts_text=artifacts_text,
                env_text=env_text,
                claims_text=claims_text,
            ),
            system=REPRO_SYSTEM,
            max_tokens=1536,
            temperature=0.2,
        )
        audit = self._parse_json(raw)

        return {
            "dossier_id": dossier_id,
            "paper_id": paper_id,
            "overall_score": audit.get("overall_score", 0),
            "dimensions": audit.get("dimensions", {}),
            "blockers": audit.get("blockers", []),
            "strengths": audit.get("strengths", []),
            "recommendation": audit.get("recommendation", ""),
            "artifacts_audited": len(artifacts),
        }

    async def extract_environment(
        self,
        dossier_id: str,
        *,
        paper_id: str | None = None,
        artifacts: list[dict] | None = None,
    ) -> dict:
        """Extract normalized environment spec from artifacts."""
        from app.clients.llm_client import LLMClient

        if not artifacts:
            graph = await self.compile_artifact_graph(dossier_id, paper_id=paper_id)
            artifacts = graph.get("artifacts", [])

        context = await self._gather_context(dossier_id, paper_id)

        artifacts_text = "\n".join(
            f"- [{a.get('type', '?')}] {a.get('name', '?')}: {a.get('url', 'no URL')}"
            for a in artifacts[:8]
        )
        readme_text = context.get("text", "")[:400]

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ENV_PROMPT.format(
                title=context.get("title", "Unknown"),
                artifacts_text=artifacts_text,
                readme_text=readme_text,
            ),
            system=ENV_SYSTEM,
            max_tokens=1536,
            temperature=0.2,
        )
        data = self._parse_json(raw)

        return {
            "dossier_id": dossier_id,
            "paper_id": paper_id,
            "environment": data.get("environment", data),
            "artifacts_analyzed": len(artifacts),
        }

    async def compile_replication_plan(
        self,
        dossier_id: str,
        *,
        paper_id: str | None = None,
        claim_ids: list[str] | None = None,
        constraints: dict | None = None,
    ) -> dict:
        """Compile a stepwise replication/verification runbook."""
        from app.clients.llm_client import LLMClient

        context = await self._gather_context(dossier_id, paper_id, claim_ids)
        graph = await self.compile_artifact_graph(
            dossier_id, paper_id=paper_id, claim_ids=claim_ids
        )
        artifacts = graph.get("artifacts", [])
        env_result = await self.extract_environment(
            dossier_id, paper_id=paper_id, artifacts=artifacts
        )

        claims_text = context.get("claims_text", "No specific claims")
        artifacts_text = "\n".join(
            f"- [{a.get('type', '?')}] {a.get('name', '?')}: {a.get('url', 'no URL')}"
            for a in artifacts[:8]
        )
        env_text = str(env_result.get("environment", {}))[:300]
        constraints_text = str(constraints or {"budget": "medium", "hardware": "single GPU"})

        llm = LLMClient()
        raw = await llm.complete(
            prompt=RUNBOOK_PROMPT.format(
                title=context.get("title", "Unknown"),
                claims_text=claims_text,
                artifacts_text=artifacts_text,
                env_text=env_text,
                constraints=constraints_text,
            ),
            system=RUNBOOK_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        data = self._parse_json(raw)
        runbook = data.get("runbook", data)

        return {
            "dossier_id": dossier_id,
            "paper_id": paper_id,
            "runbook": runbook,
            "artifacts_used": len(artifacts),
            "claims_targeted": len(claim_ids or []),
        }

    async def ingest_execution_result(
        self,
        dossier_id: str,
        *,
        runbook_title: str,
        results: dict,
        target_claim_ids: list[str] | None = None,
    ) -> dict:
        """Ingest execution results and propagate into claims/confidence."""
        from app.clients.llm_client import LLMClient
        from app.services.experiment_compiler_service import ExperimentCompilerService

        exp_svc = ExperimentCompilerService(self.db)
        return await exp_svc.ingest_result(
            dossier_id,
            experiment_id=str(uuid.uuid4())[:8],
            experiment_title=f"Replication: {runbook_title}",
            hypothesis=f"Claims from {runbook_title} are reproducible",
            protocol={"type": "replication", "runbook": runbook_title},
            results=results,
            target_claim_ids=target_claim_ids,
        )

    async def create_drift_monitor(
        self,
        dossier_id: str,
        *,
        artifacts: list[dict],
        triggers: list[str] | None = None,
    ) -> dict:
        """Create a live monitor over linked artifacts."""
        from app.models.decision_monitor import DecisionMonitor

        default_triggers = [
            {"trigger": "Repository has new commits since last check", "type": "repo_update", "action": "re_audit"},
            {"trigger": "Dataset version changed", "type": "data_drift", "action": "re_audit"},
            {"trigger": "Model checkpoint updated or deprecated", "type": "model_drift", "action": "re_evaluate"},
            {"trigger": "Benchmark results changed on leaderboard", "type": "benchmark_drift", "action": "re_evaluate"},
            {"trigger": "Broken link detected in artifact URLs", "type": "link_rot", "action": "alert"},
        ]

        if triggers:
            for t in triggers:
                default_triggers.append({"trigger": t, "type": "custom", "action": "re_audit"})

        monitor = DecisionMonitor(
            dossier_id=uuid.UUID(dossier_id),
            decision_id=f"artifact_drift_{uuid.uuid4().hex[:8]}",
            decision_question=f"Are artifacts for dossier {dossier_id[:8]} still valid and reproducible?",
            recommended_option={"title": "Artifacts valid", "description": "All linked artifacts are accessible and current"},
            triggers=default_triggers,
            assumptions=[
                f"Artifact '{a.get('name', '?')}' at {a.get('url', '?')} is accessible"
                for a in artifacts[:5]
            ],
            boundary_conditions=[
                "Repository is archived or deleted",
                "Dataset license changes to restrictive",
                "Hardware requirements exceed available resources",
            ],
            decision_confidence=0.8,
            fragility_score=0.3,
            status="active",
            drift_score=0.0,
            version=1,
            recommendation_changed=False,
        )
        self.db.add(monitor)
        await self.db.commit()

        return {
            "monitor_id": str(monitor.id),
            "dossier_id": dossier_id,
            "status": "active",
            "artifacts_monitored": len(artifacts),
            "triggers_count": len(default_triggers),
            "type": "artifact_drift",
        }

    async def run_drift_check(
        self,
        monitor_id: str,
        *,
        artifacts: list[dict] | None = None,
    ) -> dict:
        """Run one drift pass over monitored artifacts."""
        from app.services.decision_watchtower_service import DecisionWatchtowerService

        watchtower = DecisionWatchtowerService(self.db)
        return await watchtower.run_check(
            monitor_id,
            lookback_days=30,
            budget_papers=3,
        )

    # ─── Internal helpers ─────────────────────────────────────────────

    async def _gather_context(
        self, dossier_id: str, paper_id: str | None = None, claim_ids: list[str] | None = None
    ) -> dict:
        from sqlalchemy import select
        from app.models.paper import Paper

        title = "Unknown"
        text = ""
        references = "None available"

        if paper_id:
            try:
                q = await self.db.execute(
                    select(Paper).where(Paper.id == uuid.UUID(paper_id))
                )
                paper = q.scalar_one_or_none()
                if paper:
                    title = paper.title or "Untitled"
                    text = paper.abstract or ""
                    urls = []
                    if paper.doi:
                        urls.append(f"DOI: {paper.doi}")
                    if hasattr(paper, 'url') and paper.url:
                        urls.append(f"URL: {paper.url}")
                    references = "\n".join(urls) or "None"
            except Exception as e:
                logger.warning("paper_fetch_error", error=str(e))

        claims = await self._get_dossier_claims(dossier_id, claim_ids)
        claims_text = "\n".join(
            f"- {c.get('text', '')[:120]}" for c in claims[:8]
        ) or "No specific claims"

        if not text and claims:
            text = " ".join(c.get("text", "") for c in claims[:3])
            title = claims[0].get("text", "")[:60] if claims else title

        return {
            "title": title,
            "text": text,
            "references": references,
            "claims_text": claims_text,
        }

    async def _get_dossier_claims(
        self, dossier_id: str, claim_ids: list[str] | None = None
    ) -> list[dict]:
        from sqlalchemy import select
        from app.models.claim_ledger import GlobalClaim, ClaimMention

        if claim_ids:
            uuids = [uuid.UUID(c) for c in claim_ids]
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
        else:
            mention_q = await self.db.execute(
                select(ClaimMention.global_claim_id)
                .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
                .distinct().limit(20)
            )
            cids = [r[0] for r in mention_q.all()]
            if not cids:
                return []
            q = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(cids))
            )

        claims = list(q.scalars().all())
        return [
            {"claim_id": str(c.id), "text": c.canonical_text}
            for c in claims[:15]
        ]

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)(?:\n?```|$)", text, re.DOTALL)
        if fence:
            try:
                return json.loads(fence.group(1).strip())
            except json.JSONDecodeError:
                repaired = self._repair_json(fence.group(1).strip())
                if repaired:
                    return repaired
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        return {}

    def _repair_json(self, text: str) -> dict | None:
        import json
        text = text.rstrip().rstrip(",")
        stack = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()
        if in_string:
            text += '"'
        text = text.rstrip().rstrip(",")
        text += ''.join(reversed(stack))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
