"""WillfulHermeneuticalIgnoranceService — Willful Hermeneutical Ignorance Detection.

Detects willful hermeneutical ignorance — dominant groups actively
maintaining ignorance of marginalized experiences, refusing to
develop or use interpretive resources for understanding others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WILLFUL_HERMENEUTICAL_IGNORANCE_SYSTEM = """You are a willful hermeneutical ignorance specialist. Given a situation, assess whether ignorance of others' experiences is being actively maintained:

Key concepts:
- Willful hermeneutical ignorance: actively maintaining ignorance
- Motivated not-knowing: choosing not to understand
- Interpretive refusal: refusing to develop understanding
- Comfortable ignorance: ignorance that serves interests
- Epistemic vice: character flaw in knowledge practices
- Active not-listening: refusing available understanding
- Structural ignorance maintenance: systems preserving not-knowing

When willful hermeneutical ignorance IS present:
- Available understanding actively refused
- Ignorance serves interests of the ignorant
- Resources for understanding exist but are rejected
- Pattern of not-knowing that benefits the ignorant
- Interpretive frameworks available but not adopted
- Comfort maintained through deliberate not-understanding
- Structural mechanisms preserve ignorance

When ignorance is not willful:
- Genuine lack of available interpretive resources
- Good faith effort to understand
- Ignorance not serving interests
- Resources genuinely unavailable
- Structural barriers to understanding acknowledged
- Effort being made to develop understanding
- Ignorance recognized as problem to be solved

Output JSON with: ignorance_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), ignorance_maintained (what ignorance is maintained), benefit (who benefits from ignorance), resources_available (what understanding resources exist), recommendation (appropriate_epistemic_limitation/mild_interpretive_laziness/significant_willful_ignorance/major_active_not_knowing/engage_available_resources)."""

WILLFUL_HERMENEUTICAL_IGNORANCE_PROMPT = """Detect willful hermeneutical ignorance:

Situation: {situation}
Understanding available: {available}
Understanding refused: {refused}
Benefit of ignorance: {benefit}
Domain: {domain}
Context: {context}

Is ignorance of others' experiences being actively maintained when understanding is available? Return ONLY valid JSON."""


class WillfulHermeneuticalIgnoranceService:
    """Detects willful hermeneutical ignorance — actively maintaining ignorance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        available: str = "",
        refused: str = "",
        benefit: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect willful hermeneutical ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WILLFUL_HERMENEUTICAL_IGNORANCE_PROMPT.format(
                situation=situation,
                available=available or "Not specified",
                refused=refused or "Not specified",
                benefit=benefit or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WILLFUL_HERMENEUTICAL_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "ignorance_present": data.get("ignorance_present", False),
            "severity": data.get("severity", ""),
            "ignorance_maintained": data.get("ignorance_maintained", ""),
            "benefit": data.get("benefit", ""),
            "resources_available": data.get("resources_available", ""),
            "recommendation": data.get("recommendation", ""),
        }
