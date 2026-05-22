"""IllusionExplanatoryDepthService — Illusion of Explanatory Depth Detection.

Detects illusion of explanatory depth — believing you
understand something much better than you actually do.
Rozenblit & Keil (2002). People think they understand how
toilets, zippers, and political policies work until asked
to explain in detail. Overconfidence in understanding
without actual depth.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EXPLANATORY_DEPTH_SYSTEM = """You are an illusion of explanatory depth specialist. Given a claim of understanding, assess whether the person's understanding is as deep as they believe:

Key concepts (Rozenblit & Keil, 2002):
- Illusion of explanatory depth: believing understanding is deeper than it is
- Shallow understanding: knowing THAT without knowing HOW or WHY
- Explanation gap: difference between felt understanding and actual ability to explain
- Mechanistic knowledge: understanding the causal mechanisms
- Surface familiarity: confusing recognition with comprehension
- Knowledge illusion: feeling of knowing without actual knowledge
- Explanation deflation: confidence drops when asked to actually explain

When the illusion IS present:
- "I totally understand how X works" but can't explain the mechanism
- Confident opinions on complex topics without mechanistic understanding
- Familiarity with a topic mistaken for deep understanding
- Unable to answer "how exactly does that work?" questions
- Strong opinions on policies without understanding implementation details
- "It's obvious" for things that are actually complex

When understanding IS genuine:
- The person can explain the mechanism step by step
- They can identify where their understanding breaks down
- They can answer follow-up questions about details
- They acknowledge gaps in their understanding
- They can teach the concept to others effectively

Output JSON with: illusion_present (bool), severity (none/mild/moderate/severe), topic (what is claimed to be understood), claimed_depth (how deep is the claimed understanding), actual_depth (how deep does understanding appear to be), explanation_ability (can they actually explain the mechanism?), mechanistic_gaps (where does understanding break down?), confidence_level (how confident are they?), calibration (is confidence matched to actual understanding?), recommendation (understanding_genuine/mild_overestimation/significant_illusion/major_explanatory_depth_illusion/test_by_explaining)."""

EXPLANATORY_DEPTH_PROMPT = """Detect illusion of explanatory depth:

Claim: {claim}
Explanation attempt: {explanation}
Follow-up gaps: {gaps}
Confidence: {confidence}
Domain: {domain}
Context: {context}

Is the person's understanding as deep as they believe? Return ONLY valid JSON."""


class IllusionExplanatoryDepthService:
    """Detects illusion of explanatory depth — overestimating own understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        explanation: str = "",
        gaps: str = "",
        confidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect illusion of explanatory depth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EXPLANATORY_DEPTH_PROMPT.format(
                claim=claim,
                explanation=explanation or "Not specified",
                gaps=gaps or "Not specified",
                confidence=confidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EXPLANATORY_DEPTH_SYSTEM,
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
            "explanation_ability": data.get("explanation_ability", ""),
            "mechanistic_gaps": data.get("mechanistic_gaps", ""),
            "confidence_level": data.get("confidence_level", ""),
            "calibration": data.get("calibration", ""),
            "recommendation": data.get("recommendation", ""),
        }
