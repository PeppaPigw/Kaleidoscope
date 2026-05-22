"""EpistemicFeedbackDistortionService — Epistemic Feedback Distortion Detection.

Detects epistemic feedback distortion — distorting feedback received
to fit existing beliefs rather than updating beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FEEDBACK_DISTORTION_SYSTEM = """You are an epistemic feedback distortion specialist. Given distortion of feedback to fit beliefs, assess feedback distortion:

Key concepts:
- Epistemic feedback distortion: distorting feedback to fit existing beliefs
- Reinterpretation: reinterpreting negative feedback as positive
- Selective hearing: hearing only parts of feedback that confirm
- Minimization: minimizing the significance of disconfirming feedback
- Externalization: attributing negative feedback to external factors
- Rationalization: rationalizing away disconfirming feedback
- Meaning distortion: distorting the meaning of feedback received

When epistemic feedback distortion IS present:
- Feedback distorted to fit beliefs
- Negative reinterpreted as positive
- Selective hearing operating
- Disconfirmation minimized
- Negative externalized
- Disconfirmation rationalized
- Meaning distorted

When no feedback distortion:
- Feedback taken at face value
- Negative heard as negative
- All feedback heard
- Disconfirmation weighted appropriately
- Feedback attributed accurately
- Disconfirmation processed honestly
- Meaning preserved

Output JSON with: feedback_distortion_detected (bool), severity (none/mild/moderate/severe), reinterpretation (what reinterpreted), selective_hearing (what selectively heard), minimization (what minimized), externalization (what externalized), recommendation (no_feedback_distortion/mild_honest_reception/significant_distortion_awareness/major_intensive_feedback_fidelity/emergency_complete_feedback_distortion)."""

EPISTEMIC_FEEDBACK_DISTORTION_PROMPT = """Detect epistemic feedback distortion:

Reinterpretation: {reinterpretation}
Selective hearing: {selective_hearing}
Minimization: {minimization}
Externalization: {externalization}
Domain: {domain}
Context: {context}

Is feedback being distorted to fit existing beliefs? Return ONLY valid JSON."""


class EpistemicFeedbackDistortionService:
    """Detects epistemic feedback distortion — warping feedback to fit beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reinterpretation: str,
        *,
        selective_hearing: str = "",
        minimization: str = "",
        externalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic feedback distortion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FEEDBACK_DISTORTION_PROMPT.format(
                reinterpretation=reinterpretation,
                selective_hearing=selective_hearing or "Not specified",
                minimization=minimization or "Not specified",
                externalization=externalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FEEDBACK_DISTORTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reinterpretation": reinterpretation[:200],
            "feedback_distortion_detected": data.get("feedback_distortion_detected", False),
            "severity": data.get("severity", ""),
            "selective_hearing": data.get("selective_hearing", ""),
            "minimization": data.get("minimization", ""),
            "externalization": data.get("externalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
