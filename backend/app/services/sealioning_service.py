"""SealioningService — Sealioning Detection.

Detects sealioning — a form of bad-faith engagement where someone
makes persistent, polite requests for evidence or debate that are
designed to exhaust rather than to learn. The requests appear
reasonable individually but are disingenuous in aggregate.
Wondermark comic (2014).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SEALIONING_SYSTEM = """You are a sealioning specialist. Given an interaction pattern, assess whether persistent requests for evidence or debate are made in bad faith to exhaust rather than to learn:

Key concepts (Wondermark, 2014):
- Sealioning: bad-faith requests disguised as polite inquiry
- JAQing off: "just asking questions" as harassment technique
- Concern trolling overlap: feigning interest to waste time
- Exhaustion strategy: wearing down opponents through persistence
- Plausible deniability: each request seems reasonable in isolation
- Moving goalposts: no amount of evidence is ever sufficient
- Performative civility: using politeness as a weapon

When sealioning IS present:
- Persistent requests for evidence that are never satisfied
- "I'm just asking questions" with no genuine interest in answers
- Polite tone masking bad-faith engagement
- Each answer generates more questions without progress
- The questioner shows no signs of updating their views
- Requests that would be reasonable once but are exhausting in aggregate
- Demanding engagement as if it's owed

When persistent questioning IS appropriate:
- The questioner genuinely updates based on answers
- The questions build toward understanding
- The questioner acknowledges good answers
- The persistence reflects genuine confusion, not strategy
- The questioner has skin in the game (consequences for being wrong)
- Questions are specific and answerable
- The interaction shows mutual good faith

Output JSON with: sealioning_present (bool), severity (none/mild/moderate/severe), interaction (the interaction pattern), requests (what is being requested), good_faith_indicators (signs of genuine inquiry), bad_faith_indicators (signs of exhaustion strategy), updating (does the questioner update based on answers), recommendation (genuine_inquiry/mild_persistence/significant_sealioning/major_bad_faith_exhaustion/disengage_or_set_boundaries)."""

SEALIONING_PROMPT = """Detect sealioning:

Interaction: {interaction}
Requests: {requests}
Responses: {responses}
Pattern: {pattern}
Domain: {domain}
Context: {context}

Are persistent requests for evidence being made in bad faith to exhaust rather than to learn? Return ONLY valid JSON."""


class SealioningService:
    """Detects sealioning — bad-faith requests disguised as polite inquiry."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        interaction: str,
        *,
        requests: str = "",
        responses: str = "",
        pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect sealioning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SEALIONING_PROMPT.format(
                interaction=interaction,
                requests=requests or "Not specified",
                responses=responses or "Not specified",
                pattern=pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SEALIONING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "interaction": interaction[:200],
            "sealioning_present": data.get("sealioning_present", False),
            "severity": data.get("severity", ""),
            "bad_faith_indicators": data.get("bad_faith_indicators", ""),
            "good_faith_indicators": data.get("good_faith_indicators", ""),
            "updating": data.get("updating", ""),
            "recommendation": data.get("recommendation", ""),
        }
