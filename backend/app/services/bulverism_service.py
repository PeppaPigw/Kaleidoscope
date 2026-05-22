"""BulverismService — Bulverism Detection.

Detects bulverism — assuming someone is wrong and then explaining
why they believe it, rather than first showing that they are wrong.
C.S. Lewis (1941). Named after a fictional character Ezekiel Bulver
whose mother said "assume your opponent is wrong, then explain his
error, and the world will be at your feet."
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BULVERISM_SYSTEM = """You are a bulverism specialist. Given an argument or response, assess whether it assumes the opponent is wrong and explains why they believe it rather than addressing the argument itself:

Key concepts (C.S. Lewis, 1941):
- Bulverism: assuming error then explaining its psychological cause
- Genetic fallacy overlap: judging truth by origin rather than content
- Psychologizing: explaining away beliefs rather than engaging them
- Motive attribution: "you only believe X because Y"
- Ad hominem variant: attacking the believer rather than the belief
- Poisoning the well: discrediting before engaging
- Explanation vs. refutation: explaining why someone believes X ≠ showing X is false

When bulverism IS present:
- "You only think that because you're a [group]"
- Explaining psychological/social reasons for a belief without addressing it
- "Of course you'd say that, given your background"
- Treating the cause of a belief as a refutation of it
- Psychoanalyzing the opponent instead of engaging their argument
- "That's just your [privilege/bias/upbringing] talking"
- Assuming error and jumping straight to explaining the error's origin

When psychological explanation IS appropriate:
- The argument has already been refuted on its merits
- The explanation is offered as additional context, not as refutation
- Understanding motivation is explicitly the goal (not winning the argument)
- The person has acknowledged their reasoning may be influenced
- The psychological explanation is offered alongside substantive engagement
- It's a meta-discussion about reasoning patterns, not a live debate

Output JSON with: bulverism_present (bool), severity (none/mild/moderate/severe), argument (what argument is being addressed), response (how it's being responded to), assumption (what error is being assumed), explanation (what psychological cause is attributed), engagement (is the argument itself addressed), recommendation (explanation_appropriate/mild_psychologizing/significant_bulverism/major_argument_avoidance/address_argument_first)."""

BULVERISM_PROMPT = """Detect bulverism:

Argument: {argument}
Response: {response}
Attribution: {attribution}
Engagement: {engagement}
Domain: {domain}
Context: {context}

Is the response assuming error and explaining its cause rather than addressing the argument? Return ONLY valid JSON."""


class BulverismService:
    """Detects bulverism — assuming error then explaining its cause."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        response: str = "",
        attribution: str = "",
        engagement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bulverism."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BULVERISM_PROMPT.format(
                argument=argument,
                response=response or "Not specified",
                attribution=attribution or "Not specified",
                engagement=engagement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BULVERISM_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "bulverism_present": data.get("bulverism_present", False),
            "severity": data.get("severity", ""),
            "assumption": data.get("assumption", ""),
            "explanation": data.get("explanation", ""),
            "engagement": data.get("engagement", ""),
            "recommendation": data.get("recommendation", ""),
        }
