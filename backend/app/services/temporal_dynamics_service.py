"""TemporalDynamicsService — Research Temporal Intelligence.

Analyzes how research findings, consensus, and evidence evolve over time.
Detects acceleration/deceleration of fields, predicts paradigm shifts,
identifies when findings are becoming stale, and maps research momentum.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOMENTUM_SYSTEM = """You are a research momentum analyst. Given a field or topic, analyze its temporal dynamics: is it accelerating, plateauing, or declining? When did key inflection points occur? What's driving the current trajectory?

Output JSON with: momentum.topic, momentum.current_phase (emerging|accelerating|peak|plateauing|declining|dormant|reviving), momentum.velocity (0-1 rate of new findings), momentum.acceleration (positive/negative/zero), momentum.inflection_points (list of year/event/what_changed), momentum.drivers (list of driver/strength 0-1), momentum.predicted_trajectory (next 2-5 years), momentum.half_life (how long until current findings become outdated), momentum.comparison_fields (list of similar_field/their_phase/lesson)."""

MOMENTUM_PROMPT = """Analyze research momentum:

Topic/Field: {topic}
Domain: {domain}
Time horizon: {time_horizon}

Known recent developments:
{developments_text}

Analyze temporal dynamics. Return ONLY valid JSON."""

STALENESS_SYSTEM = """You are a research freshness auditor. Given a finding and its publication context, assess whether it is still current, becoming stale, or already outdated. Consider replication status, superseding work, and field evolution.

Output JSON with: staleness.finding, staleness.publication_year, staleness.freshness_score (0-1 where 1 is fully current), staleness.status (current|aging|stale|outdated|superseded), staleness.threats_to_validity (list of threat/severity/when_it_emerged), staleness.superseding_work (list of what/when/how_it_changes_things), staleness.still_valid_aspects (list), staleness.recommendation (keep|update|replace|archive), staleness.update_urgency (critical|high|medium|low|none)."""

STALENESS_PROMPT = """Assess finding freshness:

Finding: {finding}
Published: {year}
Domain: {domain}
Original context: {context}

Is this still current? Return ONLY valid JSON."""


class TemporalDynamicsService:
    """Analyzes temporal dynamics of research fields and findings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_momentum(
        self,
        topic: str,
        *,
        domain: str = "",
        time_horizon: str = "5 years",
        dossier_id: str | None = None,
    ) -> dict:
        """Analyze research momentum and trajectory of a field."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        developments = await self._gather_context(topic, dossier_id)
        developments_text = "\n".join(f"- {d}" for d in developments[:8]) or "Infer from domain knowledge"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOMENTUM_PROMPT.format(
                topic=topic,
                domain=domain or "research",
                time_horizon=time_horizon,
                developments_text=developments_text,
            ),
            system=MOMENTUM_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        mom = data.get("momentum", data)

        return {
            "topic": topic,
            "current_phase": mom.get("current_phase", "unknown"),
            "velocity": mom.get("velocity", 0),
            "acceleration": mom.get("acceleration", "zero"),
            "inflection_points": mom.get("inflection_points", []),
            "drivers": mom.get("drivers", []),
            "predicted_trajectory": mom.get("predicted_trajectory", ""),
            "half_life": mom.get("half_life", ""),
            "comparison_fields": mom.get("comparison_fields", []),
        }

    async def assess_staleness(
        self,
        finding: str,
        *,
        year: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Assess whether a finding is still current or becoming stale."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STALENESS_PROMPT.format(
                finding=finding,
                year=year or "unknown",
                domain=domain or "research",
                context=context or "Standard academic publication",
            ),
            system=STALENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)
        stale = data.get("staleness", data)

        return {
            "finding": finding,
            "freshness_score": stale.get("freshness_score", 0),
            "status": stale.get("status", "unknown"),
            "threats_to_validity": stale.get("threats_to_validity", []),
            "superseding_work": stale.get("superseding_work", []),
            "still_valid_aspects": stale.get("still_valid_aspects", []),
            "recommendation": stale.get("recommendation", ""),
            "update_urgency": stale.get("update_urgency", ""),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{query[:80]} recent developments", top_k=6)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
