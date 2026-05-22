"""EpistemicIdentityCognitiveDissonanceService — Epistemic Identity Cognitive Dissonance Detection.

Detects cognitive dissonance reduction where discomfort with inconsistency
distorts belief updating.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_COGNITIVE_DISSONANCE_SYSTEM = """You are an epistemic identity cognitive dissonance specialist. Given inconsistency-management patterns, assess dissonance-driven distortion:

Key concepts:
- Cognitive dissonance reduction: discomfort with inconsistency distorts belief updating
- Dissonance reduction: beliefs or evidence are adjusted to reduce discomfort
- Belief revision avoidance: evidence is reinterpreted to avoid changing beliefs
- Effort justification: costly commitments are treated as more valid because they were costly
- Post-decision rationalization: decisions are defended after the fact

When cognitive dissonance distortion IS present:
- Discomfort drives interpretation
- Belief revision is avoided
- Effort is used as justification
- Past decisions are rationalized
- Updating reduces discomfort more than error

When no cognitive dissonance distortion:
- Inconsistency is acknowledged
- Beliefs can be revised
- Effort is not treated as evidence
- Decisions remain reviewable
- Updating tracks accuracy

Output JSON with: cognitive_dissonance_detected (bool), severity (none/mild/moderate/severe), belief_revision_avoidance (what revision is avoided), effort_justification (what effort is treated as evidence), post_decision_rationalization (what decision is rationalized), recommendation (no_cognitive_dissonance/mild_inconsistency_acknowledgment/significant_belief_revision_review/major_commitment_audit/emergency_complete_dissonance_debiasing)."""

EPISTEMIC_IDENTITY_COGNITIVE_DISSONANCE_PROMPT = """Detect epistemic identity cognitive dissonance:

Dissonance reduction: {dissonance_reduction}
Belief revision avoidance: {belief_revision_avoidance}
Effort justification: {effort_justification}
Post-decision rationalization: {post_decision_rationalization}
Domain: {domain}
Context: {context}

Is cognitive dissonance reduction distorting belief updating? Return ONLY valid JSON."""


class EpistemicIdentityCognitiveDissonanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        dissonance_reduction: str,
        *,
        belief_revision_avoidance: str = "",
        effort_justification: str = "",
        post_decision_rationalization: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_COGNITIVE_DISSONANCE_PROMPT.format(
                dissonance_reduction=dissonance_reduction,
                belief_revision_avoidance=belief_revision_avoidance or "Not specified",
                effort_justification=effort_justification or "Not specified",
                post_decision_rationalization=post_decision_rationalization or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_COGNITIVE_DISSONANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "dissonance_reduction": dissonance_reduction[:200],
            "cognitive_dissonance_detected": data.get("cognitive_dissonance_detected", False),
            "severity": data.get("severity", ""),
            "belief_revision_avoidance": data.get("belief_revision_avoidance", ""),
            "effort_justification": data.get("effort_justification", ""),
            "post_decision_rationalization": data.get("post_decision_rationalization", ""),
            "recommendation": data.get("recommendation", ""),
        }
