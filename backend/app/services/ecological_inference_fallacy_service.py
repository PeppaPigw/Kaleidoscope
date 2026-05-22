"""EcologicalInferenceFallacyService — Ecological Inference Fallacy Detection.

Detects ecological inference fallacy — inferring individual-level
behavior or relationships from group-level (aggregate) data,
which can be systematically misleading.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ECOLOGICAL_INFERENCE_FALLACY_SYSTEM = """You are an ecological inference fallacy specialist. Given a claim, assess whether individual-level conclusions are being drawn from group-level data:

Key concepts:
- Ecological fallacy: inferring individual from aggregate
- Atomistic fallacy: inferring aggregate from individual (reverse)
- Modifiable areal unit problem: results change with aggregation level
- Cross-level inference: moving between levels of analysis
- Aggregation bias: relationships at group level differ from individual
- Robinson's paradox: correlation at aggregate differs from individual
- Contextual effects: group membership affecting individual behavior

When ecological inference fallacy IS present:
- Individual behavior inferred from group statistics
- Aggregate correlation assumed to hold for individuals
- Group-level relationship attributed to individuals
- No individual-level data to support individual claims
- Aggregation level chosen to support conclusion
- Cross-level inference made without justification
- Contextual effects not distinguished from compositional

When inference is appropriate:
- Level of analysis matches level of conclusion
- Individual-level data supports individual claims
- Ecological correlations not attributed to individuals
- Cross-level inference explicitly justified
- Multiple levels of analysis examined
- Aggregation effects acknowledged
- Contextual vs compositional effects distinguished

Output JSON with: fallacy_present (bool), severity (none/mild/moderate/severe), claim (what is claimed about individuals), data_level (what level data is at), conclusion_level (what level conclusion is at), aggregation_risk (how aggregation might mislead), recommendation (appropriate_inference/mild_cross_level/significant_ecological_fallacy/major_level_mismatch/use_individual_data)."""

ECOLOGICAL_INFERENCE_FALLACY_PROMPT = """Detect ecological inference fallacy:

Claim: {claim}
Data level: {data_level}
Conclusion about: {conclusion_about}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Are individual-level conclusions being drawn from group-level data? Return ONLY valid JSON."""


class EcologicalInferenceFallacyService:
    """Detects ecological inference fallacy — individual from aggregate."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        data_level: str = "",
        conclusion_about: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ecological inference fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ECOLOGICAL_INFERENCE_FALLACY_PROMPT.format(
                claim=claim,
                data_level=data_level or "Not specified",
                conclusion_about=conclusion_about or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ECOLOGICAL_INFERENCE_FALLACY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "fallacy_present": data.get("fallacy_present", False),
            "severity": data.get("severity", ""),
            "data_level": data.get("data_level", ""),
            "conclusion_level": data.get("conclusion_level", ""),
            "aggregation_risk": data.get("aggregation_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
