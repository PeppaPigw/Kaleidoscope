"""DiffusionOfResponsibilityService — Diffusion of Responsibility Detection.

Detects diffusion of responsibility — tendency for individuals
to feel less personal responsibility when part of a group.
Darley & Latané (1968). "Someone else will handle it."
The more people present, the less each person feels responsible.
Leads to inaction, poor accountability, and collective failures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DIFFUSION_SYSTEM = """You are a diffusion of responsibility specialist. Given a situation involving group action or inaction, assess whether responsibility is being diffused:

Key concepts (Darley & Latané, 1968):
- Diffusion of responsibility: less personal responsibility in groups
- Bystander effect connection: more observers = less individual action
- Social loafing connection: less effort when contribution is pooled
- Accountability gap: no single person owns the outcome
- Pluralistic ignorance: "no one else is acting, so it must be fine"
- Free rider problem: benefiting without contributing
- Tragedy of the commons: shared resources without individual ownership

When diffusion IS present:
- "Someone else will take care of it" in group settings
- No clear owner for important tasks or decisions
- Reduced effort because individual contribution isn't visible
- "That's not my job" when everyone could act
- Committee decisions where no one feels personally accountable
- Shared responsibility leading to no one taking action
- "We all agreed" used to avoid individual accountability

When shared responsibility IS appropriate:
- Tasks genuinely require collective action
- Clear roles and accountability exist within the group
- Individual contributions are tracked and visible
- The group has explicit ownership assignments
- Shared responsibility reflects genuine shared expertise

Output JSON with: diffusion_present (bool), severity (none/mild/moderate/severe), situation (what situation involves group responsibility), group_size (how many people are involved), accountability (who is specifically accountable), individual_action (what could an individual do), inaction_risk (what is at risk from inaction), ownership_clarity (how clear is task ownership), recommendation (responsibility_clear/mild_diffusion/significant_accountability_gap/major_diffusion/assign_clear_ownership)."""

DIFFUSION_PROMPT = """Detect diffusion of responsibility:

Situation: {situation}
Group: {group}
Accountability: {accountability}
Action needed: {action}
Domain: {domain}
Context: {context}

Is responsibility being diffused across the group leading to inaction? Return ONLY valid JSON."""


class DiffusionOfResponsibilityService:
    """Detects diffusion of responsibility — reduced accountability in groups."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        group: str = "",
        accountability: str = "",
        action: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect diffusion of responsibility."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DIFFUSION_PROMPT.format(
                situation=situation,
                group=group or "Not specified",
                accountability=accountability or "Not specified",
                action=action or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DIFFUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "diffusion_present": data.get("diffusion_present", False),
            "severity": data.get("severity", ""),
            "group_size": data.get("group_size", ""),
            "accountability": data.get("accountability", ""),
            "individual_action": data.get("individual_action", ""),
            "inaction_risk": data.get("inaction_risk", ""),
            "ownership_clarity": data.get("ownership_clarity", ""),
            "recommendation": data.get("recommendation", ""),
        }
