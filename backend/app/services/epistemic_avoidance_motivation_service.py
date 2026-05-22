"""EpistemicAvoidanceMotivationService — Epistemic Avoidance Motivation Detection.

Detects epistemic avoidance motivation — motivated to avoid knowing
uncomfortable truths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AVOIDANCE_MOTIVATION_SYSTEM = """You are an epistemic avoidance motivation specialist. Given motivation to avoid knowing, assess avoidance motivation:

Key concepts:
- Epistemic avoidance motivation: motivated to avoid uncomfortable truths
- Willful ignorance: choosing not to know to avoid discomfort
- Information avoidance: actively avoiding information that might disturb
- Comfort preservation: protecting comfort over seeking truth
- Ostrich strategy: burying head to avoid threatening knowledge
- Preemptive denial: denying before even encountering evidence
- Knowledge phobia: fear of what knowing might require

When epistemic avoidance motivation IS present:
- Motivated to avoid uncomfortable truths
- Choosing not to know
- Actively avoiding disturbing information
- Protecting comfort over truth
- Burying head in sand
- Denying before encountering
- Fearing what knowing requires

When no avoidance motivation:
- Seeking truth regardless of comfort
- Choosing to know
- Welcoming all information
- Truth over comfort
- Facing reality
- Open to evidence
- Accepting what knowing requires

Output JSON with: avoidance_motivation_detected (bool), severity (none/mild/moderate/severe), willful_ignorance (what choosing not to know), information_avoidance (what actively avoiding), comfort_preservation (what protecting comfort about), knowledge_phobia (what fearing knowing about), recommendation (no_avoidance_motivation/mild_courage_practice/significant_truth_seeking_recovery/major_intensive_avoidance_work/emergency_complete_truth_avoidance)."""

EPISTEMIC_AVOIDANCE_MOTIVATION_PROMPT = """Detect epistemic avoidance motivation:

Willful ignorance: {willful_ignorance}
Information avoidance: {information_avoidance}
Comfort preservation: {comfort_preservation}
Knowledge phobia: {knowledge_phobia}
Domain: {domain}
Context: {context}

Is there motivation to avoid knowing uncomfortable truths? Return ONLY valid JSON."""


class EpistemicAvoidanceMotivationService:
    """Detects epistemic avoidance motivation — motivated to avoid uncomfortable truths."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        willful_ignorance: str,
        *,
        information_avoidance: str = "",
        comfort_preservation: str = "",
        knowledge_phobia: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic avoidance motivation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AVOIDANCE_MOTIVATION_PROMPT.format(
                willful_ignorance=willful_ignorance,
                information_avoidance=information_avoidance or "Not specified",
                comfort_preservation=comfort_preservation or "Not specified",
                knowledge_phobia=knowledge_phobia or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AVOIDANCE_MOTIVATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "willful_ignorance": willful_ignorance[:200],
            "avoidance_motivation_detected": data.get("avoidance_motivation_detected", False),
            "severity": data.get("severity", ""),
            "information_avoidance": data.get("information_avoidance", ""),
            "comfort_preservation": data.get("comfort_preservation", ""),
            "knowledge_phobia": data.get("knowledge_phobia", ""),
            "recommendation": data.get("recommendation", ""),
        }
