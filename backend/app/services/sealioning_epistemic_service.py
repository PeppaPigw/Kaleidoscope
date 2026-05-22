"""SealioningEpistemicService — Epistemic Sealioning Detection.

Detects epistemic sealioning — bad-faith demands for evidence
designed to exhaust opponents rather than genuinely seek understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SEALIONING_EPISTEMIC_SYSTEM = """You are an epistemic sealioning specialist. Given a discourse interaction, assess whether demands for evidence are made in bad faith to exhaust rather than understand:

Key concepts:
- Epistemic sealioning: bad-faith evidence demands to exhaust
- Performative curiosity: appearing curious without genuine interest
- Evidence exhaustion: demanding evidence to tire opponents
- Moving evidence goalposts: never accepting any evidence as sufficient
- Burden shifting: constantly shifting burden of proof
- Polite harassment: using politeness to mask bad-faith demands
- Infinite regress demands: always demanding more justification

When epistemic sealioning IS present:
- Evidence demands made in bad faith
- Goal is exhaustion not understanding
- No evidence would ever be accepted as sufficient
- Goalposts moved after each response
- Burden of proof shifted unfairly
- Politeness masking harassment
- Demands designed to tire not learn

When genuine inquiry is present:
- Evidence requests made in good faith
- Goal is genuine understanding
- Evidence would change the questioner's mind
- Standards consistent and reasonable
- Burden of proof fairly distributed
- Politeness reflecting genuine respect
- Questions seeking actual answers

Output JSON with: sealioning_present (bool), severity (none/mild/moderate/severe), interaction (what interaction occurs), demands (what demands are made), bad_faith_indicators (what indicates bad faith), exhaustion_goal (how exhaustion is pursued), recommendation (genuine_inquiry/mild_persistence/significant_epistemic_sealioning/major_bad_faith_demands/engage_genuinely_or_disengage)."""

SEALIONING_EPISTEMIC_PROMPT = """Detect epistemic sealioning:

Interaction: {interaction}
Demands made: {demands}
Response pattern: {response_pattern}
Indicators: {indicators}
Domain: {domain}
Context: {context}

Are evidence demands being made in bad faith to exhaust rather than understand? Return ONLY valid JSON."""


class SealioningEpistemicService:
    """Detects epistemic sealioning — bad-faith evidence demands to exhaust."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        demands: str = "",
        response_pattern: str = "",
        indicators: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sealioning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SEALIONING_EPISTEMIC_PROMPT.format(
                interaction=interaction,
                demands=demands or "Not specified",
                response_pattern=response_pattern or "Not specified",
                indicators=indicators or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SEALIONING_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "sealioning_present": data.get("sealioning_present", False),
            "severity": data.get("severity", ""),
            "demands": data.get("demands", ""),
            "bad_faith_indicators": data.get("bad_faith_indicators", ""),
            "exhaustion_goal": data.get("exhaustion_goal", ""),
            "recommendation": data.get("recommendation", ""),
        }
