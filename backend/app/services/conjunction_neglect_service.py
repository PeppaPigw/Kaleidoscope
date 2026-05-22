"""ConjunctionNeglectService — Conjunction Neglect Detection.

Detects conjunction neglect — the failure to recognize that
combining multiple conditions always reduces (or maintains)
probability. People often judge conjunctions as more likely
than their components due to representativeness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONJUNCTION_NEGLECT_SYSTEM = """You are a conjunction neglect specialist. Given a probability judgment, assess whether conjunction rules are being violated:

Key concepts:
- Conjunction rule: P(A and B) <= P(A) for any events A and B
- Representativeness: conjunctions seem more likely when they fit a narrative
- Unpacking effect: listing components makes conjunction seem more probable
- Scenario thinking: detailed scenarios feel more likely than vague ones
- Probability neglect: ignoring that each added condition reduces probability
- Linda problem: classic demonstration of conjunction fallacy
- Planning fallacy connection: detailed plans seem more achievable

When conjunction neglect IS present:
- A specific scenario judged more likely than a general one it's part of
- Adding detail makes something seem more probable
- Multiple conditions assumed to all hold without probability reduction
- "It's likely that A AND B AND C" without recognizing compounding
- Detailed narrative treated as more probable than simple prediction
- Plan assumes multiple things go right without discounting
- Scenario with many conditions treated as base case

When conjunction neglect is NOT present:
- Probability properly discounted for each additional condition
- Conjunction rule explicitly applied
- Simpler predictions preferred over detailed scenarios
- Multiple conditions recognized as reducing overall probability
- Base rates maintained when adding specificity
- Planning accounts for probability of each step succeeding
- Distinction made between plausibility and probability

Output JSON with: neglect_present (bool), severity (none/mild/moderate/severe), conjunction (what conditions are being combined), individual_probabilities (rough probability of each), combined_probability (what the conjunction probability should be), stated_probability (what probability is being claimed), recommendation (no_neglect/mild_overestimate/significant_conjunction_neglect/major_probability_error/apply_conjunction_rule)."""

CONJUNCTION_NEGLECT_PROMPT = """Detect conjunction neglect:

Claim: {claim}
Conditions: {conditions}
Probability stated: {probability}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is the conjunction rule being violated in this probability judgment? Return ONLY valid JSON."""


class ConjunctionNeglectService:
    """Detects conjunction neglect — failure to discount for combined conditions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        conditions: str = "",
        probability: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect conjunction neglect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONJUNCTION_NEGLECT_PROMPT.format(
                claim=claim,
                conditions=conditions or "Not specified",
                probability=probability or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONJUNCTION_NEGLECT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "neglect_present": data.get("neglect_present", False),
            "severity": data.get("severity", ""),
            "conjunction": data.get("conjunction", ""),
            "combined_probability": data.get("combined_probability", ""),
            "stated_probability": data.get("stated_probability", ""),
            "recommendation": data.get("recommendation", ""),
        }
