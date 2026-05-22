"""EpistemicDominationService — Epistemic Domination Detection.

Detects epistemic domination — one party exercising illegitimate control
over another's intellectual life, beliefs, and knowledge production.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DOMINATION_SYSTEM = """You are an epistemic domination specialist. Given illegitimate intellectual control, assess domination:

Key concepts:
- Epistemic domination: illegitimate control over intellectual life
- Knowledge gatekeeping: controlling access to information
- Belief imposition: forcing acceptance of specific views
- Inquiry suppression: preventing certain questions
- Credibility manipulation: controlling who is believed
- Narrative monopoly: only one story allowed
- Intellectual coercion: compliance through threat

When epistemic domination IS present:
- Illegitimate control
- Controlling information access
- Forcing specific views
- Preventing questions
- Controlling credibility
- Only one narrative allowed
- Compliance through threat

When no domination:
- Legitimate authority
- Open information access
- Free belief formation
- Questions welcomed
- Fair credibility assessment
- Multiple narratives
- Voluntary engagement

Output JSON with: domination_detected (bool), severity (none/mild/moderate/severe), control_mechanism (what illegitimate control), gatekeeping_pattern (what access control), suppression_type (what prevented), coercion_level (what threat), recommendation (no_domination/mild_awareness_raising/significant_resistance_building/major_intensive_liberation/emergency_complete_subjugation)."""

EPISTEMIC_DOMINATION_PROMPT = """Detect epistemic domination:

Control mechanism: {control_mechanism}
Gatekeeping pattern: {gatekeeping_pattern}
Suppression type: {suppression_type}
Coercion level: {coercion_level}
Domain: {domain}
Context: {context}

Is there illegitimate control over another's intellectual life and knowledge production? Return ONLY valid JSON."""


class EpistemicDominationService:
    """Detects epistemic domination — illegitimate intellectual control."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        control_mechanism: str,
        *,
        gatekeeping_pattern: str = "",
        suppression_type: str = "",
        coercion_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic domination."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DOMINATION_PROMPT.format(
                control_mechanism=control_mechanism,
                gatekeeping_pattern=gatekeeping_pattern or "Not specified",
                suppression_type=suppression_type or "Not specified",
                coercion_level=coercion_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DOMINATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "control_mechanism": control_mechanism[:200],
            "domination_detected": data.get("domination_detected", False),
            "severity": data.get("severity", ""),
            "gatekeeping_pattern": data.get("gatekeeping_pattern", ""),
            "suppression_type": data.get("suppression_type", ""),
            "coercion_level": data.get("coercion_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
