"""EpistemicHormoneCascadeService — Epistemic Hormone Cascade Detection.

Detects epistemic hormone cascades — ideas triggering cascading regulatory
signals that amplify through multiple levels of intellectual control.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HORMONE_CASCADE_SYSTEM = """You are an epistemic hormone cascade specialist. Given an intellectual signaling system, assess whether ideas trigger cascading regulatory signals:

Key concepts:
- Epistemic hormone cascade: ideas triggering multi-level regulatory signals
- Hypothalamic signal: initial high-level directive
- Pituitary amplification: mid-level signal amplification
- Target organ response: final effector activation
- Signal amplification: each level multiplying the signal
- Releasing factor: trigger that initiates the cascade
- Tropic hormone: signal that stimulates another signaling gland

When epistemic hormone cascade IS present:
- Ideas triggering multi-level regulatory signals
- High-level directives cascading through amplification layers
- Mid-level amplification of initial signals
- Final effector activation from cascaded signals
- Each level multiplying the regulatory signal
- Specific triggers initiating cascades
- Signals stimulating further signaling

When no cascade is present:
- No multi-level signaling
- No cascading amplification
- No mid-level relay
- No effector activation chains
- No signal multiplication
- No cascade triggers
- No tropic signaling

Output JSON with: hormone_cascade_present (bool), severity (none/mild/moderate/severe), hypothalamic_signal (what high-level directive), pituitary_amplification (what mid-level amplification), target_response (what effector activation), signal_amplification (what multiplication), recommendation (no_cascade/mild_cascade/significant_hormone_cascade/major_regulatory_cascade/modulate_cascade_gain)."""

EPISTEMIC_HORMONE_CASCADE_PROMPT = """Detect epistemic hormone cascade:

Hypothalamic signal: {hypothalamic_signal}
Pituitary amplification: {pituitary_amplification}
Target response: {target_response}
Signal amplification: {signal_amplification}
Domain: {domain}
Context: {context}

Are ideas triggering cascading regulatory signals that amplify through multiple levels? Return ONLY valid JSON."""


class EpistemicHormoneCascadeService:
    """Detects epistemic hormone cascades — cascading regulatory signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hypothalamic_signal: str,
        *,
        pituitary_amplification: str = "",
        target_response: str = "",
        signal_amplification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hormone cascade."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HORMONE_CASCADE_PROMPT.format(
                hypothalamic_signal=hypothalamic_signal,
                pituitary_amplification=pituitary_amplification or "Not specified",
                target_response=target_response or "Not specified",
                signal_amplification=signal_amplification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HORMONE_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hypothalamic_signal": hypothalamic_signal[:200],
            "hormone_cascade_present": data.get("hormone_cascade_present", False),
            "severity": data.get("severity", ""),
            "pituitary_amplification": data.get("pituitary_amplification", ""),
            "target_response": data.get("target_response", ""),
            "signal_amplification": data.get("signal_amplification", ""),
            "recommendation": data.get("recommendation", ""),
        }
