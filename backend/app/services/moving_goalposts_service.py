"""MovingGoalpostsService — Moving the Goalposts Detection.

Detects moving the goalposts — changing the criteria for proof
or success after evidence meeting the original criteria has been
presented, making it impossible to ever satisfy the demand.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOVING_GOALPOSTS_SYSTEM = """You are a moving the goalposts specialist. Given a debate, assess whether one party changes their criteria after evidence is presented:

Key concepts:
- Moving goalposts: changing what counts as proof after proof is given
- Raising the bar: demanding ever-higher standards of evidence
- Unfalsifiability: making a position immune to disproof
- Legitimate refinement: sometimes criteria SHOULD be updated (distinguish)
- Demand escalation: "yes but what about..." indefinitely
- Asymmetric skepticism: applying different standards to different claims
- Good faith vs bad faith: genuine learning vs evasion

When moving goalposts IS present:
- "Show me X" → [X shown] → "Well, show me Y instead"
- Changing the success criteria after they've been met
- Adding new requirements that weren't part of the original challenge
- "That doesn't count because..." with ad hoc exclusions
- Demanding increasingly specific or unlikely evidence
- Never acknowledging when a criterion has been satisfied
- Retroactively declaring the evidence insufficient

When moving goalposts is NOT present:
- New evidence reveals the original criteria were insufficient
- The refinement is acknowledged as a change in position
- Higher standards are applied consistently to all claims
- The original criteria are met and acknowledged before new ones are raised
- Legitimate follow-up questions after initial evidence is accepted
- The criteria were unclear and are being clarified, not changed
- New information genuinely changes what evidence is needed

Output JSON with: moving_goalposts_present (bool), severity (none/mild/moderate/severe), original_criterion (what was originally demanded), evidence_presented (what evidence was given), new_criterion (what new demand was made), acknowledgment (was the original criterion met acknowledged), recommendation (no_moving_goalposts/mild_criterion_shift/significant_moving_goalposts/major_unfalsifiability/acknowledge_evidence_met)."""

MOVING_GOALPOSTS_PROMPT = """Detect moving the goalposts:

Debate: {debate}
Original demand: {original_demand}
Evidence given: {evidence_given}
New demand: {new_demand}
Domain: {domain}
Context: {context}

Does this change the criteria for proof after evidence is presented? Return ONLY valid JSON."""


class MovingGoalpostsService:
    """Detects moving the goalposts — changing criteria after evidence is presented."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        debate: str,
        *,
        original_demand: str = "",
        evidence_given: str = "",
        new_demand: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moving the goalposts."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOVING_GOALPOSTS_PROMPT.format(
                debate=debate,
                original_demand=original_demand or "Not specified",
                evidence_given=evidence_given or "Not specified",
                new_demand=new_demand or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOVING_GOALPOSTS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "debate": debate[:200],
            "moving_goalposts_present": data.get("moving_goalposts_present", False),
            "severity": data.get("severity", ""),
            "original_criterion": data.get("original_criterion", ""),
            "evidence_presented": data.get("evidence_presented", ""),
            "new_criterion": data.get("new_criterion", ""),
            "recommendation": data.get("recommendation", ""),
        }
