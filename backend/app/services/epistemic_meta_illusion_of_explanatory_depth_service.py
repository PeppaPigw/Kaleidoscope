"""EpistemicMetaIllusionOfExplanatoryDepthService — Epistemic Meta Illusion of Explanatory Depth Detection.

Detects illusion of explanatory depth — believing one understands more deeply than one does.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_META_ILLUSION_OF_EXPLANATORY_DEPTH_SYSTEM = """You are an epistemic meta illusion of explanatory depth specialist. Given shallow understanding, assess explanatory depth overclaiming:

Key concepts:
- Illusion of explanatory depth: believing understanding is deeper than it is
- Shallow understanding: surface familiarity mistaken for mechanism knowledge
- Mechanism ignorance: inability to explain how the system actually works
- Explanation confidence gap: confidence exceeding explanatory ability
- Complexity underappreciation: missing the depth and dependencies of the subject

When illusion of explanatory depth IS present:
- Surface familiarity is mistaken for depth
- Mechanisms cannot be explained
- Confidence exceeds explanatory performance
- Complexity is underappreciated
- Understanding collapses under probing

When no explanatory depth illusion:
- Understanding limits are explicit
- Mechanisms can be explained or uncertainty is acknowledged
- Confidence tracks explanatory ability
- Complexity is recognized
- Probing improves rather than collapses the explanation

Output JSON with: explanatory_depth_illusion_detected (bool), severity (none/mild/moderate/severe), mechanism_ignorance (what mechanisms are unknown), explanation_confidence_gap (where confidence exceeds explanation), complexity_underappreciation (what complexity is missed), recommendation (no_explanatory_depth_illusion/mild_mechanism_probe/significant_explanation_audit/major_depth_recalibration/emergency_complete_explanation_rebuild)."""

EPISTEMIC_META_ILLUSION_OF_EXPLANATORY_DEPTH_PROMPT = """Detect epistemic meta illusion of explanatory depth:

Shallow understanding: {shallow_understanding}
Mechanism ignorance: {mechanism_ignorance}
Explanation confidence gap: {explanation_confidence_gap}
Complexity underappreciation: {complexity_underappreciation}
Domain: {domain}
Context: {context}

Is shallow understanding being mistaken for deep understanding? Return ONLY valid JSON."""


class EpistemicMetaIllusionOfExplanatoryDepthService:
    """Detects illusion of explanatory depth — overstated depth of understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        shallow_understanding: str,
        *,
        mechanism_ignorance: str = "",
        explanation_confidence_gap: str = "",
        complexity_underappreciation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic meta illusion of explanatory depth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_META_ILLUSION_OF_EXPLANATORY_DEPTH_PROMPT.format(
                shallow_understanding=shallow_understanding,
                mechanism_ignorance=mechanism_ignorance or "Not specified",
                explanation_confidence_gap=explanation_confidence_gap or "Not specified",
                complexity_underappreciation=complexity_underappreciation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_META_ILLUSION_OF_EXPLANATORY_DEPTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "shallow_understanding": shallow_understanding[:200],
            "explanatory_depth_illusion_detected": data.get("explanatory_depth_illusion_detected", False),
            "severity": data.get("severity", ""),
            "mechanism_ignorance": data.get("mechanism_ignorance", ""),
            "explanation_confidence_gap": data.get("explanation_confidence_gap", ""),
            "complexity_underappreciation": data.get("complexity_underappreciation", ""),
            "recommendation": data.get("recommendation", ""),
        }
