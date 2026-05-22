"""StrategicIncomprehensionService — Strategic Incomprehension Detection.

Detects strategic incomprehension — pretending not to understand
in order to avoid engagement or shift burden.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_INCOMPREHENSION_SYSTEM = """You are a strategic incomprehension specialist. Given a discourse interaction, assess whether someone is pretending not to understand:

Key concepts:
- Strategic incomprehension: pretending not to understand
- Feigned confusion: performing confusion to avoid engagement
- Willful misunderstanding: deliberately misunderstanding
- Burden shifting through confusion: using confusion to shift burden
- Selective comprehension: understanding selectively for advantage
- Performative ignorance: performing ignorance strategically
- Comprehension as weapon: withholding comprehension as tactic

When strategic incomprehension IS present:
- Understanding feigned to avoid engagement
- Confusion performed rather than genuine
- Misunderstanding deliberate not accidental
- Burden shifted through claimed confusion
- Comprehension selective based on convenience
- Ignorance performed for strategic advantage
- Understanding withheld as tactical move

When genuine difficulty is present:
- Confusion genuine and good-faith
- Misunderstanding accidental and correctable
- Difficulty proportionate to material complexity
- Clarification sought genuinely
- Comprehension limited by genuine constraints
- Ignorance honest and acknowledged
- Understanding sought actively

Output JSON with: incomprehension_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), feigned_confusion (what confusion is feigned), strategic_purpose (what purpose is served), indicators (what indicates strategy), recommendation (genuine_difficulty/mild_avoidance/significant_strategic_incomprehension/major_willful_misunderstanding/engage_honestly)."""

STRATEGIC_INCOMPREHENSION_PROMPT = """Detect strategic incomprehension:

Interaction: {interaction}
Claimed confusion: {confusion}
Strategic purpose: {purpose}
Indicators: {indicators}
Domain: {domain}
Context: {context}

Is someone pretending not to understand to avoid engagement? Return ONLY valid JSON."""


class StrategicIncomprehensionService:
    """Detects strategic incomprehension — pretending not to understand."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        confusion: str = "",
        purpose: str = "",
        indicators: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic incomprehension."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_INCOMPREHENSION_PROMPT.format(
                interaction=interaction,
                confusion=confusion or "Not specified",
                purpose=purpose or "Not specified",
                indicators=indicators or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_INCOMPREHENSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "incomprehension_present": data.get("incomprehension_present", False),
            "severity": data.get("severity", ""),
            "feigned_confusion": data.get("feigned_confusion", ""),
            "strategic_purpose": data.get("strategic_purpose", ""),
            "indicators": data.get("indicators", ""),
            "recommendation": data.get("recommendation", ""),
        }
