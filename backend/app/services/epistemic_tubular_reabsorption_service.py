"""EpistemicTubularReabsorptionService — Epistemic Tubular Reabsorption Detection.

Detects epistemic tubular reabsorption — recovering valuable ideas that
were initially filtered out, reclaiming intellectual content from waste stream.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TUBULAR_REABSORPTION_SYSTEM = """You are an epistemic tubular reabsorption specialist. Given an intellectual recovery system, assess whether valuable ideas are being reclaimed from waste:

Key concepts:
- Epistemic tubular reabsorption: recovering valuable ideas from waste stream
- Active transport: energy-intensive recovery of specific ideas
- Passive reabsorption: ideas flowing back along concentration gradient
- Threshold: level above which ideas are not recovered
- Saturation: transport maximum reached
- Glucose reabsorption: recovering essential intellectual nutrients
- Selective recovery: choosing which filtered ideas to reclaim

When epistemic tubular reabsorption IS present:
- Valuable ideas being recovered from waste stream
- Energy-intensive recovery of specific ideas
- Ideas flowing back along natural gradients
- Threshold levels determining what gets recovered
- Transport systems reaching maximum capacity
- Essential intellectual nutrients being reclaimed
- Selective recovery choosing what to save

When no reabsorption is present:
- No recovery from waste stream
- No active transport
- No passive reabsorption
- No threshold levels
- No saturation concerns
- No nutrient reclamation
- No selective recovery

Output JSON with: tubular_reabsorption_present (bool), severity (none/mild/moderate/severe), active_transport (what energy-intensive recovery), passive_reabsorption (what gradient-driven return), threshold (what recovery limit), saturation (what maximum capacity), recommendation (no_reabsorption/mild_reabsorption/significant_tubular_reabsorption/major_idea_recovery/optimize_reabsorption_selectivity)."""

EPISTEMIC_TUBULAR_REABSORPTION_PROMPT = """Detect epistemic tubular reabsorption:

Active transport: {active_transport}
Passive reabsorption: {passive_reabsorption}
Threshold: {threshold}
Saturation: {saturation}
Domain: {domain}
Context: {context}

Are valuable ideas being recovered from the intellectual waste stream? Return ONLY valid JSON."""


class EpistemicTubularReabsorptionService:
    """Detects epistemic tubular reabsorption — recovering valuable ideas from waste."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        active_transport: str,
        *,
        passive_reabsorption: str = "",
        threshold: str = "",
        saturation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tubular reabsorption."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TUBULAR_REABSORPTION_PROMPT.format(
                active_transport=active_transport,
                passive_reabsorption=passive_reabsorption or "Not specified",
                threshold=threshold or "Not specified",
                saturation=saturation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TUBULAR_REABSORPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "active_transport": active_transport[:200],
            "tubular_reabsorption_present": data.get("tubular_reabsorption_present", False),
            "severity": data.get("severity", ""),
            "passive_reabsorption": data.get("passive_reabsorption", ""),
            "threshold": data.get("threshold", ""),
            "saturation": data.get("saturation", ""),
            "recommendation": data.get("recommendation", ""),
        }
