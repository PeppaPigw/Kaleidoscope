"""StreetlightEffectService — Observational Bias & Search Misdirection.

Identifies when research or investigation is focused where it's easy
to look rather than where the answer is likely to be. Named after
the joke about searching for keys under the streetlight because
that's where the light is.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STREETLIGHT_SYSTEM = """You are a streetlight effect specialist. Given a research approach or investigation, assess whether it's looking where it's easy rather than where the answer is:
- Is the methodology chosen for convenience rather than appropriateness?
- Are easily measurable proxies being used instead of hard-to-measure realities?
- Is the search space artificially narrowed to what's accessible?
- What important areas are being ignored because they're hard to study?
- Is there a mismatch between where we're looking and where the answer likely is?

Output JSON with: streetlight_effect_present (bool), severity (none/mild/moderate/severe), where_looking (what's being studied/measured), where_answer_likely_is (where the real answer probably lives), why_looking_here (what makes this area convenient), why_not_looking_there (what makes the right area hard), measurement_convenience_bias (0-1, how much convenience is driving the approach), dark_areas (list of: area, why_important, why_ignored), methodology_mismatch (bool — is the method chosen for ease rather than fit?), data_availability_bias (bool — studying what has data rather than what matters), famous_examples (similar streetlight effects in this domain), what_would_change (how conclusions might differ if we looked in the right place), recommendation (approach_valid/expand_search/redirect_entirely), better_approach (how to look where the answer actually is)."""

STREETLIGHT_PROMPT = """Detect streetlight effect:

Research/Investigation: {investigation}
What's being measured: {measured}
What's the real question: {real_question}
Domain: {domain}
Context: {context}

Are we looking where it's easy rather than where the answer is? Return ONLY valid JSON."""


class StreetlightEffectService:
    """Detects streetlight effect in research and investigation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investigation: str,
        *,
        measured: str = "",
        real_question: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect streetlight effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STREETLIGHT_PROMPT.format(
                investigation=investigation,
                measured=measured or "Not specified",
                real_question=real_question or "Not explicitly stated",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STREETLIGHT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investigation": investigation[:200],
            "streetlight_effect_present": data.get("streetlight_effect_present", False),
            "severity": data.get("severity", ""),
            "where_looking": data.get("where_looking", ""),
            "where_answer_likely_is": data.get("where_answer_likely_is", ""),
            "why_looking_here": data.get("why_looking_here", ""),
            "why_not_looking_there": data.get("why_not_looking_there", ""),
            "measurement_convenience_bias": data.get("measurement_convenience_bias", 0),
            "dark_areas": data.get("dark_areas", []),
            "methodology_mismatch": data.get("methodology_mismatch", False),
            "data_availability_bias": data.get("data_availability_bias", False),
            "famous_examples": data.get("famous_examples", []),
            "what_would_change": data.get("what_would_change", ""),
            "recommendation": data.get("recommendation", ""),
            "better_approach": data.get("better_approach", ""),
        }
