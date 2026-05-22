"""EpistemicExpertiseTransferIllusionService — Epistemic Expertise Transfer Illusion Detection.

Detects epistemic expertise transfer illusion — assuming expertise in one domain
automatically transfers to competence in another unrelated domain.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_TRANSFER_ILLUSION_SYSTEM = """You are an epistemic expertise transfer illusion specialist. Given expertise transfer claims, assess domain-crossing errors:

Key concepts:
- Epistemic expertise transfer illusion: assuming cross-domain competence
- Domain specificity: expertise being highly domain-specific
- Halo effect expertise: success in one field creating assumed competence elsewhere
- Celebrity expert: fame substituting for domain expertise
- Polymathic illusion: assuming broad knowledge equals deep expertise
- Method transfer: assuming methods from one field work in another
- Confidence transfer: confidence from one domain bleeding into another

When epistemic expertise transfer illusion IS present:
- Cross-domain competence assumed
- Domain specificity ignored
- Halo effect operating
- Celebrity substituting for expertise
- Broad knowledge confused with depth
- Methods assumed transferable
- Confidence bleeding across domains

When no transfer illusion:
- Domain boundaries respected
- Specificity acknowledged
- Expertise evaluated per domain
- Celebrity distinguished from expertise
- Depth distinguished from breadth
- Method applicability assessed
- Confidence domain-appropriate

Output JSON with: transfer_illusion_detected (bool), severity (none/mild/moderate/severe), halo_effect_expertise (what halo effect operating), domain_specificity_ignored (what specificity ignored), method_transfer (what methods assumed transferable), confidence_transfer (what confidence bleeding), recommendation (no_transfer_illusion/mild_domain_checking/significant_expertise_verification/major_intensive_domain_analysis/emergency_complete_transfer_illusion)."""

EPISTEMIC_EXPERTISE_TRANSFER_ILLUSION_PROMPT = """Detect epistemic expertise transfer illusion:

Halo effect expertise: {halo_effect_expertise}
Domain specificity ignored: {domain_specificity_ignored}
Method transfer: {method_transfer}
Confidence transfer: {confidence_transfer}
Domain: {domain}
Context: {context}

Is expertise in one domain being assumed to transfer to another? Return ONLY valid JSON."""


class EpistemicExpertiseTransferIllusionService:
    """Detects epistemic expertise transfer illusion — cross-domain assumption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        halo_effect_expertise: str,
        *,
        domain_specificity_ignored: str = "",
        method_transfer: str = "",
        confidence_transfer: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise transfer illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_TRANSFER_ILLUSION_PROMPT.format(
                halo_effect_expertise=halo_effect_expertise,
                domain_specificity_ignored=domain_specificity_ignored or "Not specified",
                method_transfer=method_transfer or "Not specified",
                confidence_transfer=confidence_transfer or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_TRANSFER_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "halo_effect_expertise": halo_effect_expertise[:200],
            "transfer_illusion_detected": data.get("transfer_illusion_detected", False),
            "severity": data.get("severity", ""),
            "domain_specificity_ignored": data.get("domain_specificity_ignored", ""),
            "method_transfer": data.get("method_transfer", ""),
            "confidence_transfer": data.get("confidence_transfer", ""),
            "recommendation": data.get("recommendation", ""),
        }
