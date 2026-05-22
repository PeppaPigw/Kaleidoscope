"""BiasDetectorService — Specific Cognitive Bias Identification.

Identifies specific cognitive biases in an argument — not just "bias
exists" but which specific bias, where in the argument it operates,
and how it distorts the conclusion. Maps to the taxonomy of known biases.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BIAS_SYSTEM = """You are a cognitive bias detection specialist. Given an argument, identify specific cognitive biases at work:
- Name the specific bias (anchoring, availability heuristic, survivorship bias, confirmation bias, etc.)
- Show exactly WHERE in the argument it operates
- Explain HOW it distorts the conclusion
- Assess how much the conclusion would change if the bias were corrected
- Distinguish between biases that invalidate the argument vs merely weaken it

Output JSON with: biases_detected (list of: bias_name, bias_category (cognitive/motivational/social/statistical), location_in_argument (which part), how_it_distorts (mechanism), severity (minor/moderate/major/invalidating), debiased_conclusion (what you'd conclude without this bias)), overall_bias_load (low/moderate/high/extreme), most_damaging_bias (which one matters most), debiased_verdict (the conclusion after correcting for all biases), bias_direction (which direction do the biases collectively push), confidence_after_debiasing (0-1)."""

BIAS_PROMPT = """Detect cognitive biases in this argument:

Argument: {argument}
Conclusion claimed: {conclusion}
Domain: {domain}
Context: {context}

Which specific biases are at work? Return ONLY valid JSON."""


class BiasDetectorService:
    """Detects specific cognitive biases in arguments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cognitive biases in an argument."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIAS_PROMPT.format(
                argument=argument,
                conclusion=conclusion or "Not explicitly stated",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        biases = data.get("biases_detected", [])
        return {
            "argument": argument[:200],
            "biases_count": len(biases),
            "biases_detected": biases,
            "overall_bias_load": data.get("overall_bias_load", ""),
            "most_damaging_bias": data.get("most_damaging_bias", ""),
            "debiased_verdict": data.get("debiased_verdict", ""),
            "bias_direction": data.get("bias_direction", ""),
            "confidence_after_debiasing": data.get("confidence_after_debiasing", 0),
        }
