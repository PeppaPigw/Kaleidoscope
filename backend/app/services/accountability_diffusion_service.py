"""AccountabilityDiffusionService — Accountability Diffusion Detection.

Detects accountability diffusion — when shared responsibility
leads to no one being effectively responsible. As the number
of people involved increases, individual accountability
decreases, leading to inaction or poor outcomes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACCOUNTABILITY_DIFFUSION_SYSTEM = """You are an accountability diffusion specialist. Given a situation, assess whether shared responsibility is leading to no effective responsibility:

Key concepts:
- Accountability diffusion: shared responsibility = no responsibility
- Bystander effect: more people = less individual action
- Diffusion of responsibility: "someone else will handle it"
- Social loafing: reduced effort in groups
- Free rider problem: benefiting without contributing
- Tragedy of the commons: shared resources, individual incentives
- Accountability gap: space between collective and individual responsibility

When accountability diffusion IS present:
- Multiple parties responsible but no one acting
- "That's not my job" despite collective ownership
- Shared responsibility leading to inaction
- No clear individual accountability for outcomes
- Everyone assumes someone else will handle it
- Group ownership without individual assignment
- Outcomes falling through cracks between responsibilities

When accountability diffusion is NOT present:
- Clear individual accountability despite shared goals
- Specific people assigned to specific outcomes
- Collective responsibility supplemented by individual ownership
- Mechanisms to prevent diffusion (RACI, DRI, etc.)
- Individual contributions visible and tracked
- Accountability maintained as group size increases
- Clear escalation paths when things fall through

Output JSON with: diffusion_present (bool), severity (none/mild/moderate/severe), responsibility_structure (how responsibility is shared), accountability_gap (where no one is responsible), group_size (how many share responsibility), mechanism_missing (what accountability mechanism is absent), recommendation (no_diffusion/mild_ambiguity/significant_diffusion/major_accountability_gap/assign_individual_ownership)."""

ACCOUNTABILITY_DIFFUSION_PROMPT = """Detect accountability diffusion:

Situation: {situation}
Responsibility structure: {structure}
Outcome: {outcome}
Group size: {group_size}
Domain: {domain}
Context: {context}

Is shared responsibility leading to no effective responsibility? Return ONLY valid JSON."""


class AccountabilityDiffusionService:
    """Detects accountability diffusion — shared responsibility becoming none."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        structure: str = "",
        outcome: str = "",
        group_size: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect accountability diffusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACCOUNTABILITY_DIFFUSION_PROMPT.format(
                situation=situation,
                structure=structure or "Not specified",
                outcome=outcome or "Not specified",
                group_size=group_size or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACCOUNTABILITY_DIFFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "diffusion_present": data.get("diffusion_present", False),
            "severity": data.get("severity", ""),
            "accountability_gap": data.get("accountability_gap", ""),
            "group_size": data.get("group_size", ""),
            "mechanism_missing": data.get("mechanism_missing", ""),
            "recommendation": data.get("recommendation", ""),
        }
