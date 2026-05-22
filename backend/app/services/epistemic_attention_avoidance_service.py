"""EpistemicAttentionAvoidanceService — Epistemic Attention Avoidance Detection.

Detects epistemic attention avoidance — systematically avoiding attending
to important but uncomfortable information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ATTENTION_AVOIDANCE_SYSTEM = """You are an epistemic attention avoidance specialist. Given systematically avoiding uncomfortable info, assess attention avoidance:

Key concepts:
- Epistemic attention avoidance: systematically avoiding uncomfortable information
- Uncomfortable truth avoidance: avoiding information that is uncomfortable
- Selective inattention: selectively not attending to certain information
- Willful blindness: choosing not to see what is there
- Discomfort-driven avoidance: avoiding topics because they cause discomfort
- Inconvenient fact dodging: dodging facts that are inconvenient
- Emotional avoidance: avoiding information that triggers negative emotions

When epistemic attention avoidance IS present:
- Systematically avoiding uncomfortable info
- Avoiding uncomfortable truths
- Selectively not attending
- Choosing not to see
- Avoiding because of discomfort
- Dodging inconvenient facts
- Avoiding emotionally triggering info

When no attention avoidance:
- Attending to all relevant info
- Facing uncomfortable truths
- Attending comprehensively
- Seeing what is there
- Engaging despite discomfort
- Facing inconvenient facts
- Processing emotional information

Output JSON with: attention_avoidance_detected (bool), severity (none/mild/moderate/severe), uncomfortable_truth_avoidance (what uncomfortable truths avoiding), selective_inattention (what selectively not attending to), willful_blindness (what choosing not to see), discomfort_driven_avoidance (what avoiding because of discomfort), recommendation (no_attention_avoidance/mild_facing_practice/significant_engagement_building/major_intensive_avoidance_interruption/emergency_complete_attention_avoidance)."""

EPISTEMIC_ATTENTION_AVOIDANCE_PROMPT = """Detect epistemic attention avoidance:

Uncomfortable truth avoidance: {uncomfortable_truth_avoidance}
Selective inattention: {selective_inattention}
Willful blindness: {willful_blindness}
Discomfort driven avoidance: {discomfort_driven_avoidance}
Domain: {domain}
Context: {context}

Is there systematically avoiding attending to important but uncomfortable information? Return ONLY valid JSON."""


class EpistemicAttentionAvoidanceService:
    """Detects epistemic attention avoidance — avoiding uncomfortable information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        uncomfortable_truth_avoidance: str,
        *,
        selective_inattention: str = "",
        willful_blindness: str = "",
        discomfort_driven_avoidance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic attention avoidance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ATTENTION_AVOIDANCE_PROMPT.format(
                uncomfortable_truth_avoidance=uncomfortable_truth_avoidance,
                selective_inattention=selective_inattention or "Not specified",
                willful_blindness=willful_blindness or "Not specified",
                discomfort_driven_avoidance=discomfort_driven_avoidance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ATTENTION_AVOIDANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "uncomfortable_truth_avoidance": uncomfortable_truth_avoidance[:200],
            "attention_avoidance_detected": data.get("attention_avoidance_detected", False),
            "severity": data.get("severity", ""),
            "selective_inattention": data.get("selective_inattention", ""),
            "willful_blindness": data.get("willful_blindness", ""),
            "discomfort_driven_avoidance": data.get("discomfort_driven_avoidance", ""),
            "recommendation": data.get("recommendation", ""),
        }
