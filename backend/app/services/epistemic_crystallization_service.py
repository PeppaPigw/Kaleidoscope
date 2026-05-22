"""EpistemicCrystallizationService — Epistemic Crystallization Detection.

Detects epistemic crystallization — fluid knowledge prematurely
solidifying into rigid structures that resist change.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CRYSTALLIZATION_SYSTEM = """You are an epistemic crystallization specialist. Given a knowledge solidification pattern, assess whether fluid knowledge is prematurely solidifying:

Key concepts:
- Epistemic crystallization: fluid knowledge prematurely solidifying
- Premature rigidity: becoming rigid before fully developed
- Structure lock: locking into structure too early
- Flexibility loss: losing flexibility prematurely
- Growth arrest: growth arrested by premature solidification
- Revision resistance: resisting revision after crystallization
- Brittle formation: forming brittle rather than resilient structures

When epistemic crystallization IS present:
- Fluid knowledge prematurely solidifying into rigid structures
- Becoming rigid before ideas are fully developed
- Locking into structure too early in development
- Losing flexibility before exploration is complete
- Growth arrested by premature solidification
- Resisting revision after crystallizing
- Forming brittle structures that shatter under pressure

When appropriate solidification is present:
- Knowledge solidifying at appropriate developmental stage
- Rigidity appropriate to level of development
- Structure forming after adequate exploration
- Flexibility maintained until appropriate time
- Growth continuing until natural completion
- Revision possible when warranted
- Resilient structures that flex under pressure

Output JSON with: crystallization_present (bool), severity (none/mild/moderate/severe), knowledge (what knowledge crystallizes), prematurity (how premature), rigidity (what rigidity results), growth_arrest (what growth is arrested), recommendation (appropriate_solidification/mild_premature/significant_crystallization/major_premature_rigidity/restore_fluidity)."""

EPISTEMIC_CRYSTALLIZATION_PROMPT = """Detect epistemic crystallization:

Knowledge: {knowledge}
Prematurity: {prematurity}
Rigidity: {rigidity}
Growth arrest: {growth_arrest}
Domain: {domain}
Context: {context}

Is fluid knowledge prematurely solidifying into rigid structures? Return ONLY valid JSON."""


class EpistemicCrystallizationService:
    """Detects epistemic crystallization — premature solidification of knowledge."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        knowledge: str,
        *,
        prematurity: str = "",
        rigidity: str = "",
        growth_arrest: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic crystallization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CRYSTALLIZATION_PROMPT.format(
                knowledge=knowledge,
                prematurity=prematurity or "Not specified",
                rigidity=rigidity or "Not specified",
                growth_arrest=growth_arrest or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CRYSTALLIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "knowledge": knowledge[:200],
            "crystallization_present": data.get("crystallization_present", False),
            "severity": data.get("severity", ""),
            "prematurity": data.get("prematurity", ""),
            "rigidity": data.get("rigidity", ""),
            "growth_arrest": data.get("growth_arrest", ""),
            "recommendation": data.get("recommendation", ""),
        }
