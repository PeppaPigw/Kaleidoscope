"""EpistemicDependentService — Epistemic Dependent Detection.

Detects epistemic dependence — excessive need for intellectual guidance
with inability to make independent intellectual decisions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEPENDENT_SYSTEM = """You are an epistemic dependence specialist. Given excessive need for intellectual guidance, assess dependent patterns:

Key concepts:
- Epistemic dependence: excessive need for intellectual guidance
- Decision inability: cannot make intellectual choices alone
- Reassurance seeking: constantly needing validation
- Submission: agreeing with authority to maintain support
- Helplessness: feeling unable to function intellectually alone
- Separation anxiety: distress when intellectual guide unavailable
- Clinging: excessive attachment to intellectual authority

When epistemic dependence IS present:
- Excessive need for guidance
- Cannot make choices alone
- Constantly needing validation
- Agreeing with authority
- Unable to function alone
- Distress when guide unavailable
- Excessive attachment to authority

When no dependence:
- Self-directed intellectual work
- Independent decision-making
- Internal validation
- Appropriate disagreement
- Autonomous functioning
- Comfortable alone
- Healthy relationships with authority

Output JSON with: dependent_detected (bool), severity (none/mild/moderate/severe), guidance_need (what reliance), decision_capacity (what independence), reassurance_frequency (what validation seeking), authority_submission (what compliance), recommendation (no_dependence/mild_autonomy_building/significant_assertiveness_training/major_intensive_independence/emergency_complete_helplessness)."""

EPISTEMIC_DEPENDENT_PROMPT = """Detect epistemic dependence:

Guidance need: {guidance_need}
Decision capacity: {decision_capacity}
Reassurance frequency: {reassurance_frequency}
Authority submission: {authority_submission}
Domain: {domain}
Context: {context}

Is there excessive need for intellectual guidance with inability to decide independently? Return ONLY valid JSON."""


class EpistemicDependentService:
    """Detects epistemic dependence — excessive need for intellectual guidance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        guidance_need: str,
        *,
        decision_capacity: str = "",
        reassurance_frequency: str = "",
        authority_submission: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dependence."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEPENDENT_PROMPT.format(
                guidance_need=guidance_need,
                decision_capacity=decision_capacity or "Not specified",
                reassurance_frequency=reassurance_frequency or "Not specified",
                authority_submission=authority_submission or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEPENDENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "guidance_need": guidance_need[:200],
            "dependent_detected": data.get("dependent_detected", False),
            "severity": data.get("severity", ""),
            "decision_capacity": data.get("decision_capacity", ""),
            "reassurance_frequency": data.get("reassurance_frequency", ""),
            "authority_submission": data.get("authority_submission", ""),
            "recommendation": data.get("recommendation", ""),
        }
