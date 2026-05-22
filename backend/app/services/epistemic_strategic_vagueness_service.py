"""EpistemicStrategicVaguenessService — Epistemic Strategic Vagueness Detection.

Detects epistemic strategic vagueness — using vagueness strategically
to avoid commitment or accountability.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRATEGIC_VAGUENESS_SYSTEM = """You are an epistemic strategic vagueness specialist. Given using vagueness to avoid commitment, assess strategic vagueness:

Key concepts:
- Epistemic strategic vagueness: using vagueness to avoid commitment
- Commitment avoidance: being vague to avoid being held to positions
- Accountability escape: vagueness as escape from accountability
- Plausible deniability: vague enough to deny any interpretation
- Precision avoidance: refusing to be specific when specificity is needed
- Weasel language: using language that sounds meaningful but commits to nothing
- Ambiguity exploitation: exploiting ambiguity for strategic advantage

When epistemic strategic vagueness IS present:
- Using vagueness to avoid commitment
- Being vague to avoid being held
- Vagueness as accountability escape
- Vague enough to deny anything
- Refusing needed specificity
- Language committing to nothing
- Exploiting ambiguity strategically

When no strategic vagueness:
- Appropriate precision
- Clear commitments
- Accountable statements
- Specific positions
- Precise when needed
- Meaningful language
- Honest ambiguity

Output JSON with: strategic_vagueness_detected (bool), severity (none/mild/moderate/severe), commitment_avoidance (what being vague to avoid), accountability_escape (what escaping through vagueness), plausible_deniability (what maintaining deniability about), precision_avoidance (what refusing specificity about), recommendation (no_strategic_vagueness/mild_precision_practice/significant_commitment_building/major_intensive_accountability_work/emergency_complete_strategic_vagueness)."""

EPISTEMIC_STRATEGIC_VAGUENESS_PROMPT = """Detect epistemic strategic vagueness:

Commitment avoidance: {commitment_avoidance}
Accountability escape: {accountability_escape}
Plausible deniability: {plausible_deniability}
Precision avoidance: {precision_avoidance}
Domain: {domain}
Context: {context}

Is there using vagueness strategically to avoid commitment or accountability? Return ONLY valid JSON."""


class EpistemicStrategicVaguenessService:
    """Detects epistemic strategic vagueness — using vagueness to avoid commitment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        commitment_avoidance: str,
        *,
        accountability_escape: str = "",
        plausible_deniability: str = "",
        precision_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic strategic vagueness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRATEGIC_VAGUENESS_PROMPT.format(
                commitment_avoidance=commitment_avoidance,
                accountability_escape=accountability_escape or "Not specified",
                plausible_deniability=plausible_deniability or "Not specified",
                precision_avoidance=precision_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRATEGIC_VAGUENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "commitment_avoidance": commitment_avoidance[:200],
            "strategic_vagueness_detected": data.get("strategic_vagueness_detected", False),
            "severity": data.get("severity", ""),
            "accountability_escape": data.get("accountability_escape", ""),
            "plausible_deniability": data.get("plausible_deniability", ""),
            "precision_avoidance": data.get("precision_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
