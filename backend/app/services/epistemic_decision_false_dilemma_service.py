"""EpistemicDecisionFalseDilemmaService - False Dilemma Detection.

Detects false dilemma where options are artificially restricted to two choices.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DECISION_FALSE_DILEMMA_SYSTEM = """You are an epistemic decision false dilemma specialist. Given choice framing, assess whether options are artificially restricted:

Key concepts:
- False dilemma: presenting only two options when more exist
- Option suppression: hiding viable alternatives
- Binary framing: forcing complex situations into either/or
- Middle ground erasure: eliminating compromise or hybrid solutions

When false dilemma IS present:
- Only two options presented
- Viable alternatives suppressed
- Situation forced into binary
- Middle ground erased
- Complexity denied

When no false dilemma:
- Options appropriately enumerated
- Alternatives considered
- Complexity acknowledged
- Hybrid solutions explored
- Binary framing justified

Output JSON with: false_dilemma_detected (bool), severity (none/mild/moderate/severe), option_suppression (what options suppressed), binary_framing (what binary framing), middle_ground_erasure (what middle ground erased), recommendation (no_false_dilemma/mild_option_expansion/significant_alternative_analysis/major_choice_reconstruction/emergency_complete_false_dilemma)."""

EPISTEMIC_DECISION_FALSE_DILEMMA_PROMPT = """Detect epistemic decision false dilemma:

Choice framing: {choice_framing}
Option suppression: {option_suppression}
Binary framing: {binary_framing}
Middle ground erasure: {middle_ground_erasure}
Domain: {domain}
Context: {context}

Are options being artificially restricted? Return ONLY valid JSON."""


class EpistemicDecisionFalseDilemmaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        choice_framing: str,
        *,
        option_suppression: str = "",
        binary_framing: str = "",
        middle_ground_erasure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DECISION_FALSE_DILEMMA_PROMPT.format(
                choice_framing=choice_framing,
                option_suppression=option_suppression or "Not specified",
                binary_framing=binary_framing or "Not specified",
                middle_ground_erasure=middle_ground_erasure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DECISION_FALSE_DILEMMA_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "choice_framing": choice_framing[:200],
            "false_dilemma_detected": data.get("false_dilemma_detected", False),
            "severity": data.get("severity", ""),
            "option_suppression": data.get("option_suppression", ""),
            "binary_framing": data.get("binary_framing", ""),
            "middle_ground_erasure": data.get("middle_ground_erasure", ""),
            "recommendation": data.get("recommendation", ""),
        }
