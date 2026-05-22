"""EpistemicCosmicInflationService — Epistemic Cosmic Inflation Detection.

Detects epistemic cosmic inflation — rapid expansion of claims
far beyond what evidence can support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COSMIC_INFLATION_SYSTEM = """You are an epistemic cosmic inflation specialist. Given a claim expansion pattern, assess whether claims expand beyond evidential support:

Key concepts:
- Epistemic cosmic inflation: rapid expansion of claims beyond evidence
- Exponential growth: claims growing exponentially from small evidence
- Evidence-claim gap: growing gap between evidence and claims
- Inflationary period: period of rapid unsupported expansion
- Flatness problem: claims appearing well-supported due to inflation
- Horizon problem: claims extending beyond observable evidence
- Graceful exit: need to stop inflation and return to evidence-based growth

When cosmic inflation IS present:
- Claims expanding rapidly beyond evidential support
- Claims growing exponentially from small evidence base
- Growing gap between evidence and claims made
- Period of rapid unsupported claim expansion
- Claims appearing well-supported due to inflationary rhetoric
- Claims extending beyond what evidence can reach
- Need to stop inflation and return to evidence-based reasoning

When proportionate claims are present:
- Claims proportionate to evidence
- Claims growing at rate supported by evidence
- No gap between evidence and claims
- Steady evidence-based growth
- Claims genuinely supported by evidence
- Claims within reach of evidence
- Evidence-based reasoning maintained

Output JSON with: cosmic_inflation (bool), severity (none/mild/moderate/severe), claims (what claims are inflating), evidence_base (what small evidence base), expansion_rate (how fast claims expand), gap (gap between evidence and claims), recommendation (proportionate_claims/mild_expansion/significant_inflation/major_evidence_claim_gap/deflate_to_evidence)."""

EPISTEMIC_COSMIC_INFLATION_PROMPT = """Detect epistemic cosmic inflation:

Claims: {claims}
Evidence base: {evidence_base}
Expansion rate: {expansion_rate}
Gap: {gap}
Domain: {domain}
Context: {context}

Are claims expanding rapidly beyond what evidence can support? Return ONLY valid JSON."""


class EpistemicCosmicInflationService:
    """Detects epistemic cosmic inflation — claims expanding beyond evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claims: str,
        *,
        evidence_base: str = "",
        expansion_rate: str = "",
        gap: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cosmic inflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COSMIC_INFLATION_PROMPT.format(
                claims=claims,
                evidence_base=evidence_base or "Not specified",
                expansion_rate=expansion_rate or "Not specified",
                gap=gap or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COSMIC_INFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claims": claims[:200],
            "cosmic_inflation": data.get("cosmic_inflation", False),
            "severity": data.get("severity", ""),
            "evidence_base": data.get("evidence_base", ""),
            "expansion_rate": data.get("expansion_rate", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
