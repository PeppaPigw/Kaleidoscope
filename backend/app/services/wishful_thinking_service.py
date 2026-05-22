"""WishfulThinkingService — Wishful Thinking Detection.

Detects wishful thinking — believing something is true or
likely because one wants it to be true, rather than because
of evidence. Leads to unrealistic planning, inadequate risk
preparation, and decisions based on hope rather than data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WISHFUL_THINKING_SYSTEM = """You are a wishful thinking specialist. Given a belief or prediction, assess whether it's driven by desire rather than evidence:

Key concepts:
- Wishful thinking: believing because you want it to be true
- Desirability bias: desired outcomes judged as more likely
- Motivated reasoning overlap: but wishful thinking is specifically about probability
- Optimism bias overlap: but wishful thinking is about specific beliefs, not general outlook
- Planning fallacy interaction: wishful thinking about timelines
- Denial: refusing to accept unwanted truths
- Fantasy-based planning: plans built on hoped-for rather than likely outcomes

When wishful thinking IS present:
- "It'll work out" without evidence or plan
- Assigning high probability to desired outcomes without justification
- Ignoring evidence that the desired outcome is unlikely
- Planning based on best-case scenarios as if they're expected
- "I'm sure they'll say yes" without basis
- Dismissing risks because the desired outcome "has to" happen

When the belief IS evidence-based:
- Probability assessment is based on data, not desire
- The person can articulate evidence independent of their wishes
- They acknowledge the possibility of undesired outcomes
- Their confidence level matches the evidence strength
- They have contingency plans for if the desired outcome doesn't occur

Output JSON with: wishful_thinking_present (bool), severity (none/mild/moderate/severe), belief (what is being believed), desire (what does the person want to be true), evidence_for (what evidence supports the belief?), evidence_against (what evidence contradicts it?), probability_assigned (what probability is being assigned?), evidence_based_probability (what would evidence-based probability be?), contingency_planning (bool — are alternative outcomes planned for?), consequences_of_wrong (what happens if the belief is wrong?), recommendation (belief_evidence_based/mild_wishful_thinking/significant_desire_driven/major_wishful_thinking/base_on_evidence_not_desire)."""

WISHFUL_THINKING_PROMPT = """Detect wishful thinking:

Belief: {belief}
Desire: {desire}
Evidence: {evidence}
Planning: {planning}
Domain: {domain}
Context: {context}

Is this belief driven by desire rather than evidence? Return ONLY valid JSON."""


class WishfulThinkingService:
    """Detects wishful thinking — believing because you want it to be true."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        desire: str = "",
        evidence: str = "",
        planning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect wishful thinking."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WISHFUL_THINKING_PROMPT.format(
                belief=belief,
                desire=desire or "Not specified",
                evidence=evidence or "Not specified",
                planning=planning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WISHFUL_THINKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "wishful_thinking_present": data.get("wishful_thinking_present", False),
            "severity": data.get("severity", ""),
            "desire": data.get("desire", ""),
            "evidence_for": data.get("evidence_for", ""),
            "evidence_against": data.get("evidence_against", ""),
            "probability_assigned": data.get("probability_assigned", ""),
            "evidence_based_probability": data.get("evidence_based_probability", ""),
            "contingency_planning": data.get("contingency_planning", True),
            "consequences_of_wrong": data.get("consequences_of_wrong", ""),
            "recommendation": data.get("recommendation", ""),
        }
