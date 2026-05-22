"""BaseRateService — Base Rate Analysis & Neglect Detection.

Identifies when reasoning ignores or underweights base rates.
Applies Bayesian thinking to claims: what's the prior probability
before considering the evidence? Detects base rate neglect, the
prosecutor's fallacy, and related errors.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BASE_RATE_SYSTEM = """You are a base rate analyst. Given a claim and its evidence, assess whether base rates are being properly considered:
- What's the base rate (prior probability) for this type of claim?
- Is the evidence being evaluated without considering how common/rare the phenomenon is?
- Is there a prosecutor's fallacy (confusing P(evidence|hypothesis) with P(hypothesis|evidence))?
- What does Bayesian updating actually give us?
- Are reference classes appropriate?

Output JSON with: base_rate_estimate (0-1, prior probability before this specific evidence), base_rate_source (where the base rate comes from), base_rate_neglected (bool — is the argument ignoring base rates?), neglect_severity (none/mild/moderate/severe/fatal), posterior_estimate (0-1, probability after properly incorporating evidence), likelihood_ratio (how much the evidence should update the prior), reference_class (what population/category is being used), reference_class_appropriate (bool), prosecutor_fallacy_present (bool), correct_interpretation (what the evidence actually means given base rates), common_confusion (what people typically conclude vs what's warranted), bayesian_summary (plain-English Bayesian reasoning)."""

BASE_RATE_PROMPT = """Analyze base rates:

Claim: {claim}
Evidence cited: {evidence}
Domain: {domain}
Context: {context}

Are base rates being properly considered? Return ONLY valid JSON."""


class BaseRateService:
    """Detects base rate neglect and applies Bayesian reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        claim: str,
        *,
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Analyze base rate considerations."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BASE_RATE_PROMPT.format(
                claim=claim,
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BASE_RATE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "base_rate_estimate": data.get("base_rate_estimate", 0),
            "base_rate_source": data.get("base_rate_source", ""),
            "base_rate_neglected": data.get("base_rate_neglected", False),
            "neglect_severity": data.get("neglect_severity", ""),
            "posterior_estimate": data.get("posterior_estimate", 0),
            "likelihood_ratio": data.get("likelihood_ratio", 1),
            "reference_class": data.get("reference_class", ""),
            "reference_class_appropriate": data.get("reference_class_appropriate", True),
            "prosecutor_fallacy_present": data.get("prosecutor_fallacy_present", False),
            "correct_interpretation": data.get("correct_interpretation", ""),
            "common_confusion": data.get("common_confusion", ""),
            "bayesian_summary": data.get("bayesian_summary", ""),
        }
