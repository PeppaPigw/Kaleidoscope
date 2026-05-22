"""ExplanationDepthIllusionService — Explanation Depth Illusion Detection.

Detects the illusion of explanatory depth — when people believe
they understand something deeply but actually have only a shallow
understanding. Exposed when asked to explain mechanisms in detail.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPLANATION_DEPTH_ILLUSION_SYSTEM = """You are an explanation depth illusion specialist. Given a claimed understanding, assess whether it is genuinely deep or superficially confident:

Key concepts:
- Illusion of explanatory depth (IOED): believing you understand more than you do
- Shallow understanding: knowing THAT without knowing HOW or WHY
- Mechanism knowledge: understanding the causal chain
- Surface fluency: familiarity mistaken for comprehension
- Explanation gap: difference between claimed and actual understanding
- Knowledge illusion: confusing access to information with understanding
- Dunning-Kruger connection: not knowing what you don't know

When explanation depth illusion IS present:
- Confident claims of understanding without mechanism knowledge
- Unable to explain HOW something works when pressed
- Reliance on labels and categories instead of causal explanations
- Familiarity with a topic mistaken for deep understanding
- Circular explanations that don't add information
- Vague hand-waving where specific mechanisms should be
- Confidence drops dramatically when asked for details

When explanation depth illusion is NOT present:
- Understanding includes mechanism knowledge
- Can explain HOW and WHY, not just WHAT
- Acknowledges limits of understanding
- Specific causal chains articulated
- Confidence calibrated to actual depth of knowledge
- Can predict consequences of changes to the system
- Distinguishes between familiarity and comprehension

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), claimed_depth (how deep understanding is claimed to be), actual_depth (how deep it actually appears), mechanism_gaps (where mechanism knowledge is missing), surface_markers (signs of shallow understanding), recommendation (no_illusion/mild_overconfidence/significant_depth_gap/major_knowledge_illusion/test_with_mechanism_questions)."""

EXPLANATION_DEPTH_ILLUSION_PROMPT = """Detect explanation depth illusion:

Claim: {claim}
Explanation given: {explanation}
Mechanism detail: {mechanism}
Confidence level: {confidence}
Domain: {domain}
Context: {context}

Is the understanding genuinely deep or superficially confident? Return ONLY valid JSON."""


class ExplanationDepthIllusionService:
    """Detects illusion of explanatory depth — shallow understanding mistaken for deep."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        explanation: str = "",
        mechanism: str = "",
        confidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect explanation depth illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPLANATION_DEPTH_ILLUSION_PROMPT.format(
                claim=claim,
                explanation=explanation or "Not specified",
                mechanism=mechanism or "Not specified",
                confidence=confidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPLANATION_DEPTH_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "illusion_present": data.get("illusion_present", False),
            "severity": data.get("severity", ""),
            "claimed_depth": data.get("claimed_depth", ""),
            "actual_depth": data.get("actual_depth", ""),
            "mechanism_gaps": data.get("mechanism_gaps", ""),
            "recommendation": data.get("recommendation", ""),
        }
