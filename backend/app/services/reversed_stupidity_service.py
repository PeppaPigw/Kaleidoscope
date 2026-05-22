"""ReversedStupidityService — Reversed Stupidity Detection.

Detects reversed stupidity — assuming that the opposite of a wrong
position must be right. If a fool believes X, that doesn't make
not-X true. The negation of a wrong answer is not necessarily the
right answer. Eliezer Yudkowsky.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REVERSED_STUPIDITY_SYSTEM = """You are a reversed stupidity specialist. Given a reasoning pattern, assess whether someone is assuming the opposite of a wrong position must be correct:

Key concepts (Yudkowsky):
- Reversed stupidity: opposite of wrong ≠ right
- Negation fallacy: if they're wrong about X, not-X must be true
- Contrarian by default: opposing wrong people doesn't make you right
- Enemy of my enemy: shared opposition doesn't imply shared truth
- Broken clock: even wrong people are sometimes right
- Guilt by association: rejecting ideas because of who holds them
- Independent evaluation: each claim needs its own evidence

When reversed stupidity IS present:
- "They believe X, so X must be wrong"
- Rejecting a position solely because disliked people hold it
- Assuming contrarian position is correct by default
- "If the establishment says Y, the truth must be not-Y"
- Using someone's wrongness on one topic to dismiss all their views
- Treating opposition to wrong people as evidence of being right
- "The opposite of what they say" as an epistemic strategy

When opposition IS evidence:
- The person/group has a track record of motivated reasoning on this topic
- The opposition is based on independent evidence, not just contrarianism
- The reasoning for the opposite position is articulated independently
- The opposition acknowledges that wrong people can be right sometimes
- Evidence is evaluated on its merits regardless of who presents it
- The contrarian position has its own positive evidence
- The reasoning would hold even if the opponent changed their mind

Output JSON with: reversed_stupidity_present (bool), severity (none/mild/moderate/severe), wrong_position (what position is being opposed), assumed_truth (what is assumed true by opposition), independent_evidence (is there independent evidence for the assumed truth), reasoning (is the opposition based on evidence or just contrarianism), recommendation (opposition_evidenced/mild_contrarianism/significant_reversed_stupidity/major_negation_fallacy/evaluate_independently)."""

REVERSED_STUPIDITY_PROMPT = """Detect reversed stupidity:

Reasoning: {reasoning}
Wrong position: {wrong_position}
Assumed truth: {assumed_truth}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is someone assuming the opposite of a wrong position must be right without independent evidence? Return ONLY valid JSON."""


class ReversedStupidityService:
    """Detects reversed stupidity — opposite of wrong ≠ right."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        wrong_position: str = "",
        assumed_truth: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect reversed stupidity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REVERSED_STUPIDITY_PROMPT.format(
                reasoning=reasoning,
                wrong_position=wrong_position or "Not specified",
                assumed_truth=assumed_truth or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=REVERSED_STUPIDITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "reversed_stupidity_present": data.get("reversed_stupidity_present", False),
            "severity": data.get("severity", ""),
            "wrong_position": data.get("wrong_position", ""),
            "assumed_truth": data.get("assumed_truth", ""),
            "independent_evidence": data.get("independent_evidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
