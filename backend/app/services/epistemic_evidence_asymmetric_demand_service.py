"""EpistemicEvidenceAsymmetricDemandService — Epistemic Evidence Asymmetric Demand Detection.

Detects epistemic evidence asymmetric demand — demanding more evidence
for disfavored conclusions than favored ones.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVIDENCE_ASYMMETRIC_DEMAND_SYSTEM = """You are an epistemic evidence asymmetric demand specialist. Given asymmetric evidence standards, assess evidence demand asymmetry:

Key concepts:
- Epistemic evidence asymmetric demand: different evidence standards for different conclusions
- Motivated skepticism: skepticism applied selectively to disfavored conclusions
- Low bar for favored: low evidence bar for conclusions one wants to believe
- High bar for disfavored: high evidence bar for conclusions one resists
- Double standard: applying different standards to same type of claim
- Selective rigor: rigorous only when evaluating opposing views
- Confirmation asymmetry: asymmetric treatment of confirming vs disconfirming evidence

When epistemic evidence asymmetric demand IS present:
- Different standards applied
- Skepticism selective
- Low bar for favored views
- High bar for disfavored views
- Double standard operating
- Rigor selective
- Confirmation treated asymmetrically

When no asymmetric demand:
- Standards consistent
- Skepticism uniform
- Same bar for all conclusions
- Evidence evaluated equally
- Single standard applied
- Rigor consistent
- All evidence treated equally

Output JSON with: asymmetric_demand_detected (bool), severity (none/mild/moderate/severe), motivated_skepticism (what selective skepticism), low_bar_favored (what low bar applied), high_bar_disfavored (what high bar applied), double_standard (what double standard), recommendation (no_asymmetric_demand/mild_standard_awareness/significant_standard_equalization/major_intensive_demand_calibration/emergency_complete_asymmetric_demand)."""

EPISTEMIC_EVIDENCE_ASYMMETRIC_DEMAND_PROMPT = """Detect epistemic evidence asymmetric demand:

Motivated skepticism: {motivated_skepticism}
Low bar for favored: {low_bar_favored}
High bar for disfavored: {high_bar_disfavored}
Double standard: {double_standard}
Domain: {domain}
Context: {context}

Is more evidence being demanded for disfavored conclusions than favored ones? Return ONLY valid JSON."""


class EpistemicEvidenceAsymmetricDemandService:
    """Detects epistemic evidence asymmetric demand — selective standards."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        motivated_skepticism: str,
        *,
        low_bar_favored: str = "",
        high_bar_disfavored: str = "",
        double_standard: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic evidence asymmetric demand."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVIDENCE_ASYMMETRIC_DEMAND_PROMPT.format(
                motivated_skepticism=motivated_skepticism,
                low_bar_favored=low_bar_favored or "Not specified",
                high_bar_disfavored=high_bar_disfavored or "Not specified",
                double_standard=double_standard or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVIDENCE_ASYMMETRIC_DEMAND_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "motivated_skepticism": motivated_skepticism[:200],
            "asymmetric_demand_detected": data.get("asymmetric_demand_detected", False),
            "severity": data.get("severity", ""),
            "low_bar_favored": data.get("low_bar_favored", ""),
            "high_bar_disfavored": data.get("high_bar_disfavored", ""),
            "double_standard": data.get("double_standard", ""),
            "recommendation": data.get("recommendation", ""),
        }
