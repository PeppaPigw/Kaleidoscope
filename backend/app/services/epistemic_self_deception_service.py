"""EpistemicSelfDeceptionService — Epistemic Self-Deception Detection.

Detects epistemic self-deception — actively deceiving oneself about
what one knows or believes.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SELF_DECEPTION_SYSTEM = """You are an epistemic self-deception specialist. Given actively deceiving oneself, assess self-deception:

Key concepts:
- Epistemic self-deception: actively deceiving oneself about knowledge
- Motivated ignorance: choosing not to know what one suspects
- Belief maintenance: actively maintaining beliefs against evidence
- Evidence suppression: suppressing awareness of contradicting evidence
- Narrative protection: protecting preferred story from facts
- Cognitive compartmentalization: keeping contradictions separate
- Willful self-blindness: choosing not to see what's visible

When epistemic self-deception IS present:
- Actively deceiving oneself
- Choosing not to know what suspected
- Maintaining beliefs against evidence
- Suppressing contradicting evidence
- Protecting story from facts
- Keeping contradictions separate
- Choosing not to see visible

When no self-deception:
- Honest with oneself
- Acknowledging suspicions
- Updating beliefs with evidence
- Facing contradicting evidence
- Letting facts shape story
- Integrating contradictions
- Seeing what's visible

Output JSON with: self_deception_detected (bool), severity (none/mild/moderate/severe), motivated_ignorance (what choosing not to know), belief_maintenance (what maintaining against evidence), evidence_suppression (what suppressing awareness of), narrative_protection (what protecting from facts), recommendation (no_self_deception/mild_honesty_practice/significant_self_truth_work/major_intensive_deception_dismantling/emergency_complete_self_deception)."""

EPISTEMIC_SELF_DECEPTION_PROMPT = """Detect epistemic self-deception:

Motivated ignorance: {motivated_ignorance}
Belief maintenance: {belief_maintenance}
Evidence suppression: {evidence_suppression}
Narrative protection: {narrative_protection}
Domain: {domain}
Context: {context}

Is there actively deceiving oneself about what one knows or believes? Return ONLY valid JSON."""


class EpistemicSelfDeceptionService:
    """Detects epistemic self-deception — actively deceiving oneself."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        motivated_ignorance: str,
        *,
        belief_maintenance: str = "",
        evidence_suppression: str = "",
        narrative_protection: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic self-deception."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SELF_DECEPTION_PROMPT.format(
                motivated_ignorance=motivated_ignorance,
                belief_maintenance=belief_maintenance or "Not specified",
                evidence_suppression=evidence_suppression or "Not specified",
                narrative_protection=narrative_protection or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SELF_DECEPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "motivated_ignorance": motivated_ignorance[:200],
            "self_deception_detected": data.get("self_deception_detected", False),
            "severity": data.get("severity", ""),
            "belief_maintenance": data.get("belief_maintenance", ""),
            "evidence_suppression": data.get("evidence_suppression", ""),
            "narrative_protection": data.get("narrative_protection", ""),
            "recommendation": data.get("recommendation", ""),
        }
