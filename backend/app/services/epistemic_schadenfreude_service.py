"""EpistemicSchadenfreudeService — Epistemic Schadenfreude Detection.

Detects epistemic schadenfreude — pleasure derived from others'
intellectual failures or epistemic misfortunes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCHADENFREUDE_SYSTEM = """You are an epistemic schadenfreude specialist. Given pleasure in others' intellectual failures, assess schadenfreude:

Key concepts:
- Epistemic schadenfreude: pleasure from others' intellectual failures
- Failure celebration: enjoying when others are wrong
- Vindication seeking: wanting proof others are inferior
- Competitive glee: joy when rivals stumble
- Moral disguise: hiding schadenfreude as justice
- Downward comparison: feeling better through others' misfortune
- Covert satisfaction: hidden pleasure in others' struggles

When epistemic schadenfreude IS present:
- Pleasure from others' failures
- Enjoying when others wrong
- Wanting proof others inferior
- Joy when rivals stumble
- Hiding as justice
- Feeling better through misfortune
- Hidden pleasure in struggles

When no schadenfreude:
- Compassion for failures
- Empathy when others wrong
- No need to prove inferior
- Concern when rivals stumble
- Genuine justice concern
- Not comparing downward
- No hidden pleasure

Output JSON with: schadenfreude_detected (bool), severity (none/mild/moderate/severe), failure_celebration (what enjoying), vindication_seeking (what proving), competitive_glee (what joy from), moral_disguise (what hiding as), recommendation (no_schadenfreude/mild_compassion_building/significant_empathy_practice/major_intensive_compassion_therapy/emergency_active_cruelty)."""

EPISTEMIC_SCHADENFREUDE_PROMPT = """Detect epistemic schadenfreude:

Failure celebration: {failure_celebration}
Vindication seeking: {vindication_seeking}
Competitive glee: {competitive_glee}
Moral disguise: {moral_disguise}
Domain: {domain}
Context: {context}

Is there pleasure derived from others' intellectual failures? Return ONLY valid JSON."""


class EpistemicSchadenfreudeService:
    """Detects epistemic schadenfreude — pleasure from others' intellectual failures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        failure_celebration: str,
        *,
        vindication_seeking: str = "",
        competitive_glee: str = "",
        moral_disguise: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic schadenfreude."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCHADENFREUDE_PROMPT.format(
                failure_celebration=failure_celebration,
                vindication_seeking=vindication_seeking or "Not specified",
                competitive_glee=competitive_glee or "Not specified",
                moral_disguise=moral_disguise or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCHADENFREUDE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "failure_celebration": failure_celebration[:200],
            "schadenfreude_detected": data.get("schadenfreude_detected", False),
            "severity": data.get("severity", ""),
            "vindication_seeking": data.get("vindication_seeking", ""),
            "competitive_glee": data.get("competitive_glee", ""),
            "moral_disguise": data.get("moral_disguise", ""),
            "recommendation": data.get("recommendation", ""),
        }
