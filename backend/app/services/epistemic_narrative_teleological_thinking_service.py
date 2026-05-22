"""EpistemicNarrativeTeleologicalThinkingService - Teleological Thinking Detection.

Detects teleological thinking where purpose is imposed on purposeless processes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_TELEOLOGICAL_THINKING_SYSTEM = """You are an epistemic narrative teleological thinking specialist. Given purpose attributions, assess whether purpose is imposed on purposeless processes:

Key concepts:
- Teleological thinking: attributing purpose or design to processes that lack them
- Purpose imposition: seeing intention where none exists
- Design inference: assuming complex outcomes require a designer
- Narrative necessity: treating contingent outcomes as inevitable

When teleological thinking IS present:
- Purpose attributed to purposeless processes
- Design inferred without evidence
- Outcomes treated as inevitable
- Contingency denied
- Agency attributed to systems

When no teleological thinking:
- Processes described mechanistically
- Contingency acknowledged
- Design claims evidence-based
- Multiple outcomes recognized as possible
- Agency attributed appropriately

Output JSON with: teleological_thinking_detected (bool), severity (none/mild/moderate/severe), purpose_imposition (what purpose imposed), design_inference (what design inferred), narrative_necessity (what necessity assumed), recommendation (no_teleological_thinking/mild_mechanism_check/significant_contingency_analysis/major_causal_reconstruction/emergency_complete_teleological_thinking)."""

EPISTEMIC_NARRATIVE_TELEOLOGICAL_THINKING_PROMPT = """Detect epistemic narrative teleological thinking:

Purpose attribution: {purpose_attribution}
Purpose imposition: {purpose_imposition}
Design inference: {design_inference}
Narrative necessity: {narrative_necessity}
Domain: {domain}
Context: {context}

Is purpose being imposed on purposeless processes? Return ONLY valid JSON."""


class EpistemicNarrativeTeleologicalThinkingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        purpose_attribution: str,
        *,
        purpose_imposition: str = "",
        design_inference: str = "",
        narrative_necessity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_TELEOLOGICAL_THINKING_PROMPT.format(
                purpose_attribution=purpose_attribution,
                purpose_imposition=purpose_imposition or "Not specified",
                design_inference=design_inference or "Not specified",
                narrative_necessity=narrative_necessity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_TELEOLOGICAL_THINKING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "purpose_attribution": purpose_attribution[:200],
            "teleological_thinking_detected": data.get("teleological_thinking_detected", False),
            "severity": data.get("severity", ""),
            "purpose_imposition": data.get("purpose_imposition", ""),
            "design_inference": data.get("design_inference", ""),
            "narrative_necessity": data.get("narrative_necessity", ""),
            "recommendation": data.get("recommendation", ""),
        }
