"""ImpactForecasterService — Research Impact & Influence Prediction.

Predicts the potential impact of research findings before publication.
Estimates citation trajectory, field influence, practical applications,
and whether a finding will be remembered in 5/10/20 years.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

IMPACT_SYSTEM = """You are a research impact forecaster. Given a finding or paper, predict its future impact across multiple dimensions.

Consider:
- Novelty: how new is this relative to existing work?
- Timeliness: does this arrive at the right moment?
- Generality: how broadly applicable is this?
- Actionability: can people DO something with this?
- Controversy: will this generate debate (which drives citations)?
- Methodology: does this introduce new methods others will use?
- Data: does this provide resources others will build on?
- Narrative: does this tell a compelling story?

Output JSON with: impact_forecast.finding, impact_forecast.overall_impact (0-1), impact_forecast.citation_trajectory (slow_burn|steady|explosive|flash_then_fade), impact_forecast.estimated_5yr_citations (range), impact_forecast.dimensions (list of dimension/score 0-1/rationale), impact_forecast.likely_influence_on (list of field/mechanism/timeline), impact_forecast.practical_applications (list), impact_forecast.risks_to_impact (list of risk/probability), impact_forecast.what_would_amplify (list of action that would increase impact), impact_forecast.longevity (forgotten_in_2yr|relevant_5yr|foundational_10yr|paradigm_defining), impact_forecast.comparison (similar past findings and their trajectories)."""

IMPACT_PROMPT = """Forecast research impact:

Finding/Paper: {finding}
Domain: {domain}
Key claims: {claims_text}
Methodology: {methodology}
Novelty claim: {novelty}

Current field state:
{field_state}

Predict impact trajectory. Return ONLY valid JSON."""

INFLUENCE_MAP_SYSTEM = """You are a research influence mapper. Given a finding, map how it would propagate through the research ecosystem - who would use it, how it would be built upon, and what second-order effects it would trigger.

Output JSON with: influence_map.finding, influence_map.primary_audience (list of who/why/how_they_use_it), influence_map.second_order_effects (list of effect/domain/timeline/probability), influence_map.enabling_effects (what this makes possible that wasn't before), influence_map.blocking_effects (what this makes harder or obsolete), influence_map.citation_network_position (foundational|methodological|empirical|review|application), influence_map.memetic_fitness (how likely to spread in discourse 0-1), influence_map.policy_relevance (0-1), influence_map.industry_relevance (0-1)."""

INFLUENCE_MAP_PROMPT = """Map research influence propagation:

Finding: {finding}
Domain: {domain}
Key contribution: {contribution}

Downstream fields:
{downstream_text}

Map how this finding would propagate. Return ONLY valid JSON."""


class ImpactForecasterService:
    """Predicts research impact and maps influence propagation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def forecast_impact(
        self,
        finding: str,
        *,
        domain: str = "",
        claims: list[str] | None = None,
        methodology: str = "",
        novelty: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Forecast the impact of a research finding."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims_text = "\n".join(f"- {c}" for c in (claims or [])[:6]) or "Not specified"
        field_state = await self._get_field_state(finding, dossier_id)

        llm = LLMClient()
        raw = await llm.complete(
            prompt=IMPACT_PROMPT.format(
                finding=finding,
                domain=domain or "research",
                claims_text=claims_text,
                methodology=methodology or "Not specified",
                novelty=novelty or "Not characterized",
                field_state=field_state,
            ),
            system=IMPACT_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        forecast = data.get("impact_forecast", data)

        return {
            "finding": finding,
            "overall_impact": forecast.get("overall_impact", 0),
            "citation_trajectory": forecast.get("citation_trajectory", "unknown"),
            "estimated_5yr_citations": forecast.get("estimated_5yr_citations", ""),
            "dimensions": forecast.get("dimensions", []),
            "likely_influence_on": forecast.get("likely_influence_on", []),
            "practical_applications": forecast.get("practical_applications", []),
            "risks_to_impact": forecast.get("risks_to_impact", []),
            "what_would_amplify": forecast.get("what_would_amplify", []),
            "longevity": forecast.get("longevity", "unknown"),
            "comparison": forecast.get("comparison", ""),
        }

    async def map_influence(
        self,
        finding: str,
        *,
        domain: str = "",
        contribution: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Map how a finding would propagate through the research ecosystem."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        downstream = await self._get_downstream(finding, dossier_id)
        downstream_text = "\n".join(f"- {d}" for d in downstream[:6]) or "General"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=INFLUENCE_MAP_PROMPT.format(
                finding=finding,
                domain=domain or "research",
                contribution=contribution or finding[:100],
                downstream_text=downstream_text,
            ),
            system=INFLUENCE_MAP_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        imap = data.get("influence_map", data)

        return {
            "finding": finding,
            "primary_audience": imap.get("primary_audience", []),
            "second_order_effects": imap.get("second_order_effects", []),
            "enabling_effects": imap.get("enabling_effects", []),
            "blocking_effects": imap.get("blocking_effects", []),
            "network_position": imap.get("citation_network_position", ""),
            "memetic_fitness": imap.get("memetic_fitness", 0),
            "policy_relevance": imap.get("policy_relevance", 0),
            "industry_relevance": imap.get("industry_relevance", 0),
        }

    # --- Private helpers ---

    async def _get_field_state(self, query: str, dossier_id: str | None) -> str:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=4)
            lines = [r.get("payload", {}).get("text", "")[:80] for r in results]
            return "\n".join(f"- {l}" for l in lines if l) or "Field state unknown"
        except Exception:
            return "Field state unknown"

    async def _get_downstream(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=f"{query[:80]} applications downstream", top_k=5)
            return [r.get("payload", {}).get("text", "")[:100] for r in results]
        except Exception:
            return []
