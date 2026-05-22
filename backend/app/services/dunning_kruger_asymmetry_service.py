"""DunningKrugerAsymmetryService — Dunning-Kruger Asymmetry Detection.

Detects Dunning-Kruger asymmetry — when someone's expressed
confidence is inversely correlated with their actual competence
in a specific domain. The least competent overestimate their
ability while the most competent underestimate theirs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DK_ASYMMETRY_SYSTEM = """You are a Dunning-Kruger asymmetry specialist. Given a claim or assessment, evaluate whether confidence and competence are misaligned:

Key concepts:
- Dunning-Kruger effect: incompetence prevents recognizing incompetence
- Metacognitive deficit: lacking the skill to evaluate one's own skill
- Illusory superiority: overestimating one's abilities
- Imposter syndrome: the reverse — underestimating despite competence
- Calibration: alignment between confidence and actual ability
- Domain specificity: the effect is domain-specific
- Unskilled and unaware: the double burden of incompetence

When DK asymmetry IS present:
- High confidence paired with demonstrable errors or misconceptions
- Dismissing expert consensus without relevant expertise
- "I've done my own research" on complex technical topics
- Inability to recognize the complexity of a domain
- Overconfident predictions in areas of limited experience
- Dismissing feedback from more qualified sources
- Simple explanations for genuinely complex phenomena

When DK asymmetry is NOT present:
- Confidence is calibrated to demonstrated competence
- The person acknowledges limitations of their knowledge
- Expertise is relevant to the domain of the claim
- Confidence is based on track record and evidence
- The person can articulate what they don't know
- Appropriate hedging and uncertainty acknowledgment
- Willingness to update based on new information

Output JSON with: dk_asymmetry_present (bool), severity (none/mild/moderate/severe), confidence_level (how confident the person is), competence_indicators (evidence of actual competence), domain (what domain is involved), metacognition (awareness of own limitations), recommendation (no_dk_asymmetry/mild_overconfidence/significant_dk_asymmetry/major_competence_gap/seek_expert_feedback)."""

DK_ASYMMETRY_PROMPT = """Detect Dunning-Kruger asymmetry:

Assessment: {assessment}
Confidence expressed: {confidence}
Competence evidence: {competence}
Domain: {domain}
Feedback response: {feedback}
Context: {context}

Is confidence inversely correlated with actual competence here? Return ONLY valid JSON."""


class DunningKrugerAsymmetryService:
    """Detects Dunning-Kruger asymmetry — confidence-competence mismatch."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        assessment: str,
        *,
        confidence: str = "",
        competence: str = "",
        domain: str = "",
        feedback: str = "",
        context: str = "",
    ) -> dict:
        """Detect Dunning-Kruger asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DK_ASYMMETRY_PROMPT.format(
                assessment=assessment,
                confidence=confidence or "Not specified",
                competence=competence or "Not specified",
                domain=domain or "general",
                feedback=feedback or "Not specified",
                context=context or "No additional context",
            ),
            system=DK_ASYMMETRY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "assessment": assessment[:200],
            "dk_asymmetry_present": data.get("dk_asymmetry_present", False),
            "severity": data.get("severity", ""),
            "confidence_level": data.get("confidence_level", ""),
            "competence_indicators": data.get("competence_indicators", ""),
            "metacognition": data.get("metacognition", ""),
            "recommendation": data.get("recommendation", ""),
        }
