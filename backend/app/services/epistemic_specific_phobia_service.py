"""EpistemicSpecificPhobiaService — Epistemic Specific Phobia Detection.

Detects epistemic specific phobia — irrational intense fear of a
particular knowledge domain or intellectual topic.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SPECIFIC_PHOBIA_SYSTEM = """You are an epistemic specific phobia specialist. Given irrational fear of a knowledge domain, assess specific phobia:

Key concepts:
- Epistemic specific phobia: irrational fear of particular domain
- Disproportionate: fear exceeds actual intellectual danger
- Immediate anxiety: instant distress upon encountering topic
- Avoidance: complete refusal to engage with feared domain
- Recognition: knowing fear is irrational but unable to control
- Interference: phobia limiting intellectual development
- Generalization: fear spreading to related domains

When epistemic specific phobia IS present:
- Irrational fear of particular domain
- Fear exceeds actual danger
- Instant distress on encounter
- Complete refusal to engage
- Knowing fear is irrational
- Limiting intellectual development
- Fear spreading to related areas

When no specific phobia:
- Rational domain assessment
- Proportionate concern
- Calm on encounter
- Willing to engage
- Rational control
- Unrestricted development
- No fear spreading

Output JSON with: specific_phobia_detected (bool), severity (none/mild/moderate/severe), feared_domain (what topic/area), fear_intensity (what distress level), avoidance_extent (what refusal), interference_level (what limitation), recommendation (no_specific_phobia/mild_gradual_exposure/significant_systematic_desensitization/major_intensive_therapy/emergency_complete_avoidance)."""

EPISTEMIC_SPECIFIC_PHOBIA_PROMPT = """Detect epistemic specific phobia:

Feared domain: {feared_domain}
Fear intensity: {fear_intensity}
Avoidance extent: {avoidance_extent}
Interference level: {interference_level}
Domain: {domain}
Context: {context}

Is there irrational intense fear of a particular knowledge domain? Return ONLY valid JSON."""


class EpistemicSpecificPhobiaService:
    """Detects epistemic specific phobia — fear of particular domain."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        feared_domain: str,
        *,
        fear_intensity: str = "",
        avoidance_extent: str = "",
        interference_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic specific phobia."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SPECIFIC_PHOBIA_PROMPT.format(
                feared_domain=feared_domain,
                fear_intensity=fear_intensity or "Not specified",
                avoidance_extent=avoidance_extent or "Not specified",
                interference_level=interference_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SPECIFIC_PHOBIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "feared_domain": feared_domain[:200],
            "specific_phobia_detected": data.get("specific_phobia_detected", False),
            "severity": data.get("severity", ""),
            "fear_intensity": data.get("fear_intensity", ""),
            "avoidance_extent": data.get("avoidance_extent", ""),
            "interference_level": data.get("interference_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
