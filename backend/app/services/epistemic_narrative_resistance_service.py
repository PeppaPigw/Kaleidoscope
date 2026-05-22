"""EpistemicNarrativeResistanceService — Epistemic Narrative Resistance Detection.

Detects epistemic narrative resistance — resisting updating one's narrative
when evidence contradicts it.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_NARRATIVE_RESISTANCE_SYSTEM = """You are an epistemic narrative resistance specialist. Given resisting narrative update, assess narrative resistance:

Key concepts:
- Epistemic narrative resistance: resisting updating narrative when evidence contradicts
- Story preservation: preserving story despite contradicting evidence
- Evidence dismissal: dismissing evidence that threatens narrative
- Narrative rigidity: rigid narrative resistant to change
- Counter-evidence minimization: minimizing evidence against narrative
- Plot armor: giving narrative plot armor against reality
- Revision refusal: refusing to revise narrative

When epistemic narrative resistance IS present:
- Resisting narrative update
- Preserving story despite evidence
- Dismissing threatening evidence
- Rigid narrative
- Minimizing counter-evidence
- Narrative has plot armor
- Refusing revision

When no narrative resistance:
- Updating narrative with evidence
- Revising story with evidence
- Accepting threatening evidence
- Flexible narrative
- Weighing counter-evidence fairly
- Narrative responsive to reality
- Willing to revise

Output JSON with: narrative_resistance_detected (bool), severity (none/mild/moderate/severe), story_preservation (what story preserved despite evidence), evidence_dismissal (what evidence dismissed), narrative_rigidity (what narrative rigid about), revision_refusal (what refusing to revise), recommendation (no_narrative_resistance/mild_openness_practice/significant_revision_willingness/major_intensive_narrative_flexibility/emergency_complete_narrative_resistance)."""

EPISTEMIC_NARRATIVE_RESISTANCE_PROMPT = """Detect epistemic narrative resistance:

Story preservation: {story_preservation}
Evidence dismissal: {evidence_dismissal}
Narrative rigidity: {narrative_rigidity}
Revision refusal: {revision_refusal}
Domain: {domain}
Context: {context}

Is there resisting updating one's narrative when evidence contradicts it? Return ONLY valid JSON."""


class EpistemicNarrativeResistanceService:
    """Detects epistemic narrative resistance — resisting narrative update."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        story_preservation: str,
        *,
        evidence_dismissal: str = "",
        narrative_rigidity: str = "",
        revision_refusal: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic narrative resistance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_NARRATIVE_RESISTANCE_PROMPT.format(
                story_preservation=story_preservation,
                evidence_dismissal=evidence_dismissal or "Not specified",
                narrative_rigidity=narrative_rigidity or "Not specified",
                revision_refusal=revision_refusal or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_NARRATIVE_RESISTANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "story_preservation": story_preservation[:200],
            "narrative_resistance_detected": data.get("narrative_resistance_detected", False),
            "severity": data.get("severity", ""),
            "evidence_dismissal": data.get("evidence_dismissal", ""),
            "narrative_rigidity": data.get("narrative_rigidity", ""),
            "revision_refusal": data.get("revision_refusal", ""),
            "recommendation": data.get("recommendation", ""),
        }
