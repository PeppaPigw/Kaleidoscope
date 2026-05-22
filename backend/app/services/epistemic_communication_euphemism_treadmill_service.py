"""EpistemicCommunicationEuphemismTreadmillService - Euphemism Treadmill Detection.

Detects euphemism treadmill where language sanitization obscures reality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMMUNICATION_EUPHEMISM_TREADMILL_SYSTEM = """You are an epistemic communication euphemism treadmill specialist. Given euphemistic framing, assess whether language sanitization obscures reality:

Key concepts:
- Euphemism treadmill: progressive sanitization of language that obscures underlying reality
- Reality obscuring: language choices that hide uncomfortable truths
- Sanitization pattern: systematic replacement of direct terms with softer ones
- Meaning drift: gradual loss of original meaning through euphemization

When euphemism treadmill IS present:
- Language sanitizes uncomfortable reality
- Direct terms systematically replaced
- Meaning drifts from original referent
- Accountability reduced through vagueness
- Critical thinking impaired by soft framing

When no euphemism treadmill:
- Language is appropriately precise
- Terms maintain connection to referent
- Softening serves legitimate sensitivity
- Meaning remains clear
- Accountability preserved

Output JSON with: euphemism_treadmill_detected (bool), severity (none/mild/moderate/severe), reality_obscured (what reality is hidden), sanitization_pattern (what pattern of sanitization), meaning_drift (what meaning has drifted), recommendation (no_euphemism_treadmill/mild_language_check/significant_clarity_restoration/major_direct_language_reconstruction/emergency_complete_euphemism_treadmill)."""

EPISTEMIC_COMMUNICATION_EUPHEMISM_TREADMILL_PROMPT = """Detect epistemic communication euphemism treadmill:

Euphemistic framing: {euphemistic_framing}
Reality obscured: {reality_obscured}
Sanitization pattern: {sanitization_pattern}
Meaning drift: {meaning_drift}
Domain: {domain}
Context: {context}

Is language sanitization obscuring reality? Return ONLY valid JSON."""


class EpistemicCommunicationEuphemismTreadmillService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        euphemistic_framing: str,
        *,
        reality_obscured: str = "",
        sanitization_pattern: str = "",
        meaning_drift: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMMUNICATION_EUPHEMISM_TREADMILL_PROMPT.format(
                euphemistic_framing=euphemistic_framing,
                reality_obscured=reality_obscured or "Not specified",
                sanitization_pattern=sanitization_pattern or "Not specified",
                meaning_drift=meaning_drift or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMMUNICATION_EUPHEMISM_TREADMILL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "euphemistic_framing": euphemistic_framing[:200],
            "euphemism_treadmill_detected": data.get("euphemism_treadmill_detected", False),
            "severity": data.get("severity", ""),
            "reality_obscured": data.get("reality_obscured", ""),
            "sanitization_pattern": data.get("sanitization_pattern", ""),
            "meaning_drift": data.get("meaning_drift", ""),
            "recommendation": data.get("recommendation", ""),
        }
