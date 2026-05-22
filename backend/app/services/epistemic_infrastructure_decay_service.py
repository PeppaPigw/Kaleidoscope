"""EpistemicInfrastructureDecayService — Epistemic Infrastructure Decay Detection.

Detects epistemic infrastructure decay — decay of institutions and
practices that support good reasoning, where the foundations of
knowledge production are eroding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFRASTRUCTURE_DECAY_SYSTEM = """You are an epistemic infrastructure decay specialist. Given an institutional or practice context, assess whether epistemic infrastructure is decaying:

Key concepts:
- Epistemic infrastructure decay: institutions supporting reasoning eroding
- Institutional erosion: knowledge institutions losing capacity
- Practice degradation: epistemic practices losing rigor
- Standards erosion: quality standards declining
- Expertise loss: expertise leaving without replacement
- Institutional memory loss: organizations forgetting how to know
- Capacity degradation: ability to produce knowledge declining

When infrastructure decay IS present:
- Institutions supporting reasoning losing capacity
- Epistemic practices losing rigor over time
- Quality standards declining without replacement
- Expertise leaving without succession
- Institutional memory of good practices fading
- Capacity to produce reliable knowledge declining
- Infrastructure maintenance neglected

When appropriate evolution is present:
- Institutions adapting to new needs
- Practices evolving to improve
- Standards updating to reflect new understanding
- Expertise transitioning to new forms
- Institutional memory actively maintained
- Capacity growing or transforming
- Infrastructure being renewed not just maintained

Output JSON with: decay_present (bool), severity (none/mild/moderate/severe), infrastructure (what infrastructure is assessed), erosion (what is eroding), impact (how knowledge production is affected), cause (what causes the decay), recommendation (healthy_evolution/mild_capacity_loss/significant_infrastructure_decay/major_institutional_erosion/invest_in_epistemic_infrastructure)."""

EPISTEMIC_INFRASTRUCTURE_DECAY_PROMPT = """Detect epistemic infrastructure decay:

Infrastructure: {infrastructure}
Current state: {state}
Historical capacity: {historical}
Trends: {trends}
Domain: {domain}
Context: {context}

Are institutions and practices that support good reasoning decaying? Return ONLY valid JSON."""


class EpistemicInfrastructureDecayService:
    """Detects epistemic infrastructure decay — institutions supporting reasoning eroding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        infrastructure: str,
        *,
        state: str = "",
        historical: str = "",
        trends: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic infrastructure decay."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFRASTRUCTURE_DECAY_PROMPT.format(
                infrastructure=infrastructure,
                state=state or "Not specified",
                historical=historical or "Not specified",
                trends=trends or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFRASTRUCTURE_DECAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "infrastructure": infrastructure[:200],
            "decay_present": data.get("decay_present", False),
            "severity": data.get("severity", ""),
            "erosion": data.get("erosion", ""),
            "impact": data.get("impact", ""),
            "cause": data.get("cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
