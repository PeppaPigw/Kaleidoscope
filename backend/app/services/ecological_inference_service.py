"""EcologicalInferenceService — Ecological Inference Fallacy Detection.

Detects ecological inference fallacy — drawing conclusions about
individual behavior or characteristics from aggregate group-level
data. What is true of a group may not be true of its members.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ECOLOGICAL_INFERENCE_SYSTEM = """You are an ecological inference specialist. Given a claim, assess whether it inappropriately draws individual-level conclusions from group-level data:

Key concepts:
- Ecological fallacy: inferring individual traits from group statistics
- Aggregation bias: group-level patterns don't imply individual patterns
- Simpson's paradox: group trends can reverse at individual level
- Modifiable areal unit problem: results change with grouping boundaries
- Individual vs aggregate: correlation at one level ≠ correlation at other
- Cross-level inference: moving between levels of analysis
- Atomistic fallacy: the reverse — inferring group from individual

When ecological inference IS present:
- "Country X has high Y, so people in X must have high Y"
- Drawing individual conclusions from census/aggregate data
- "Neighborhoods with more Z have more W, so Z causes W in individuals"
- Assuming group averages apply to all members
- Using regional correlations to make claims about personal behavior
- Ignoring within-group variation
- Treating ecological correlations as individual correlations

When ecological inference is NOT present:
- Individual-level data supports the claim
- The claim is explicitly about groups, not individuals
- Multi-level analysis accounts for both group and individual effects
- The inference is about institutional/structural effects (appropriate level)
- Within-group variation is acknowledged
- The ecological data is used as one piece of evidence among many
- The claim is about probabilities, not certainties

Output JSON with: ecological_inference_present (bool), severity (none/mild/moderate/severe), claim (what is concluded), data_level (what level the data is at), inference_level (what level the conclusion is at), within_group_variation (is variation acknowledged), recommendation (no_ecological_fallacy/mild_level_confusion/significant_ecological_inference/major_cross_level_error/use_individual_data)."""

ECOLOGICAL_INFERENCE_PROMPT = """Detect ecological inference fallacy:

Claim: {claim}
Data source: {data_source}
Data level: {data_level}
Conclusion level: {conclusion_level}
Domain: {domain}
Context: {context}

Does this draw individual-level conclusions from group-level data? Return ONLY valid JSON."""


class EcologicalInferenceService:
    """Detects ecological inference — individual conclusions from group data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        data_source: str = "",
        data_level: str = "",
        conclusion_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ecological inference fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ECOLOGICAL_INFERENCE_PROMPT.format(
                claim=claim,
                data_source=data_source or "Not specified",
                data_level=data_level or "Not specified",
                conclusion_level=conclusion_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ECOLOGICAL_INFERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "ecological_inference_present": data.get("ecological_inference_present", False),
            "severity": data.get("severity", ""),
            "data_level": data.get("data_level", ""),
            "inference_level": data.get("inference_level", ""),
            "within_group_variation": data.get("within_group_variation", ""),
            "recommendation": data.get("recommendation", ""),
        }
