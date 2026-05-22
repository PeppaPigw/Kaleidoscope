"""EpistemicPandemicService — Epistemic Pandemic Detection.

Detects epistemic pandemics — rapid global spread of harmful
epistemic content overwhelming critical thinking capacity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PANDEMIC_SYSTEM = """You are an epistemic pandemic specialist. Given a spread pattern, assess whether harmful epistemic content is spreading globally and overwhelming critical thinking:

Key concepts:
- Epistemic pandemic: global spread overwhelming critical thinking
- Rapid global spread: harmful content spreading across boundaries
- Critical thinking overwhelm: spread faster than evaluation capacity
- Infrastructure collapse: epistemic infrastructure overwhelmed
- Cross-cultural spread: spreading across cultural boundaries
- Mutation during spread: content mutating as it spreads
- Overwhelm of defenses: defenses unable to keep up

When epistemic pandemic IS present:
- Harmful content spreading globally at overwhelming rate
- Spread crossing all normal boundaries
- Critical thinking capacity overwhelmed by volume
- Epistemic infrastructure collapsing under load
- Content spreading across all cultural boundaries
- Content mutating during spread creating variants
- All defenses overwhelmed by speed and volume

When manageable spread is present:
- Content spread at manageable rate
- Normal boundaries containing spread
- Critical thinking capacity adequate
- Epistemic infrastructure functioning
- Cultural boundaries providing natural containment
- Content stable during transmission
- Defenses adequate to manage spread

Output JSON with: pandemic_present (bool), severity (none/mild/moderate/severe), content (what content spreads), spread_rate (how fast it spreads), overwhelm (how defenses are overwhelmed), mutation (how content mutates), recommendation (manageable_spread/mild_acceleration/significant_pandemic/major_global_overwhelm/emergency_epistemic_response)."""

EPISTEMIC_PANDEMIC_PROMPT = """Detect epistemic pandemic:

Content: {content}
Spread rate: {spread_rate}
Overwhelm: {overwhelm}
Mutation: {mutation}
Domain: {domain}
Context: {context}

Is harmful epistemic content spreading globally and overwhelming critical thinking? Return ONLY valid JSON."""


class EpistemicPandemicService:
    """Detects epistemic pandemics — global spread overwhelming critical thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        content: str,
        *,
        spread_rate: str = "",
        overwhelm: str = "",
        mutation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pandemic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PANDEMIC_PROMPT.format(
                content=content,
                spread_rate=spread_rate or "Not specified",
                overwhelm=overwhelm or "Not specified",
                mutation=mutation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PANDEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "content": content[:200],
            "pandemic_present": data.get("pandemic_present", False),
            "severity": data.get("severity", ""),
            "spread_rate": data.get("spread_rate", ""),
            "overwhelm": data.get("overwhelm", ""),
            "mutation": data.get("mutation", ""),
            "recommendation": data.get("recommendation", ""),
        }
