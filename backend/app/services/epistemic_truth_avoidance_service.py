"""EpistemicTruthAvoidanceService — Epistemic Truth Avoidance Detection.

Detects epistemic truth avoidance — actively avoiding truths that would
require uncomfortable action.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TRUTH_AVOIDANCE_SYSTEM = """You are an epistemic truth avoidance specialist. Given actively avoiding uncomfortable truths, assess truth avoidance:

Key concepts:
- Epistemic truth avoidance: avoiding truths requiring uncomfortable action
- Action-implication avoidance: avoiding truths that demand change
- Responsibility dodge: avoiding knowledge that creates obligation
- Comfort-truth tradeoff: choosing comfort over truth
- Inconvenient knowledge: avoiding knowledge with inconvenient implications
- Moral knowledge avoidance: avoiding truths with moral demands
- Consequence blindness: refusing to see consequences of knowing

When epistemic truth avoidance IS present:
- Avoiding truths requiring action
- Avoiding truths demanding change
- Avoiding knowledge creating obligation
- Choosing comfort over truth
- Avoiding inconvenient implications
- Avoiding moral demands
- Refusing to see consequences

When no truth avoidance:
- Facing truths regardless of action needed
- Accepting change demands
- Accepting obligations
- Truth over comfort
- Accepting implications
- Facing moral demands
- Seeing consequences

Output JSON with: truth_avoidance_detected (bool), severity (none/mild/moderate/severe), action_implication_avoidance (what avoiding because demands change), responsibility_dodge (what avoiding because creates obligation), comfort_truth_tradeoff (what choosing comfort over), moral_knowledge_avoidance (what avoiding moral demands of), recommendation (no_truth_avoidance/mild_courage_practice/significant_truth_facing/major_intensive_responsibility_acceptance/emergency_complete_truth_avoidance)."""

EPISTEMIC_TRUTH_AVOIDANCE_PROMPT = """Detect epistemic truth avoidance:

Action implication avoidance: {action_implication_avoidance}
Responsibility dodge: {responsibility_dodge}
Comfort truth tradeoff: {comfort_truth_tradeoff}
Moral knowledge avoidance: {moral_knowledge_avoidance}
Domain: {domain}
Context: {context}

Is there actively avoiding truths that would require uncomfortable action? Return ONLY valid JSON."""


class EpistemicTruthAvoidanceService:
    """Detects epistemic truth avoidance — avoiding truths requiring uncomfortable action."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        action_implication_avoidance: str,
        *,
        responsibility_dodge: str = "",
        comfort_truth_tradeoff: str = "",
        moral_knowledge_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic truth avoidance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TRUTH_AVOIDANCE_PROMPT.format(
                action_implication_avoidance=action_implication_avoidance,
                responsibility_dodge=responsibility_dodge or "Not specified",
                comfort_truth_tradeoff=comfort_truth_tradeoff or "Not specified",
                moral_knowledge_avoidance=moral_knowledge_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TRUTH_AVOIDANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "action_implication_avoidance": action_implication_avoidance[:200],
            "truth_avoidance_detected": data.get("truth_avoidance_detected", False),
            "severity": data.get("severity", ""),
            "responsibility_dodge": data.get("responsibility_dodge", ""),
            "comfort_truth_tradeoff": data.get("comfort_truth_tradeoff", ""),
            "moral_knowledge_avoidance": data.get("moral_knowledge_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
