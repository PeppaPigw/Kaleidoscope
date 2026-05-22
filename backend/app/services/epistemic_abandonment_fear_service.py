"""EpistemicAbandonmentFearService — Epistemic Abandonment Fear Detection.

Detects epistemic abandonment fear — terror of being intellectually
abandoned, left behind, or excluded from knowledge communities.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ABANDONMENT_FEAR_SYSTEM = """You are an epistemic abandonment fear specialist. Given terror of intellectual exclusion, assess abandonment fear:

Key concepts:
- Epistemic abandonment fear: terror of being left behind intellectually
- Exclusion anxiety: fear of being cut off from knowledge
- Clinging behavior: desperately holding onto intellectual connections
- Preemptive rejection: leaving before being left
- Hypervigilance: scanning for signs of intellectual abandonment
- Separation distress: panic when intellectual connection threatened
- Frantic efforts: desperate attempts to prevent intellectual loss

When epistemic abandonment fear IS present:
- Terror of being left behind
- Fear of knowledge exclusion
- Desperately holding on
- Leaving before being left
- Scanning for abandonment signs
- Panic at connection threat
- Desperate prevention attempts

When no abandonment fear:
- Secure intellectual attachment
- Comfortable with independence
- Relaxed connections
- Staying through difficulty
- Trusting stability
- Calm at separation
- Natural relationship flow

Output JSON with: abandonment_fear_detected (bool), severity (none/mild/moderate/severe), exclusion_anxiety (what fearing), clinging_pattern (what holding onto), preemptive_rejection (what leaving), hypervigilance_level (what scanning), recommendation (no_abandonment_fear/mild_security_building/significant_attachment_work/major_intensive_therapy/emergency_panic_state)."""

EPISTEMIC_ABANDONMENT_FEAR_PROMPT = """Detect epistemic abandonment fear:

Exclusion anxiety: {exclusion_anxiety}
Clinging pattern: {clinging_pattern}
Preemptive rejection: {preemptive_rejection}
Hypervigilance level: {hypervigilance_level}
Domain: {domain}
Context: {context}

Is there terror of being intellectually abandoned or excluded? Return ONLY valid JSON."""


class EpistemicAbandonmentFearService:
    """Detects epistemic abandonment fear — terror of intellectual exclusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        exclusion_anxiety: str,
        *,
        clinging_pattern: str = "",
        preemptive_rejection: str = "",
        hypervigilance_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic abandonment fear."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ABANDONMENT_FEAR_PROMPT.format(
                exclusion_anxiety=exclusion_anxiety,
                clinging_pattern=clinging_pattern or "Not specified",
                preemptive_rejection=preemptive_rejection or "Not specified",
                hypervigilance_level=hypervigilance_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ABANDONMENT_FEAR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "exclusion_anxiety": exclusion_anxiety[:200],
            "abandonment_fear_detected": data.get("abandonment_fear_detected", False),
            "severity": data.get("severity", ""),
            "clinging_pattern": data.get("clinging_pattern", ""),
            "preemptive_rejection": data.get("preemptive_rejection", ""),
            "hypervigilance_level": data.get("hypervigilance_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
