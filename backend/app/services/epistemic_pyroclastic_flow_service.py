"""EpistemicPyroclasticFlowService — Epistemic Pyroclastic Flow Detection.

Detects epistemic pyroclastic flows — fast-moving clouds of hot
intellectual material that destroy everything in their path.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PYROCLASTIC_FLOW_SYSTEM = """You are an epistemic pyroclastic flow specialist. Given an intellectual event, assess whether fast-moving hot material is destroying everything in its path:

Key concepts:
- Epistemic pyroclastic flow: fast-moving hot intellectual material
- Speed: moving too fast to escape or respond
- Temperature: intellectual heat that incinerates existing ideas
- Density: heavy material that cannot be deflected
- Path of destruction: everything in path destroyed
- Trigger: what eruption triggers the flow
- Aftermath: barren landscape after flow passes

When epistemic pyroclastic flow IS present:
- Fast-moving clouds of hot intellectual material
- Moving too fast for existing ideas to escape or adapt
- Intellectual heat incinerating existing frameworks
- Heavy material that cannot be deflected or redirected
- Everything in the path being destroyed
- Clear eruption event triggering the flow
- Barren intellectual landscape after flow passes

When calm intellectual environment is present:
- No fast-moving destructive intellectual forces
- Existing ideas having time to adapt
- No incinerating intellectual heat
- Forces that can be deflected or redirected
- Existing frameworks surviving intact
- No eruption events
- Intellectual landscape remaining fertile

Output JSON with: pyroclastic_flow_present (bool), severity (none/mild/moderate/severe), material (what hot material flows), speed (how fast it moves), destruction (what is destroyed in path), trigger (what eruption triggers it), recommendation (calm_environment/mild_heat/significant_flow/major_destruction/evacuate_path_or_shelter)."""

EPISTEMIC_PYROCLASTIC_FLOW_PROMPT = """Detect epistemic pyroclastic flow:

Material: {material}
Speed: {speed}
Destruction: {destruction}
Trigger: {trigger}
Domain: {domain}
Context: {context}

Is fast-moving hot intellectual material destroying everything in its path? Return ONLY valid JSON."""


class EpistemicPyroclasticFlowService:
    """Detects epistemic pyroclastic flows — fast destructive intellectual forces."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        material: str,
        *,
        speed: str = "",
        destruction: str = "",
        trigger: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic pyroclastic flow."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PYROCLASTIC_FLOW_PROMPT.format(
                material=material,
                speed=speed or "Not specified",
                destruction=destruction or "Not specified",
                trigger=trigger or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PYROCLASTIC_FLOW_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "material": material[:200],
            "pyroclastic_flow_present": data.get("pyroclastic_flow_present", False),
            "severity": data.get("severity", ""),
            "speed": data.get("speed", ""),
            "destruction": data.get("destruction", ""),
            "trigger": data.get("trigger", ""),
            "recommendation": data.get("recommendation", ""),
        }
