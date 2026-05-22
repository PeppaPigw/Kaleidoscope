"""ConsensusMapperService — Social Epistemology & Agreement Landscape.

Maps the landscape of agreement and disagreement across a research field.
Not just "what do we know" but "who agrees with whom, why, and what would
change their mind." Identifies consensus, active controversies, and the
fault lines where the field might split.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONSENSUS_MAP_SYSTEM = """You are a social epistemology analyst mapping the agreement landscape of a research field. For a given question, identify where consensus exists, where genuine disagreement persists, and what drives the disagreement.

Output JSON with: consensus_map.question, consensus_map.consensus_claims (list of claim/agreement_level 0-1/evidence_basis/dissenters), consensus_map.active_controversies (list of controversy/camp_a/camp_b/crux_of_disagreement/what_would_resolve_it), consensus_map.emerging_consensus (claims gaining agreement), consensus_map.dissolving_consensus (claims losing agreement), consensus_map.fault_lines (fundamental disagreements that may split the field), consensus_map.overall_coherence (0-1), consensus_map.maturity (pre_paradigmatic|normal_science|crisis|revolutionary)."""

CONSENSUS_MAP_PROMPT = """Map the consensus landscape:

Research question: {question}
Domain: {domain}

Known positions and claims:
{claims_text}

Evidence state:
{evidence_text}

Map where agreement and disagreement exist. Return ONLY valid JSON."""

CONTROVERSY_SYSTEM = """You are a controversy analyst. Given a specific scientific controversy, map it in detail: who believes what, why, what evidence each side cites, and what would change minds.

Output JSON with: controversy.topic, controversy.camps (list of name/position/key_proponents/evidence_cited/methodology_preferred/philosophical_commitments), controversy.crux (the single deepest disagreement), controversy.empirical_tests (what experiments could settle this), controversy.meta_disagreements (disagreements about how to disagree), controversy.resolution_probability (0-1), controversy.timeline_to_resolution, controversy.stakes (what depends on the outcome)."""

CONTROVERSY_PROMPT = """Analyze this controversy in detail:

Topic: {topic}
Domain: {domain}

Known positions:
{positions_text}

Evidence available:
{evidence_text}

Map the controversy structure. Return ONLY valid JSON."""


class ConsensusMapperService:
    """Maps agreement/disagreement landscapes in research fields."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def map_consensus(
        self,
        question: str,
        *,
        domain: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Map the consensus landscape for a research question."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        claims = await self._gather_claims(question, dossier_id)
        claims_text = "\n".join(f"- {c}" for c in claims[:10]) or "General knowledge"
        evidence = await self._gather_evidence(question)
        evidence_text = "\n".join(f"- {e}" for e in evidence[:8]) or "Limited"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONSENSUS_MAP_PROMPT.format(
                question=question,
                domain=domain or "research",
                claims_text=claims_text,
                evidence_text=evidence_text,
            ),
            system=CONSENSUS_MAP_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        cmap = data.get("consensus_map", data)

        return {
            "question": question,
            "consensus_claims": cmap.get("consensus_claims", []),
            "active_controversies": cmap.get("active_controversies", []),
            "emerging_consensus": cmap.get("emerging_consensus", []),
            "dissolving_consensus": cmap.get("dissolving_consensus", []),
            "fault_lines": cmap.get("fault_lines", []),
            "overall_coherence": cmap.get("overall_coherence", 0),
            "maturity": cmap.get("maturity", "unknown"),
        }

    async def analyze_controversy(
        self,
        topic: str,
        *,
        domain: str = "",
        positions: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Deep-dive into a specific controversy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        positions_text = "\n".join(f"- {p}" for p in (positions or [])) or "Not specified"
        evidence = await self._gather_evidence(topic)
        evidence_text = "\n".join(f"- {e}" for e in evidence[:8]) or "Limited"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONTROVERSY_PROMPT.format(
                topic=topic,
                domain=domain or "research",
                positions_text=positions_text,
                evidence_text=evidence_text,
            ),
            system=CONTROVERSY_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        controversy = data.get("controversy", data)

        return {
            "topic": topic,
            "camps": controversy.get("camps", []),
            "crux": controversy.get("crux", ""),
            "empirical_tests": controversy.get("empirical_tests", []),
            "meta_disagreements": controversy.get("meta_disagreements", []),
            "resolution_probability": controversy.get("resolution_probability", 0),
            "timeline": controversy.get("timeline_to_resolution", ""),
            "stakes": controversy.get("stakes", ""),
        }

    # --- Private helpers ---

    async def _gather_claims(self, query: str, dossier_id: str | None) -> list[str]:
        claims = []
        if dossier_id:
            try:
                from app.models.dossier import ResearchDossier
                from sqlalchemy import select
                stmt = select(ResearchDossier).where(ResearchDossier.id == dossier_id)
                result = await self.db.execute(stmt)
                dossier = result.scalar_one_or_none()
                if dossier and dossier.claims:
                    for c in dossier.claims[:10]:
                        if isinstance(c, dict):
                            claims.append(c.get("text", c.get("claim", str(c)))[:200])
                        else:
                            claims.append(str(c)[:200])
            except Exception:
                pass
        if not claims:
            try:
                from app.services.search.vector_search import VectorSearchService
                svc = VectorSearchService()
                results = svc.search(query=query[:150], top_k=8)
                for r in results:
                    p = r.get("payload", {})
                    claims.append(p.get("text", p.get("title", ""))[:200])
            except Exception:
                pass
        return claims

    async def _gather_evidence(self, query: str) -> list[str]:
        evidence = []
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:150], top_k=6)
            for r in results:
                p = r.get("payload", {})
                evidence.append(p.get("text", p.get("title", ""))[:150])
        except Exception:
            pass
        return evidence
