"""EpistemicThoughtIntrusionService — Epistemic Thought Intrusion Detection.

Detects epistemic thought intrusion — unwanted intrusion of others'
thoughts/beliefs into one's own thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_THOUGHT_INTRUSION_SYSTEM = """You are an epistemic thought intrusion specialist. Given unwanted intrusion of others' thoughts, assess thought intrusion:

Key concepts:
- Epistemic thought intrusion: unwanted others' thoughts intruding
- Belief contamination: others' beliefs infiltrating without consent
- Intellectual haunting: can't stop thinking in another's framework
- Cognitive colonization: another's thinking taking over one's own
- Unwanted influence: being shaped by ideas one rejects
- Mental echo: hearing another's voice in one's own reasoning
- Framework imprisonment: trapped in another's way of thinking

When epistemic thought intrusion IS present:
- Unwanted thoughts intruding
- Beliefs infiltrating without consent
- Can't stop using another's framework
- Another's thinking taking over
- Shaped by rejected ideas
- Hearing another's voice in reasoning
- Trapped in another's framework

When no thought intrusion:
- Own thoughts dominant
- Beliefs adopted by choice
- Frameworks chosen freely
- Own thinking sovereign
- Influenced only by accepted ideas
- Own voice in reasoning
- Free to choose frameworks

Output JSON with: thought_intrusion_detected (bool), severity (none/mild/moderate/severe), belief_contamination (what infiltrating without consent), intellectual_haunting (what can't stop thinking in), cognitive_colonization (what taking over), framework_imprisonment (what trapped in), recommendation (no_thought_intrusion/mild_boundary_strengthening/significant_decolonization_work/major_intensive_sovereignty_recovery/emergency_complete_cognitive_takeover)."""

EPISTEMIC_THOUGHT_INTRUSION_PROMPT = """Detect epistemic thought intrusion:

Belief contamination: {belief_contamination}
Intellectual haunting: {intellectual_haunting}
Cognitive colonization: {cognitive_colonization}
Framework imprisonment: {framework_imprisonment}
Domain: {domain}
Context: {context}

Is there unwanted intrusion of others' thoughts into one's own thinking? Return ONLY valid JSON."""


class EpistemicThoughtIntrusionService:
    """Detects epistemic thought intrusion — unwanted intrusion of others' thoughts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief_contamination: str,
        *,
        intellectual_haunting: str = "",
        cognitive_colonization: str = "",
        framework_imprisonment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic thought intrusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_THOUGHT_INTRUSION_PROMPT.format(
                belief_contamination=belief_contamination,
                intellectual_haunting=intellectual_haunting or "Not specified",
                cognitive_colonization=cognitive_colonization or "Not specified",
                framework_imprisonment=framework_imprisonment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_THOUGHT_INTRUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief_contamination": belief_contamination[:200],
            "thought_intrusion_detected": data.get("thought_intrusion_detected", False),
            "severity": data.get("severity", ""),
            "intellectual_haunting": data.get("intellectual_haunting", ""),
            "cognitive_colonization": data.get("cognitive_colonization", ""),
            "framework_imprisonment": data.get("framework_imprisonment", ""),
            "recommendation": data.get("recommendation", ""),
        }
