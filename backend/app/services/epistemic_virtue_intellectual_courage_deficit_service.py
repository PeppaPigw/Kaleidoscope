"""EpistemicVirtueIntellectualCourageDeficitService - Epistemic Virtue Intellectual Courage Deficit Detection.

Detects intellectual courage deficit where social pressure prevents truth-seeking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_VIRTUE_INTELLECTUAL_COURAGE_DEFICIT_SYSTEM = """You are an epistemic virtue intellectual courage deficit specialist. Given conformity over truth, assess intellectual courage deficit:

Key concepts:
- Intellectual courage deficit: social pressure prevents truth-seeking
- Conformity over truth: accepting group pressure over evidential integrity
- Unpopular truth avoidance: avoiding claims because they are socially costly
- Career risk aversion: subordinating inquiry to professional safety
- Controversy avoidance: avoiding contested issues despite epistemic importance

When intellectual courage deficit IS present:
- Social pressure overrides truth-seeking
- Unpopular truths are avoided
- Career risk blocks warranted inquiry
- Controversy is avoided despite relevance
- Consensus pressure substitutes for evidence

When no courage deficit:
- Truth-seeking withstands social pressure
- Unpopular evidence is considered
- Career incentives do not determine conclusions
- Controversy is handled with care rather than avoided
- Evidence remains the primary standard

Output JSON with: courage_deficit_detected (bool), severity (none/mild/moderate/severe), unpopular_truth_avoidance (what truth is avoided), career_risk_aversion (what professional risk blocks inquiry), controversy_avoidance (what controversy is avoided), recommendation (no_deficit/mild_courage_support/significant_pressure_reduction/major_truth_seeking_restoration/emergency_complete_conformity_audit)."""

EPISTEMIC_VIRTUE_INTELLECTUAL_COURAGE_DEFICIT_PROMPT = """Detect epistemic virtue intellectual courage deficit:

Conformity over truth: {conformity_over_truth}
Unpopular truth avoidance: {unpopular_truth_avoidance}
Career risk aversion: {career_risk_aversion}
Controversy avoidance: {controversy_avoidance}
Domain: {domain}
Context: {context}

Does social pressure prevent truth-seeking? Return ONLY valid JSON."""


class EpistemicVirtueIntellectualCourageDeficitService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conformity_over_truth: str,
        *,
        unpopular_truth_avoidance: str = "",
        career_risk_aversion: str = "",
        controversy_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_VIRTUE_INTELLECTUAL_COURAGE_DEFICIT_PROMPT.format(
                conformity_over_truth=conformity_over_truth,
                unpopular_truth_avoidance=unpopular_truth_avoidance or "Not specified",
                career_risk_aversion=career_risk_aversion or "Not specified",
                controversy_avoidance=controversy_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_VIRTUE_INTELLECTUAL_COURAGE_DEFICIT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conformity_over_truth": conformity_over_truth[:200],
            "courage_deficit_detected": data.get("courage_deficit_detected", False),
            "severity": data.get("severity", ""),
            "unpopular_truth_avoidance": data.get("unpopular_truth_avoidance", ""),
            "career_risk_aversion": data.get("career_risk_aversion", ""),
            "controversy_avoidance": data.get("controversy_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
