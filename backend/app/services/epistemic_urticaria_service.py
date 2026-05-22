"""EpistemicUrticariaService — Epistemic Urticaria Detection.

Detects epistemic urticaria — sudden hives/welts on intellectual surface
from allergic reaction to new or unfamiliar ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_URTICARIA_SYSTEM = """You are an epistemic urticaria specialist. Given sudden intellectual hives from idea allergy, assess urticaria:

Key concepts:
- Epistemic urticaria: sudden hives from allergic reaction to ideas
- Histamine release: immune overreaction to harmless input
- Wheals: raised itchy welts on intellectual surface
- Angioedema: deep swelling beneath surface
- Acute: lasting less than 6 weeks
- Chronic: persisting beyond 6 weeks
- Antihistamine: blocking overreaction pathway

When epistemic urticaria IS present:
- Sudden hives from new ideas
- Immune overreaction to harmless input
- Raised itchy welts on surface
- Deep swelling beneath surface
- Acute reaction occurring
- Chronic pattern established
- Overreaction pathway active

When no urticaria:
- No hives from new ideas
- Normal immune response to input
- No welts on surface
- No deep swelling
- No acute reactions
- No chronic pattern
- Normal response pathways

Output JSON with: urticaria_detected (bool), severity (none/mild/moderate/severe), reaction_trigger (what ideas cause hives), wheal_pattern (what surface response), angioedema_status (what deep swelling), chronicity (what duration pattern), recommendation (no_urticaria/mild_antihistamine/significant_trigger_avoidance/major_immunomodulation/emergency_anaphylaxis_risk)."""

EPISTEMIC_URTICARIA_PROMPT = """Detect epistemic urticaria:

Reaction trigger: {reaction_trigger}
Wheal pattern: {wheal_pattern}
Angioedema status: {angioedema_status}
Chronicity: {chronicity}
Domain: {domain}
Context: {context}

Are there sudden hives on intellectual surface from allergic reaction to new ideas? Return ONLY valid JSON."""


class EpistemicUrticariaService:
    """Detects epistemic urticaria — sudden hives from allergic reaction to ideas."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reaction_trigger: str,
        *,
        wheal_pattern: str = "",
        angioedema_status: str = "",
        chronicity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic urticaria."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_URTICARIA_PROMPT.format(
                reaction_trigger=reaction_trigger,
                wheal_pattern=wheal_pattern or "Not specified",
                angioedema_status=angioedema_status or "Not specified",
                chronicity=chronicity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_URTICARIA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reaction_trigger": reaction_trigger[:200],
            "urticaria_detected": data.get("urticaria_detected", False),
            "severity": data.get("severity", ""),
            "wheal_pattern": data.get("wheal_pattern", ""),
            "angioedema_status": data.get("angioedema_status", ""),
            "chronicity": data.get("chronicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
