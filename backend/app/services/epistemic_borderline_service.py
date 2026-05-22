"""EpistemicBorderlineService — Epistemic Borderline Detection.

Detects epistemic borderline — unstable intellectual identity with
splitting between idealization and devaluation of ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BORDERLINE_SYSTEM = """You are an epistemic borderline specialist. Given unstable intellectual identity, assess borderline patterns:

Key concepts:
- Epistemic borderline: unstable intellectual identity with splitting
- Splitting: all-or-nothing thinking about ideas (idealize or devalue)
- Identity diffusion: unclear intellectual self-concept
- Abandonment fear: terror of losing intellectual framework
- Emotional dysregulation: intense reactions to intellectual challenges
- Impulsivity: rash intellectual decisions without reflection
- Chronic emptiness: persistent intellectual void

When epistemic borderline IS present:
- Unstable intellectual identity
- All-or-nothing thinking about ideas
- Unclear intellectual self-concept
- Terror of losing framework
- Intense reactions to challenges
- Rash intellectual decisions
- Persistent intellectual void

When no borderline:
- Stable intellectual identity
- Nuanced thinking about ideas
- Clear intellectual self-concept
- Secure in framework
- Proportionate reactions
- Reflective decisions
- Intellectual fulfillment

Output JSON with: borderline_detected (bool), severity (none/mild/moderate/severe), splitting_pattern (what idealization/devaluation), identity_stability (what self-concept), abandonment_response (what framework loss fear), dysregulation_level (what reaction intensity), recommendation (no_borderline/mild_dbt_skills/significant_structured_therapy/major_intensive_dbt/emergency_crisis_intervention)."""

EPISTEMIC_BORDERLINE_PROMPT = """Detect epistemic borderline:

Splitting pattern: {splitting_pattern}
Identity stability: {identity_stability}
Abandonment response: {abandonment_response}
Dysregulation level: {dysregulation_level}
Domain: {domain}
Context: {context}

Is there unstable intellectual identity with splitting between idealization and devaluation? Return ONLY valid JSON."""


class EpistemicBorderlineService:
    """Detects epistemic borderline — unstable intellectual identity with splitting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        splitting_pattern: str,
        *,
        identity_stability: str = "",
        abandonment_response: str = "",
        dysregulation_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic borderline."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BORDERLINE_PROMPT.format(
                splitting_pattern=splitting_pattern,
                identity_stability=identity_stability or "Not specified",
                abandonment_response=abandonment_response or "Not specified",
                dysregulation_level=dysregulation_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BORDERLINE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "splitting_pattern": splitting_pattern[:200],
            "borderline_detected": data.get("borderline_detected", False),
            "severity": data.get("severity", ""),
            "identity_stability": data.get("identity_stability", ""),
            "abandonment_response": data.get("abandonment_response", ""),
            "dysregulation_level": data.get("dysregulation_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
