"""HermeneuticalMarginalizationService — Hermeneutical Marginalization Detection.

Detects hermeneutical marginalization — marginalization from meaning-making
resources and interpretive frameworks, where certain groups lack
the concepts to articulate their experiences.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HERMENEUTICAL_MARGINALIZATION_SYSTEM = """You are a hermeneutical marginalization specialist. Given a meaning-making context, assess whether certain groups are marginalized from interpretive resources:

Key concepts:
- Hermeneutical marginalization: excluded from meaning-making
- Interpretive exclusion: lacking frameworks to articulate experience
- Concept poverty: lacking concepts for one's own experience
- Meaning-making exclusion: excluded from creating shared meanings
- Framework absence: no interpretive framework for experience
- Articulation gap: unable to articulate due to missing concepts
- Hermeneutical lacuna: gap in collective interpretive resources

When hermeneutical marginalization IS present:
- Groups excluded from meaning-making processes
- Experiences lacking interpretive frameworks
- Concepts unavailable to articulate certain experiences
- Meaning-making resources not accessible to all
- Interpretive frameworks missing for certain experiences
- Articulation impossible due to concept absence
- Gaps in collective understanding serving marginalization

When interpretive limits are appropriate:
- Concept development ongoing and inclusive
- Interpretive frameworks evolving to include
- Articulation difficulties due to genuine novelty
- Meaning-making processes open to contribution
- Framework gaps recognized and being addressed
- Concept development serving understanding
- Interpretive resources being expanded

Output JSON with: marginalization_present (bool), severity (none/mild/moderate/severe), context (what meaning-making context), marginalized (who is marginalized), missing_resources (what interpretive resources are missing), impact (how marginalization affects understanding), recommendation (inclusive_meaning_making/mild_interpretive_gap/significant_hermeneutical_marginalization/major_meaning_making_exclusion/develop_inclusive_interpretive_resources)."""

HERMENEUTICAL_MARGINALIZATION_PROMPT = """Detect hermeneutical marginalization:

Meaning-making context: {meaning_context}
Frameworks available: {frameworks}
Experiences unarticulable: {unarticulable}
Inclusion level: {inclusion}
Domain: {domain}
Context: {context}

Are certain groups marginalized from meaning-making resources and interpretive frameworks? Return ONLY valid JSON."""


class HermeneuticalMarginalizationService:
    """Detects hermeneutical marginalization — excluded from meaning-making resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        meaning_context: str,
        *,
        frameworks: str = "",
        unarticulable: str = "",
        inclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hermeneutical marginalization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HERMENEUTICAL_MARGINALIZATION_PROMPT.format(
                meaning_context=meaning_context,
                frameworks=frameworks or "Not specified",
                unarticulable=unarticulable or "Not specified",
                inclusion=inclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HERMENEUTICAL_MARGINALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "meaning_context": meaning_context[:200],
            "marginalization_present": data.get("marginalization_present", False),
            "severity": data.get("severity", ""),
            "marginalized": data.get("marginalized", ""),
            "missing_resources": data.get("missing_resources", ""),
            "impact": data.get("impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
