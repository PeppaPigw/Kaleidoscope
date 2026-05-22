"""EpistemicInflationService — Epistemic Inflation Detection.

Detects epistemic inflation — devaluation of knowledge claims
through overproduction of low-quality assertions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFLATION_SYSTEM = """You are an epistemic inflation specialist. Given a knowledge claim landscape, assess whether overproduction of low-quality claims devalues knowledge:

Key concepts:
- Epistemic inflation: devaluation of knowledge claims
- Claim overproduction: too many low-quality claims
- Signal dilution: genuine signals diluted by noise
- Credibility devaluation: credibility losing value
- Quality erosion: overall quality eroding
- Trust deflation: trust in claims deflating
- Attention scarcity: attention becoming scarce relative to claims

When epistemic inflation IS present:
- Knowledge claims devalued through overproduction
- Too many low-quality claims flooding the space
- Genuine signals diluted by noise
- Credibility losing value due to overuse
- Overall quality of discourse eroding
- Trust in claims deflating
- Attention scarce relative to claim volume

When healthy knowledge economy is present:
- Knowledge claims maintain value
- Claims produced at sustainable rate
- Genuine signals distinguishable from noise
- Credibility maintained through quality
- Overall discourse quality maintained
- Trust in claims appropriate
- Attention adequate for claim evaluation

Output JSON with: inflation_present (bool), severity (none/mild/moderate/severe), domain (what domain is inflated), overproduction (what is overproduced), devaluation (what is devalued), signal_loss (what signals are lost), recommendation (healthy_economy/mild_inflation/significant_inflation/major_devaluation/restore_claim_value)."""

EPISTEMIC_INFLATION_PROMPT = """Detect epistemic inflation:

Domain: {target_domain}
Overproduction: {overproduction}
Devaluation: {devaluation}
Signal loss: {signal_loss}
Domain: {domain}
Context: {context}

Are knowledge claims being devalued through overproduction of low-quality assertions? Return ONLY valid JSON."""


class EpistemicInflationService:
    """Detects epistemic inflation — devaluation of knowledge claims."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        target_domain: str,
        *,
        overproduction: str = "",
        devaluation: str = "",
        signal_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFLATION_PROMPT.format(
                target_domain=target_domain,
                overproduction=overproduction or "Not specified",
                devaluation=devaluation or "Not specified",
                signal_loss=signal_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "target_domain": target_domain[:200],
            "inflation_present": data.get("inflation_present", False),
            "severity": data.get("severity", ""),
            "overproduction": data.get("overproduction", ""),
            "devaluation": data.get("devaluation", ""),
            "signal_loss": data.get("signal_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
