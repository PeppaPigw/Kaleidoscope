"""BystanderEffectService — Bystander Effect Detection.

Detects bystander effect — the more people who witness an
emergency or problem, the less likely any individual is to
help. Darley & Latané (1968). Kitty Genovese effect.
Each person assumes someone else will act. Leads to
collective inaction in situations requiring intervention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

BYSTANDER_SYSTEM = """You are a bystander effect specialist. Given a situation where action is needed, assess whether the presence of others is inhibiting individual action:

Key concepts (Darley & Latané, 1968):
- Bystander effect: more witnesses = less individual action
- Pluralistic ignorance: "no one else is reacting, so it must be okay"
- Diffusion of responsibility: "someone else will handle it"
- Evaluation apprehension: fear of acting inappropriately in front of others
- Audience inhibition: reluctance to act when being observed
- Notice → Interpret → Responsibility → Action: intervention decision model
- Competence concern: "I might make it worse"

When bystander effect IS present:
- Multiple people aware of a problem but no one acting
- "I assumed someone else would report it"
- Waiting for others to act first before intervening
- Problems persisting despite many people being aware
- "It's not my place to say something"
- Known issues that everyone sees but no one addresses
- Collective silence about obvious problems

When inaction IS appropriate:
- Someone more qualified is already handling it
- Action would genuinely make things worse
- The situation doesn't actually require intervention
- There are legitimate reasons to defer to others
- The person has assessed and determined no action is needed

Output JSON with: bystander_effect_present (bool), severity (none/mild/moderate/severe), situation (what situation needs action), witnesses (how many people are aware), action_needed (what action should be taken), barriers (what prevents action), pluralistic_ignorance (is everyone assuming it's fine because no one acts?), intervention_cost (what is the cost of acting), recommendation (inaction_appropriate/mild_bystander/significant_collective_inaction/major_bystander_effect/designate_specific_actor)."""

BYSTANDER_PROMPT = """Detect bystander effect:

Situation: {situation}
Observers: {observers}
Action needed: {action}
Current response: {response}
Domain: {domain}
Context: {context}

Is the presence of others inhibiting individual action? Return ONLY valid JSON."""


class BystanderEffectService:
    """Detects bystander effect — presence of others inhibiting individual action."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        observers: str = "",
        action: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect bystander effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BYSTANDER_PROMPT.format(
                situation=situation,
                observers=observers or "Not specified",
                action=action or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=BYSTANDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "bystander_effect_present": data.get("bystander_effect_present", False),
            "severity": data.get("severity", ""),
            "witnesses": data.get("witnesses", ""),
            "action_needed": data.get("action_needed", ""),
            "barriers": data.get("barriers", ""),
            "pluralistic_ignorance": data.get("pluralistic_ignorance", ""),
            "intervention_cost": data.get("intervention_cost", ""),
            "recommendation": data.get("recommendation", ""),
        }
