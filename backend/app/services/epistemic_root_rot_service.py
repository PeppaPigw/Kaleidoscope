"""EpistemicRootRotService — Epistemic Root Rot Detection.

Detects epistemic root rot — foundational assumptions decaying
invisibly while surface knowledge appears healthy.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ROOT_ROT_SYSTEM = """You are an epistemic root rot specialist. Given a knowledge system, assess whether foundations are decaying invisibly:

Key concepts:
- Epistemic root rot: foundational assumptions decaying invisibly
- Hidden decay: decay not visible on the surface
- Foundation failure: foundations failing while surface appears healthy
- Invisible damage: damage occurring below the surface
- Sudden collapse: healthy-looking system suddenly collapsing
- Structural compromise: structure compromised from within
- Surface deception: surface health hiding deep decay

When root rot IS present:
- Foundational assumptions decaying invisibly
- Decay not visible on the surface of knowledge
- Foundations failing while surface conclusions appear healthy
- Damage occurring below the visible surface
- Risk of sudden collapse of apparently healthy system
- Structure compromised from within
- Surface health hiding deep foundational decay

When healthy foundations are present:
- Foundational assumptions sound and maintained
- No hidden decay in foundations
- Foundations supporting surface conclusions well
- No invisible damage occurring
- No risk of sudden collapse
- Structure sound throughout
- Surface health reflecting genuine foundational health

Output JSON with: root_rot (bool), severity (none/mild/moderate/severe), foundations (what foundations are decaying), hidden_decay (what decay is hidden), surface_health (what surface appears healthy), collapse_risk (what collapse risk exists), recommendation (healthy_foundations/mild_decay/significant_root_rot/major_foundation_failure/examine_foundations)."""

EPISTEMIC_ROOT_ROT_PROMPT = """Detect epistemic root rot:

Foundations: {foundations}
Hidden decay: {hidden_decay}
Surface health: {surface_health}
Collapse risk: {collapse_risk}
Domain: {domain}
Context: {context}

Are foundational assumptions decaying invisibly while surface knowledge appears healthy? Return ONLY valid JSON."""


class EpistemicRootRotService:
    """Detects epistemic root rot — invisible foundational decay."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        foundations: str,
        *,
        hidden_decay: str = "",
        surface_health: str = "",
        collapse_risk: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic root rot."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ROOT_ROT_PROMPT.format(
                foundations=foundations,
                hidden_decay=hidden_decay or "Not specified",
                surface_health=surface_health or "Not specified",
                collapse_risk=collapse_risk or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ROOT_ROT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "foundations": foundations[:200],
            "root_rot": data.get("root_rot", False),
            "severity": data.get("severity", ""),
            "hidden_decay": data.get("hidden_decay", ""),
            "surface_health": data.get("surface_health", ""),
            "collapse_risk": data.get("collapse_risk", ""),
            "recommendation": data.get("recommendation", ""),
        }
