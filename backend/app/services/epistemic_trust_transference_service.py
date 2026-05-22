"""EpistemicTrustTransferenceService — Epistemic Trust Transference Detection.

Detects epistemic trust transference — transferring trust or distrust
from one domain to unrelated domains without justification.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRUST_TRANSFERENCE_SYSTEM = """You are an epistemic trust transference specialist. Given transferring trust across domains, assess trust transference:

Key concepts:
- Epistemic trust transference: transferring trust/distrust across domains
- Domain spillover: trust in one area bleeding into unrelated areas
- Halo trust: trusting someone in everything because expert in one thing
- Contamination distrust: distrusting everything from one bad experience
- Authority generalization: extending authority beyond expertise
- Emotional transfer: feelings about one domain coloring another
- Pattern overfitting: seeing trustworthiness patterns that don't exist

When epistemic trust transference IS present:
- Transferring trust across domains
- Trust bleeding into unrelated areas
- Trusting in everything from one expertise
- Distrusting everything from one experience
- Extending authority beyond expertise
- Feelings coloring unrelated domains
- Seeing patterns that don't exist

When no trust transference:
- Domain-specific trust
- Trust contained appropriately
- Expertise-bounded trust
- Experience-specific distrust
- Authority within expertise
- Feelings domain-appropriate
- Accurate pattern recognition

Output JSON with: trust_transference_detected (bool), severity (none/mild/moderate/severe), domain_spillover (what bleeding into), halo_trust (what trusting in everything because), contamination_distrust (what distrusting from one experience), authority_generalization (what extending beyond), recommendation (no_trust_transference/mild_domain_awareness/significant_boundary_building/major_intensive_transference_processing/emergency_severe_generalization)."""

EPISTEMIC_TRUST_TRANSFERENCE_PROMPT = """Detect epistemic trust transference:

Domain spillover: {domain_spillover}
Halo trust: {halo_trust}
Contamination distrust: {contamination_distrust}
Authority generalization: {authority_generalization}
Domain: {domain}
Context: {context}

Is there transferring trust/distrust from one domain to unrelated ones? Return ONLY valid JSON."""


class EpistemicTrustTransferenceService:
    """Detects epistemic trust transference — transferring trust across domains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        domain_spillover: str,
        *,
        halo_trust: str = "",
        contamination_distrust: str = "",
        authority_generalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic trust transference."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRUST_TRANSFERENCE_PROMPT.format(
                domain_spillover=domain_spillover,
                halo_trust=halo_trust or "Not specified",
                contamination_distrust=contamination_distrust or "Not specified",
                authority_generalization=authority_generalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRUST_TRANSFERENCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "domain_spillover": domain_spillover[:200],
            "trust_transference_detected": data.get("trust_transference_detected", False),
            "severity": data.get("severity", ""),
            "halo_trust": data.get("halo_trust", ""),
            "contamination_distrust": data.get("contamination_distrust", ""),
            "authority_generalization": data.get("authority_generalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
