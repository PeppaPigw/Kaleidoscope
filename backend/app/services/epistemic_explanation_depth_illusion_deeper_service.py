"""EpistemicExplanationDepthIllusionDeeperService — Epistemic Explanation Depth Illusion Detection.

Detects epistemic explanation depth illusion — illusion of understanding
deeper than actual comprehension, mistaking familiarity for understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPLANATION_DEPTH_ILLUSION_DEEPER_SYSTEM = """You are an epistemic explanation depth illusion specialist. Given illusory depth of understanding, assess explanation depth illusion:

Key concepts:
- Epistemic explanation depth illusion: thinking you understand more deeply than you do
- Familiarity-understanding confusion: confusing familiarity with understanding
- Surface fluency: surface-level fluency mistaken for deep comprehension
- Mechanism ignorance: unable to explain mechanism despite feeling of understanding
- Explanation satisfaction: satisfied with explanation before understanding achieved
- Knowledge illusion: illusion of knowledge beyond actual knowledge
- Shallow processing: processing at shallow level while feeling deep

When epistemic explanation depth illusion IS present:
- Understanding shallower than believed
- Familiarity confused with understanding
- Surface fluency mistaken for depth
- Mechanisms unknown despite confidence
- Premature satisfaction with explanation
- Knowledge illusory
- Processing shallow

When no explanation depth illusion:
- Understanding depth accurately assessed
- Familiarity distinguished from understanding
- Fluency not mistaken for depth
- Mechanisms actually understood
- Satisfaction calibrated to understanding
- Knowledge genuine
- Processing appropriately deep

Output JSON with: explanation_depth_illusion_detected (bool), severity (none/mild/moderate/severe), familiarity_confusion (what familiarity confused), surface_fluency (what surface fluency mistaken), mechanism_ignorance (what mechanisms unknown), knowledge_illusion (what knowledge illusory), recommendation (no_depth_illusion/mild_depth_checking/significant_mechanism_testing/major_intensive_understanding_verification/emergency_complete_depth_illusion)."""

EPISTEMIC_EXPLANATION_DEPTH_ILLUSION_DEEPER_PROMPT = """Detect epistemic explanation depth illusion:

Familiarity confusion: {familiarity_confusion}
Surface fluency: {surface_fluency}
Mechanism ignorance: {mechanism_ignorance}
Knowledge illusion: {knowledge_illusion}
Domain: {domain}
Context: {context}

Is understanding believed to be deeper than it actually is? Return ONLY valid JSON."""


class EpistemicExplanationDepthIllusionDeeperService:
    """Detects epistemic explanation depth illusion — shallow as deep."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        familiarity_confusion: str,
        *,
        surface_fluency: str = "",
        mechanism_ignorance: str = "",
        knowledge_illusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic explanation depth illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPLANATION_DEPTH_ILLUSION_DEEPER_PROMPT.format(
                familiarity_confusion=familiarity_confusion,
                surface_fluency=surface_fluency or "Not specified",
                mechanism_ignorance=mechanism_ignorance or "Not specified",
                knowledge_illusion=knowledge_illusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPLANATION_DEPTH_ILLUSION_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "familiarity_confusion": familiarity_confusion[:200],
            "explanation_depth_illusion_detected": data.get("explanation_depth_illusion_detected", False),
            "severity": data.get("severity", ""),
            "surface_fluency": data.get("surface_fluency", ""),
            "mechanism_ignorance": data.get("mechanism_ignorance", ""),
            "knowledge_illusion": data.get("knowledge_illusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
