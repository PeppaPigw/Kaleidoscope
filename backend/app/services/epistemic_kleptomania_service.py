"""EpistemicKleptomaniaService — Epistemic Kleptomania Detection.

Detects epistemic kleptomania — compulsive stealing of others' ideas
without attribution, driven by impulse rather than need.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_KLEPTOMANIA_SYSTEM = """You are an epistemic kleptomania specialist. Given compulsive idea stealing, assess kleptomania patterns:

Key concepts:
- Epistemic kleptomania: compulsive stealing of ideas without attribution
- Impulse-driven: not planned or need-based, but irresistible urge
- Tension buildup: increasing pressure before taking
- Relief: temporary satisfaction after appropriation
- Guilt: remorse after stealing but unable to stop
- Hoarding: accumulating stolen ideas without using them
- Pattern: repeated despite consequences

When epistemic kleptomania IS present:
- Compulsive idea stealing
- Irresistible urge to take
- Tension before appropriation
- Relief after taking
- Remorse but unable to stop
- Accumulating without using
- Repeated despite consequences

When no kleptomania:
- Proper attribution
- No urge to take
- No tension buildup
- No relief from taking
- No guilt cycle
- Using own ideas
- Respecting ownership

Output JSON with: kleptomania_detected (bool), severity (none/mild/moderate/severe), impulse_pattern (what urge), tension_cycle (what buildup-relief), guilt_response (what remorse), attribution_failure (what stealing pattern), recommendation (no_kleptomania/mild_impulse_awareness/significant_cbt/major_intensive_therapy/emergency_complete_compulsion)."""

EPISTEMIC_KLEPTOMANIA_PROMPT = """Detect epistemic kleptomania:

Impulse pattern: {impulse_pattern}
Tension cycle: {tension_cycle}
Guilt response: {guilt_response}
Attribution failure: {attribution_failure}
Domain: {domain}
Context: {context}

Is there compulsive stealing of ideas without attribution driven by impulse? Return ONLY valid JSON."""


class EpistemicKleptomaniaService:
    """Detects epistemic kleptomania — compulsive idea stealing."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        impulse_pattern: str,
        *,
        tension_cycle: str = "",
        guilt_response: str = "",
        attribution_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic kleptomania."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_KLEPTOMANIA_PROMPT.format(
                impulse_pattern=impulse_pattern,
                tension_cycle=tension_cycle or "Not specified",
                guilt_response=guilt_response or "Not specified",
                attribution_failure=attribution_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_KLEPTOMANIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "impulse_pattern": impulse_pattern[:200],
            "kleptomania_detected": data.get("kleptomania_detected", False),
            "severity": data.get("severity", ""),
            "tension_cycle": data.get("tension_cycle", ""),
            "guilt_response": data.get("guilt_response", ""),
            "attribution_failure": data.get("attribution_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
