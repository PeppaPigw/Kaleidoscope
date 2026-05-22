"""EpistemicJointDislocationService — Epistemic Joint Dislocation Detection.

Detects epistemic joint dislocation — ideas displaced from their proper
articulation points, losing functional connection.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_JOINT_DISLOCATION_SYSTEM = """You are an epistemic joint dislocation specialist. Given intellectual articulation points, assess whether ideas have been displaced:

Key concepts:
- Epistemic joint dislocation: ideas displaced from proper articulation
- Subluxation: partial displacement maintaining some contact
- Ligament tear: connective tissue holding joint together torn
- Reduction: returning displaced ideas to proper position
- Instability: tendency to re-dislocate after reduction
- Range of motion loss: reduced flexibility after dislocation
- Habitual dislocation: repeated displacement at same joint

When epistemic joint dislocation IS present:
- Ideas displaced from proper articulation points
- Partial displacement maintaining some contact
- Connective tissue between ideas torn
- Need to return ideas to proper position
- Tendency to re-dislocate after correction
- Reduced flexibility after displacement
- Repeated displacement at same connection point

When healthy articulation is present:
- Ideas properly articulated
- Full contact at joints
- Intact connective tissue
- No reduction needed
- Stable connections
- Full range of motion
- No habitual displacement

Output JSON with: joint_dislocation_present (bool), severity (none/mild/moderate/severe), subluxation (what partial displacement), ligament_tear (what connective damage), instability (what re-dislocation tendency), range_of_motion_loss (what flexibility reduction), recommendation (healthy_articulation/mild_dislocation/significant_joint_dislocation/major_displacement/reduce_and_stabilize)."""

EPISTEMIC_JOINT_DISLOCATION_PROMPT = """Detect epistemic joint dislocation:

Subluxation: {subluxation}
Ligament tear: {ligament_tear}
Instability: {instability}
Range of motion loss: {range_of_motion_loss}
Domain: {domain}
Context: {context}

Have ideas been displaced from their proper articulation points? Return ONLY valid JSON."""


class EpistemicJointDislocationService:
    """Detects epistemic joint dislocation — ideas displaced from articulation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        subluxation: str,
        *,
        ligament_tear: str = "",
        instability: str = "",
        range_of_motion_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic joint dislocation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_JOINT_DISLOCATION_PROMPT.format(
                subluxation=subluxation,
                ligament_tear=ligament_tear or "Not specified",
                instability=instability or "Not specified",
                range_of_motion_loss=range_of_motion_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_JOINT_DISLOCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "subluxation": subluxation[:200],
            "joint_dislocation_present": data.get("joint_dislocation_present", False),
            "severity": data.get("severity", ""),
            "ligament_tear": data.get("ligament_tear", ""),
            "instability": data.get("instability", ""),
            "range_of_motion_loss": data.get("range_of_motion_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
