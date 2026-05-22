"""MunchausenTrilemmaService — Munchausen Trilemma Detection.

Detects Munchausen trilemma — when a justification chain reveals
one of three unavoidable problems: infinite regress (each justification
needs further justification), circularity (the chain loops back),
or axiomatic stopping (accepting an unjustified starting point).
Agrippa/Albert (1968).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MUNCHAUSEN_TRILEMMA_SYSTEM = """You are a Munchausen trilemma specialist. Given a justification chain, assess whether it exhibits infinite regress, circularity, or dogmatic stopping:

Key concepts (Agrippa's trilemma / Albert, 1968):
- Munchausen trilemma: all justification chains face three problems
- Infinite regress: each justification requires further justification
- Circular reasoning: the chain eventually loops back to its starting point
- Dogmatic stopping: accepting a premise without justification (axiom)
- Foundationalism: accepting some beliefs as self-justifying
- Coherentism: accepting circular justification if the circle is large enough
- Pragmatic stopping: stopping where further justification adds no value

When trilemma IS problematic:
- Demanding infinite justification to avoid accepting any conclusion
- Circular reasoning disguised as a long chain
- Dogmatic assertions presented as self-evident when they're contested
- Using the trilemma to dismiss all knowledge claims
- Hiding the stopping point to avoid scrutiny of assumptions
- Pretending a circular argument is linear
- Demanding foundations that nothing could provide

When stopping IS appropriate:
- The axiom is genuinely shared by all parties
- The stopping point is explicitly acknowledged
- Pragmatic foundations that work reliably
- The circle is large enough to be informative (coherentism)
- Further justification would not change the conclusion
- The domain has well-established foundational assumptions
- The stopping point is the actual point of disagreement (making it explicit)

Output JSON with: trilemma_present (bool), severity (none/mild/moderate/severe), justification_chain (the chain analyzed), trilemma_type (regress/circularity/dogmatic_stopping), stopping_point (where does justification stop), acknowledged (is the stopping point acknowledged), problematic (is this instance of the trilemma problematic), recommendation (stopping_appropriate/mild_foundation_issue/significant_trilemma/major_justification_failure/acknowledge_assumptions)."""

MUNCHAUSEN_TRILEMMA_PROMPT = """Detect Munchausen trilemma:

Justification: {justification}
Chain: {chain}
Foundation: {foundation}
Challenge: {challenge}
Domain: {domain}
Context: {context}

Does this justification chain exhibit infinite regress, circularity, or dogmatic stopping? Return ONLY valid JSON."""


class MunchausenTrilemmaService:
    """Detects Munchausen trilemma in justification chains."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        justification: str,
        *,
        chain: str = "",
        foundation: str = "",
        challenge: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Munchausen trilemma."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MUNCHAUSEN_TRILEMMA_PROMPT.format(
                justification=justification,
                chain=chain or "Not specified",
                foundation=foundation or "Not specified",
                challenge=challenge or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MUNCHAUSEN_TRILEMMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "justification": justification[:200],
            "trilemma_present": data.get("trilemma_present", False),
            "severity": data.get("severity", ""),
            "trilemma_type": data.get("trilemma_type", ""),
            "stopping_point": data.get("stopping_point", ""),
            "acknowledged": data.get("acknowledged", ""),
            "problematic": data.get("problematic", ""),
            "recommendation": data.get("recommendation", ""),
        }
