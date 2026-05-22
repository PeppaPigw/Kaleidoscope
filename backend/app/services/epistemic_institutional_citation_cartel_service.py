"""EpistemicInstitutionalCitationCartelService - Citation Cartel Detection.

Detects citation cartels where mutual citation inflates apparent support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INSTITUTIONAL_CITATION_CARTEL_SYSTEM = """You are an epistemic institutional citation cartel specialist. Given citation patterns, assess whether mutual citation inflates apparent support:

Key concepts:
- Citation cartel: groups mutually citing each other to inflate metrics and apparent support
- Reciprocal inflation: I-cite-you-you-cite-me arrangements
- False consensus: appearance of broad support from narrow network
- Metric gaming: manipulating citation counts for institutional benefit

When citation cartel IS present:
- Mutual citation patterns evident
- Support appears broader than reality
- Metrics artificially inflated
- Network is closed and self-referencing
- Independent validation absent

When no citation cartel:
- Citations reflect genuine intellectual debt
- Support reflects independent convergence
- Metrics reflect real impact
- Network is open and diverse
- Independent validation present

Output JSON with: citation_cartel_detected (bool), severity (none/mild/moderate/severe), reciprocal_inflation (what reciprocal inflation), false_consensus (what false consensus), metric_gaming (what metric gaming), recommendation (no_citation_cartel/mild_network_check/significant_independence_needed/major_citation_reconstruction/emergency_complete_citation_cartel)."""

EPISTEMIC_INSTITUTIONAL_CITATION_CARTEL_PROMPT = """Detect epistemic institutional citation cartel:

Citation pattern: {citation_pattern}
Reciprocal inflation: {reciprocal_inflation}
False consensus: {false_consensus}
Metric gaming: {metric_gaming}
Domain: {domain}
Context: {context}

Is mutual citation inflating apparent support? Return ONLY valid JSON."""


class EpistemicInstitutionalCitationCartelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        citation_pattern: str,
        *,
        reciprocal_inflation: str = "",
        false_consensus: str = "",
        metric_gaming: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INSTITUTIONAL_CITATION_CARTEL_PROMPT.format(
                citation_pattern=citation_pattern,
                reciprocal_inflation=reciprocal_inflation or "Not specified",
                false_consensus=false_consensus or "Not specified",
                metric_gaming=metric_gaming or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INSTITUTIONAL_CITATION_CARTEL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "citation_pattern": citation_pattern[:200],
            "citation_cartel_detected": data.get("citation_cartel_detected", False),
            "severity": data.get("severity", ""),
            "reciprocal_inflation": data.get("reciprocal_inflation", ""),
            "false_consensus": data.get("false_consensus", ""),
            "metric_gaming": data.get("metric_gaming", ""),
            "recommendation": data.get("recommendation", ""),
        }
