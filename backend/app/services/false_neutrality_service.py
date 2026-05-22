"""FalseNeutralityService — False Neutrality Detection.

Detects false neutrality — presenting a biased framing as neutral
or objective, where the appearance of impartiality masks actual
bias in selection, emphasis, or framing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_NEUTRALITY_SYSTEM = """You are a false neutrality specialist. Given a presentation, assess whether bias is being masked as neutrality:

Key concepts:
- False neutrality: bias presented as objectivity
- View from nowhere: pretending no perspective exists
- Selective objectivity: objective about some, biased about others
- Framing as neutral: biased framing presented as default
- Both-sides-ism: false balance as neutrality
- Status quo bias as neutral: treating current state as default
- Perspective erasure: hiding the perspective being used

When false neutrality IS present:
- Biased framing presented as neutral or objective
- Perspective hidden behind appearance of impartiality
- Selection bias masked as comprehensive coverage
- Emphasis patterns reveal bias despite neutral claims
- Status quo treated as neutral default
- False balance presented as objectivity
- Actual perspective denied or hidden

When genuine neutrality is present:
- Multiple perspectives genuinely represented
- Own perspective acknowledged and managed
- Selection criteria transparent
- Emphasis justified by evidence not preference
- Status quo questioned alongside alternatives
- Balance reflects actual distribution of evidence
- Perspective explicitly stated

Output JSON with: false_neutrality_present (bool), severity (none/mild/moderate/severe), presentation (what is presented), claimed_neutrality (what neutrality is claimed), actual_bias (what bias exists), masked_perspective (what perspective is hidden), recommendation (genuine_neutrality/mild_perspective_blindness/significant_false_neutrality/major_bias_as_objectivity/acknowledge_perspective)."""

FALSE_NEUTRALITY_PROMPT = """Detect false neutrality:

Presentation: {presentation}
Neutrality claimed: {neutrality}
Selection made: {selection}
Perspective: {perspective}
Domain: {domain}
Context: {context}

Is bias being masked as neutrality or objectivity? Return ONLY valid JSON."""


class FalseNeutralityService:
    """Detects false neutrality — bias presented as objectivity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        presentation: str,
        *,
        neutrality: str = "",
        selection: str = "",
        perspective: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false neutrality."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_NEUTRALITY_PROMPT.format(
                presentation=presentation,
                neutrality=neutrality or "Not specified",
                selection=selection or "Not specified",
                perspective=perspective or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_NEUTRALITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "presentation": presentation[:200],
            "false_neutrality_present": data.get("false_neutrality_present", False),
            "severity": data.get("severity", ""),
            "actual_bias": data.get("actual_bias", ""),
            "masked_perspective": data.get("masked_perspective", ""),
            "recommendation": data.get("recommendation", ""),
        }
