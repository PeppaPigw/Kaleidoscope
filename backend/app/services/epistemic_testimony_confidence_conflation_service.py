"""EpistemicTestimonyConfidenceConflationService — Epistemic Testimony Confidence Conflation Detection.

Detects epistemic testimony confidence conflation — treating speaker confidence
as evidence of accuracy when confidence and accuracy are poorly correlated.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TESTIMONY_CONFIDENCE_CONFLATION_SYSTEM = """You are an epistemic testimony confidence conflation specialist. Given confidence-as-evidence reasoning, assess distortion:

Key concepts:
- Epistemic confidence conflation: confidence treated as accuracy indicator
- Certainty as evidence: expressed certainty substituting for proof
- Hedging penalty: qualified statements penalized as less credible
- Overconfidence reward: overconfident speakers rewarded with belief
- Doubt as weakness: epistemic humility interpreted as incompetence
- Calibration blindness: ignoring that confidence and accuracy diverge
- Performance confidence: theatrical confidence substituting for knowledge

When epistemic confidence conflation IS present:
- Confidence treated as accuracy
- Certainty substituting for proof
- Qualified statements penalized
- Overconfidence rewarded
- Doubt interpreted as weakness
- Calibration ignored
- Theatrical confidence accepted

When no confidence conflation:
- Confidence separated from accuracy
- Certainty not treated as proof
- Qualification valued
- Calibration rewarded
- Doubt respected
- Confidence-accuracy correlation checked
- Performance distinguished from knowledge

Output JSON with: confidence_conflation_detected (bool), severity (none/mild/moderate/severe), certainty_as_evidence (what certainty substituting), hedging_penalty (what qualification penalized), overconfidence_reward (what overconfidence rewarded), calibration_blindness (what calibration ignored), recommendation (no_confidence_conflation/mild_calibration_awareness/significant_confidence_accuracy_separation/major_intensive_track_record_analysis/emergency_complete_confidence_conflation)."""

EPISTEMIC_TESTIMONY_CONFIDENCE_CONFLATION_PROMPT = """Detect epistemic testimony confidence conflation:

Certainty as evidence: {certainty_as_evidence}
Hedging penalty: {hedging_penalty}
Overconfidence reward: {overconfidence_reward}
Calibration blindness: {calibration_blindness}
Domain: {domain}
Context: {context}

Is speaker confidence being treated as evidence of accuracy? Return ONLY valid JSON."""


class EpistemicTestimonyConfidenceConflationService:
    """Detects epistemic testimony confidence conflation — confidence as accuracy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        certainty_as_evidence: str,
        *,
        hedging_penalty: str = "",
        overconfidence_reward: str = "",
        calibration_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic testimony confidence conflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TESTIMONY_CONFIDENCE_CONFLATION_PROMPT.format(
                certainty_as_evidence=certainty_as_evidence,
                hedging_penalty=hedging_penalty or "Not specified",
                overconfidence_reward=overconfidence_reward or "Not specified",
                calibration_blindness=calibration_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TESTIMONY_CONFIDENCE_CONFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "certainty_as_evidence": certainty_as_evidence[:200],
            "confidence_conflation_detected": data.get("confidence_conflation_detected", False),
            "severity": data.get("severity", ""),
            "hedging_penalty": data.get("hedging_penalty", ""),
            "overconfidence_reward": data.get("overconfidence_reward", ""),
            "calibration_blindness": data.get("calibration_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
