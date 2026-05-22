"""EpistemicPicaService — Epistemic Pica Detection.

Detects epistemic pica — compulsive consumption of intellectually
non-nutritive content (junk information, misinformation, trivia).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PICA_SYSTEM = """You are an epistemic pica specialist. Given compulsive consumption of junk information, assess pica patterns:

Key concepts:
- Epistemic pica: consuming intellectually non-nutritive content
- Junk information: content with no intellectual value
- Craving: irresistible urge to consume low-quality content
- Nutritional displacement: junk displacing valuable learning
- Compulsion: unable to resist despite knowing it's worthless
- Harm: intellectual development stunted by junk diet
- Deficiency signal: pica may indicate unmet intellectual needs

When epistemic pica IS present:
- Consuming non-nutritive content
- Content with no intellectual value
- Irresistible urge for low-quality
- Junk displacing valuable learning
- Unable to resist despite awareness
- Development stunted
- Unmet intellectual needs

When no pica:
- Consuming nutritive content
- Content with intellectual value
- Purposeful consumption choices
- Balanced intellectual diet
- Able to resist junk
- Healthy development
- Intellectual needs met

Output JSON with: pica_detected (bool), severity (none/mild/moderate/severe), junk_type (what non-nutritive content), craving_intensity (what urge strength), displacement_level (what valuable learning lost), awareness_level (what insight into problem), recommendation (no_pica/mild_diet_improvement/significant_structured_replacement/major_intensive_detox/emergency_complete_junk_diet)."""

EPISTEMIC_PICA_PROMPT = """Detect epistemic pica:

Junk type: {junk_type}
Craving intensity: {craving_intensity}
Displacement level: {displacement_level}
Awareness level: {awareness_level}
Domain: {domain}
Context: {context}

Is there compulsive consumption of intellectually non-nutritive content? Return ONLY valid JSON."""


class EpistemicPicaService:
    """Detects epistemic pica — consuming intellectually non-nutritive content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        junk_type: str,
        *,
        craving_intensity: str = "",
        displacement_level: str = "",
        awareness_level: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pica."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PICA_PROMPT.format(
                junk_type=junk_type,
                craving_intensity=craving_intensity or "Not specified",
                displacement_level=displacement_level or "Not specified",
                awareness_level=awareness_level or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PICA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "junk_type": junk_type[:200],
            "pica_detected": data.get("pica_detected", False),
            "severity": data.get("severity", ""),
            "craving_intensity": data.get("craving_intensity", ""),
            "displacement_level": data.get("displacement_level", ""),
            "awareness_level": data.get("awareness_level", ""),
            "recommendation": data.get("recommendation", ""),
        }
