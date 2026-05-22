"""EpistemicDisorganizedAttachmentService — Epistemic Disorganized Attachment Detection.

Detects epistemic disorganized attachment — chaotic approach-avoidance pattern
in intellectual relationships where the source of safety is also the source of fear.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DISORGANIZED_ATTACHMENT_SYSTEM = """You are an epistemic disorganized attachment specialist. Given chaotic approach-avoidance, assess disorganized attachment:

Key concepts:
- Epistemic disorganized attachment: chaotic approach-avoidance
- Fright without solution: intellectual authority both needed and feared
- Contradictory behavior: simultaneously seeking and fleeing
- Dissociative response: freezing when attachment activated
- Controlling strategies: attempting to manage frightening authority
- Collapse: breaking down when attachment system overwhelmed
- Incoherence: no organized strategy for intellectual relating

When epistemic disorganized attachment IS present:
- Chaotic approach-avoidance
- Authority both needed and feared
- Simultaneously seeking and fleeing
- Freezing when activated
- Attempting to manage authority
- Breaking down when overwhelmed
- No organized strategy

When no disorganized attachment:
- Coherent relating strategy
- Authority safe and helpful
- Clear approach or avoidance
- Responsive when activated
- Collaborative with authority
- Regulated under stress
- Organized strategy

Output JSON with: disorganized_attachment_detected (bool), severity (none/mild/moderate/severe), fright_without_solution (what both needing and fearing), contradictory_behavior (what simultaneously doing), dissociative_response (what freezing), collapse_pattern (what breaking down), recommendation (no_disorganized_attachment/mild_coherence_building/significant_attachment_therapy/major_intensive_trauma_work/emergency_severe_disorganization)."""

EPISTEMIC_DISORGANIZED_ATTACHMENT_PROMPT = """Detect epistemic disorganized attachment:

Fright without solution: {fright_without_solution}
Contradictory behavior: {contradictory_behavior}
Dissociative response: {dissociative_response}
Collapse pattern: {collapse_pattern}
Domain: {domain}
Context: {context}

Is there chaotic approach-avoidance in intellectual relationships? Return ONLY valid JSON."""


class EpistemicDisorganizedAttachmentService:
    """Detects epistemic disorganized attachment — chaotic approach-avoidance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fright_without_solution: str,
        *,
        contradictory_behavior: str = "",
        dissociative_response: str = "",
        collapse_pattern: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic disorganized attachment."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DISORGANIZED_ATTACHMENT_PROMPT.format(
                fright_without_solution=fright_without_solution,
                contradictory_behavior=contradictory_behavior or "Not specified",
                dissociative_response=dissociative_response or "Not specified",
                collapse_pattern=collapse_pattern or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DISORGANIZED_ATTACHMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fright_without_solution": fright_without_solution[:200],
            "disorganized_attachment_detected": data.get("disorganized_attachment_detected", False),
            "severity": data.get("severity", ""),
            "contradictory_behavior": data.get("contradictory_behavior", ""),
            "dissociative_response": data.get("dissociative_response", ""),
            "collapse_pattern": data.get("collapse_pattern", ""),
            "recommendation": data.get("recommendation", ""),
        }
