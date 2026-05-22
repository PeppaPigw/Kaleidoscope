"""EpistemicExpertiseDecayBlindnessService — Epistemic Expertise Decay Blindness Detection.

Detects epistemic expertise decay blindness — ignoring that expertise degrades
without active maintenance, treating past expertise as permanently valid.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_DECAY_BLINDNESS_SYSTEM = """You are an epistemic expertise decay blindness specialist. Given expertise decay blindness, assess temporal validity distortion:

Key concepts:
- Epistemic expertise decay blindness: ignoring expertise degradation over time
- Stale expertise: outdated knowledge treated as current
- Field evolution blindness: ignoring how fields change after training
- Skill atrophy: unused skills degrading without recognition
- Paradigm shift blindness: missing that field has moved past one's training
- Continuing education neglect: assuming initial training remains sufficient
- Vintage authority: treating old expertise as more authoritative

When epistemic expertise decay blindness IS present:
- Expertise degradation ignored
- Stale knowledge treated as current
- Field evolution missed
- Skill atrophy unrecognized
- Paradigm shifts missed
- Continuing education neglected
- Old expertise overvalued

When no decay blindness:
- Expertise currency assessed
- Knowledge recency checked
- Field evolution tracked
- Skill maintenance acknowledged
- Paradigm shifts recognized
- Continuing education valued
- Expertise temporally contextualized

Output JSON with: decay_blindness_detected (bool), severity (none/mild/moderate/severe), stale_expertise (what stale knowledge treated as current), field_evolution_blindness (what field evolution missed), skill_atrophy (what skills degraded), paradigm_shift_blindness (what paradigm shifts missed), recommendation (no_decay_blindness/mild_currency_checking/significant_recency_verification/major_intensive_expertise_audit/emergency_complete_decay_blindness)."""

EPISTEMIC_EXPERTISE_DECAY_BLINDNESS_PROMPT = """Detect epistemic expertise decay blindness:

Stale expertise: {stale_expertise}
Field evolution blindness: {field_evolution_blindness}
Skill atrophy: {skill_atrophy}
Paradigm shift blindness: {paradigm_shift_blindness}
Domain: {domain}
Context: {context}

Is expertise degradation being ignored, treating past expertise as permanently valid? Return ONLY valid JSON."""


class EpistemicExpertiseDecayBlindnessService:
    """Detects epistemic expertise decay blindness — temporal validity ignored."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stale_expertise: str,
        *,
        field_evolution_blindness: str = "",
        skill_atrophy: str = "",
        paradigm_shift_blindness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise decay blindness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_DECAY_BLINDNESS_PROMPT.format(
                stale_expertise=stale_expertise,
                field_evolution_blindness=field_evolution_blindness or "Not specified",
                skill_atrophy=skill_atrophy or "Not specified",
                paradigm_shift_blindness=paradigm_shift_blindness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_DECAY_BLINDNESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stale_expertise": stale_expertise[:200],
            "decay_blindness_detected": data.get("decay_blindness_detected", False),
            "severity": data.get("severity", ""),
            "field_evolution_blindness": data.get("field_evolution_blindness", ""),
            "skill_atrophy": data.get("skill_atrophy", ""),
            "paradigm_shift_blindness": data.get("paradigm_shift_blindness", ""),
            "recommendation": data.get("recommendation", ""),
        }
