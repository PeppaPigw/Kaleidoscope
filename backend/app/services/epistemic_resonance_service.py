"""EpistemicResonanceService — Epistemic Resonance Detection.

Detects epistemic resonance — ideas amplified not because of evidence
but because they match the natural frequency of existing beliefs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RESONANCE_SYSTEM = """You are an epistemic resonance specialist. Given a belief amplification pattern, assess whether ideas are amplified by matching existing beliefs:

Key concepts:
- Epistemic resonance: ideas amplified by matching existing belief frequency
- Belief matching: ideas gaining strength from matching prior beliefs
- Natural frequency: the frequency at which a belief system vibrates
- Forced resonance: external ideas matching internal frequency
- Amplitude growth: ideas growing beyond evidence through resonance
- Constructive interference: multiple resonant ideas amplifying each other
- Resonance catastrophe: amplification reaching destructive levels

When epistemic resonance IS present:
- Ideas amplified because they match existing beliefs
- Belief matching driving acceptance over evidence
- Ideas gaining strength from matching prior commitments
- External claims resonating with internal biases
- Ideas growing beyond what evidence supports through resonance
- Multiple resonant ideas amplifying each other
- Amplification reaching potentially destructive levels

When evidence-based acceptance is present:
- Ideas accepted based on evidence strength
- Prior beliefs not driving acceptance
- Ideas evaluated on their own merits
- External claims evaluated independently
- Ideas proportionate to supporting evidence
- No mutual amplification beyond evidence
- Acceptance at appropriate levels

Output JSON with: resonance_present (bool), severity (none/mild/moderate/severe), idea (what idea resonates), existing_beliefs (what beliefs it matches), amplification (how much amplification), evidence_gap (gap between evidence and acceptance), recommendation (evidence_based/mild_resonance/significant_belief_matching/major_resonance_catastrophe/evaluate_independently)."""

EPISTEMIC_RESONANCE_PROMPT = """Detect epistemic resonance:

Idea: {idea}
Existing beliefs: {existing_beliefs}
Amplification: {amplification}
Evidence gap: {evidence_gap}
Domain: {domain}
Context: {context}

Are ideas being amplified because they match existing beliefs rather than because of evidence? Return ONLY valid JSON."""


class EpistemicResonanceService:
    """Detects epistemic resonance — ideas amplified by matching existing beliefs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        idea: str,
        *,
        existing_beliefs: str = "",
        amplification: str = "",
        evidence_gap: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic resonance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RESONANCE_PROMPT.format(
                idea=idea,
                existing_beliefs=existing_beliefs or "Not specified",
                amplification=amplification or "Not specified",
                evidence_gap=evidence_gap or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RESONANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "idea": idea[:200],
            "resonance_present": data.get("resonance_present", False),
            "severity": data.get("severity", ""),
            "existing_beliefs": data.get("existing_beliefs", ""),
            "amplification": data.get("amplification", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
