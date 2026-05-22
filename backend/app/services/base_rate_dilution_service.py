"""BaseRateDilutionService — Base Rate Dilution Detection.

Detects base rate dilution — when additional irrelevant or
weakly diagnostic information causes people to underweight
strong base rate evidence. The more detail provided, the
more base rates get diluted.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BASE_RATE_DILUTION_SYSTEM = """You are a base rate dilution specialist. Given a judgment, assess whether base rates are being diluted by irrelevant information:

Key concepts:
- Base rate dilution: irrelevant info weakens use of base rates
- Dilution effect: non-diagnostic info reduces impact of diagnostic info
- Pseudodiagnosticity: treating irrelevant features as diagnostic
- Information pollution: more data doesn't always mean better judgment
- Diagnostic vs non-diagnostic: only some information changes probabilities
- Representativeness override: vivid details override statistical base rates
- Bayesian updating: only diagnostic info should change posterior probability

When base rate dilution IS present:
- Strong base rate evidence ignored after receiving irrelevant details
- Non-diagnostic information treated as if it changes the probability
- More information leading to worse calibration
- Vivid but irrelevant details overriding statistical evidence
- Case-specific information diluting population-level data
- Personality descriptions overriding occupational base rates
- Irrelevant context making base rates seem less applicable

When base rate dilution is NOT present:
- Base rates properly weighted regardless of additional detail
- Non-diagnostic information recognized and set aside
- Only genuinely diagnostic info updates the probability
- Statistical evidence maintained despite vivid narratives
- Distinction made between relevant and irrelevant information
- Bayesian updating applied correctly
- Additional detail doesn't change judgment when non-diagnostic

Output JSON with: dilution_present (bool), severity (none/mild/moderate/severe), base_rate (the relevant base rate), diluting_info (what irrelevant info is diluting it), diagnosticity (how diagnostic is the additional info), proper_weight (what weight base rate should have), recommendation (no_dilution/mild_dilution/significant_dilution/major_base_rate_neglect/restore_base_rate)."""

BASE_RATE_DILUTION_PROMPT = """Detect base rate dilution:

Judgment: {judgment}
Base rate: {base_rate}
Additional info: {additional_info}
Conclusion: {conclusion}
Domain: {domain}
Context: {context}

Is irrelevant information diluting the use of base rates? Return ONLY valid JSON."""


class BaseRateDilutionService:
    """Detects base rate dilution — irrelevant info weakening base rate usage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        base_rate: str = "",
        additional_info: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect base rate dilution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BASE_RATE_DILUTION_PROMPT.format(
                judgment=judgment,
                base_rate=base_rate or "Not specified",
                additional_info=additional_info or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BASE_RATE_DILUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "dilution_present": data.get("dilution_present", False),
            "severity": data.get("severity", ""),
            "base_rate": data.get("base_rate", ""),
            "diluting_info": data.get("diluting_info", ""),
            "diagnosticity": data.get("diagnosticity", ""),
            "recommendation": data.get("recommendation", ""),
        }
