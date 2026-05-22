"""MotivatedReasoningService — Motivated Reasoning Detection.

Detects motivated reasoning — where the conclusion is determined
first (by desire, identity, or incentive) and reasoning is
constructed backward to justify it. The person isn't reasoning
toward truth but toward a preferred conclusion. Kunda (1990).
Related to confirmation bias but stronger: actively constructing
justifications rather than just selectively attending to evidence.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_SYSTEM = """You are a motivated reasoning specialist. Given an argument or position, assess whether motivated reasoning is driving the conclusion:

Key concepts:
- Conclusion-first reasoning: the desired outcome determines the argument
- Identity-protective cognition: reasoning to protect group identity/worldview
- Directional goals: wanting to arrive at a particular conclusion
- Accuracy goals: wanting to arrive at the correct conclusion (opposite)
- Rationalization: constructing post-hoc justifications for pre-determined beliefs
- Soldier mindset vs scout mindset (Galef): defending vs discovering

Signs of motivated reasoning:
- Asymmetric skepticism: high bar for unwanted evidence, low bar for wanted evidence
- Selective evidence: cherry-picking supporting data, ignoring contradictions
- Motivated stopping: stopping search when desired conclusion is reached
- Sophistication effect: smarter people are BETTER at motivated reasoning
- Identity threat: the conclusion threatens core identity/group membership

Output JSON with: motivated_reasoning_present (bool), severity (none/mild/moderate/severe/extreme), likely_motivation (identity/financial/political/emotional/social/professional), desired_conclusion (what conclusion is being protected), evidence_asymmetry (bool — different standards for supporting vs opposing evidence?), selective_evidence (bool — cherry-picking?), motivated_stopping (bool — stopped searching at convenient point?), sophistication_effect (bool — using intelligence to rationalize?), identity_threat (what identity is threatened by the alternative conclusion), financial_incentive (what financial interest aligns with the conclusion), social_pressure (what social group demands this conclusion), quality_of_reasoning (how good the reasoning would be if the conclusion weren't predetermined), what_would_change_mind (what evidence would the person accept as disconfirming?), scout_mindset_test (would they be equally happy discovering they were wrong?), steel_man_alternative (strongest version of the conclusion they're avoiding), recommendation (reasoning_appears_genuine/mild_motivation/significant_motivated_reasoning/conclusion_predetermined/identity_protective_cognition)."""

MOTIVATED_PROMPT = """Detect motivated reasoning:

Argument/Position: {argument}
Stated reasoning: {reasoning}
Potential motivations: {motivations}
Evidence handling: {evidence_handling}
Domain: {domain}
Context: {context}

Is motivated reasoning driving this conclusion? Return ONLY valid JSON."""


class MotivatedReasoningService:
    """Detects motivated reasoning — conclusion-first rationalization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        argument: str,
        *,
        reasoning: str = "",
        motivations: str = "",
        evidence_handling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated reasoning."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_PROMPT.format(
                argument=argument,
                reasoning=reasoning or "Not specified",
                motivations=motivations or "Not specified",
                evidence_handling=evidence_handling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "argument": argument[:200],
            "motivated_reasoning_present": data.get("motivated_reasoning_present", False),
            "severity": data.get("severity", ""),
            "likely_motivation": data.get("likely_motivation", ""),
            "desired_conclusion": data.get("desired_conclusion", ""),
            "evidence_asymmetry": data.get("evidence_asymmetry", False),
            "selective_evidence": data.get("selective_evidence", False),
            "motivated_stopping": data.get("motivated_stopping", False),
            "sophistication_effect": data.get("sophistication_effect", False),
            "identity_threat": data.get("identity_threat", ""),
            "financial_incentive": data.get("financial_incentive", ""),
            "social_pressure": data.get("social_pressure", ""),
            "quality_of_reasoning": data.get("quality_of_reasoning", ""),
            "what_would_change_mind": data.get("what_would_change_mind", ""),
            "scout_mindset_test": data.get("scout_mindset_test", ""),
            "steel_man_alternative": data.get("steel_man_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
