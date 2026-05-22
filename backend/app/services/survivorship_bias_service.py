"""SurvivorshipBiasService — Survivorship Bias Detection.

Identifies when conclusions are drawn only from visible successes
while ignoring the silent evidence of failures. Detects selection
on the dependent variable, silent evidence, and cemetery of failures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SURVIVORSHIP_SYSTEM = """You are a survivorship bias specialist. Given a claim or conclusion, assess whether it suffers from survivorship bias:
- Is the conclusion drawn only from successes/survivors?
- What does the "cemetery" look like (failures we can't see)?
- Would the same factors be present in failures too?
- Is there selection on the dependent variable?
- What would a proper study design look like?

Output JSON with: survivorship_bias_present (bool), severity (none/mild/moderate/severe/fatal), visible_sample (what we're looking at), invisible_cemetery (what we're NOT seeing), cemetery_size_estimate (how many failures for each success), shared_with_failures (factors present in both successes and failures), actually_differentiating (factors that truly distinguish success from failure), selection_mechanism (how survivors got selected into the sample), proper_study_design (how to test this without survivorship bias), famous_example (a well-known case of this same bias pattern), corrected_conclusion (what we can actually conclude from the evidence), confidence_after_correction (0-1, how confident we should be after accounting for bias)."""

SURVIVORSHIP_PROMPT = """Detect survivorship bias:

Claim: {claim}
Evidence basis: {evidence_basis}
Domain: {domain}
Context: {context}

Is this conclusion drawn only from survivors? Return ONLY valid JSON."""


class SurvivorshipBiasService:
    """Detects survivorship bias in reasoning and evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        evidence_basis: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect survivorship bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SURVIVORSHIP_PROMPT.format(
                claim=claim,
                evidence_basis=evidence_basis or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SURVIVORSHIP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "survivorship_bias_present": data.get("survivorship_bias_present", False),
            "severity": data.get("severity", ""),
            "visible_sample": data.get("visible_sample", ""),
            "invisible_cemetery": data.get("invisible_cemetery", ""),
            "cemetery_size_estimate": data.get("cemetery_size_estimate", ""),
            "shared_with_failures": data.get("shared_with_failures", []),
            "actually_differentiating": data.get("actually_differentiating", []),
            "selection_mechanism": data.get("selection_mechanism", ""),
            "proper_study_design": data.get("proper_study_design", ""),
            "famous_example": data.get("famous_example", ""),
            "corrected_conclusion": data.get("corrected_conclusion", ""),
            "confidence_after_correction": data.get("confidence_after_correction", 0),
        }
