"""EpistemicDerealizationService — Epistemic Derealization Detection.

Detects epistemic derealization — the intellectual world feeling unreal,
dreamlike, or lacking substance and significance.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEREALIZATION_SYSTEM = """You are an epistemic derealization specialist. Given intellectual world feeling unreal, assess derealization:

Key concepts:
- Epistemic derealization: intellectual world feels unreal
- Dreamlike quality: ideas feel like a dream
- Substance loss: knowledge lacks weight or reality
- Significance drain: nothing feels intellectually important
- Glass wall: separated from intellectual world by barrier
- Fog: intellectual landscape obscured and distant
- Artificiality: everything feels staged or fake

When epistemic derealization IS present:
- Intellectual world feels unreal
- Ideas feel dreamlike
- Knowledge lacks weight
- Nothing feels important
- Separated by barrier
- Landscape obscured
- Everything feels fake

When no derealization:
- World feels real
- Ideas feel solid
- Knowledge has weight
- Things feel important
- Connected to world
- Clear landscape
- Authentic experience

Output JSON with: derealization_detected (bool), severity (none/mild/moderate/severe), dreamlike_quality (what feels unreal), substance_loss (what lacks weight), significance_drain (what not important), glass_wall (what separated from), recommendation (no_derealization/mild_grounding_practice/significant_reality_reconnection/major_intensive_therapy/emergency_severe_derealization)."""

EPISTEMIC_DEREALIZATION_PROMPT = """Detect epistemic derealization:

Dreamlike quality: {dreamlike_quality}
Substance loss: {substance_loss}
Significance drain: {significance_drain}
Glass wall: {glass_wall}
Domain: {domain}
Context: {context}

Is the intellectual world feeling unreal or dreamlike? Return ONLY valid JSON."""


class EpistemicDerealizationService:
    """Detects epistemic derealization — intellectual world feels unreal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dreamlike_quality: str,
        *,
        substance_loss: str = "",
        significance_drain: str = "",
        glass_wall: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic derealization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEREALIZATION_PROMPT.format(
                dreamlike_quality=dreamlike_quality,
                substance_loss=substance_loss or "Not specified",
                significance_drain=significance_drain or "Not specified",
                glass_wall=glass_wall or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEREALIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dreamlike_quality": dreamlike_quality[:200],
            "derealization_detected": data.get("derealization_detected", False),
            "severity": data.get("severity", ""),
            "substance_loss": data.get("substance_loss", ""),
            "significance_drain": data.get("significance_drain", ""),
            "glass_wall": data.get("glass_wall", ""),
            "recommendation": data.get("recommendation", ""),
        }
