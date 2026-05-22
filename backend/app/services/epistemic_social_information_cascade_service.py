"""EpistemicSocialInformationCascadeService - Information Cascade Detection.

Detects information cascades where sequential decisions follow predecessors regardless of private info.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_INFORMATION_CASCADE_SYSTEM = """You are an epistemic social information cascade specialist. Given sequential decisions, assess whether cascades override private information:

Key concepts:
- Information cascade: rational ignoring of private information in favor of observed behavior
- Herding behavior: following predecessors regardless of own evidence
- Private information suppression: discounting own knowledge due to social proof
- Fragile consensus: apparent agreement that collapses with new public information

When information cascade IS present:
- Sequential decisions follow predecessors
- Private information suppressed
- Herding behavior evident
- Consensus fragile and uninformed
- Individual judgment abandoned

When no information cascade:
- Decisions reflect private information
- Individual judgment maintained
- Social proof weighed appropriately
- Consensus robust and informed
- Independent assessment preserved

Output JSON with: information_cascade_detected (bool), severity (none/mild/moderate/severe), herding_behavior (what herding), private_info_suppression (what info suppressed), fragile_consensus (what fragile consensus), recommendation (no_information_cascade/mild_independence_check/significant_private_info_surfacing/major_decision_reconstruction/emergency_complete_information_cascade)."""

EPISTEMIC_SOCIAL_INFORMATION_CASCADE_PROMPT = """Detect epistemic social information cascade:

Sequential decision: {sequential_decision}
Herding behavior: {herding_behavior}
Private info suppression: {private_info_suppression}
Fragile consensus: {fragile_consensus}
Domain: {domain}
Context: {context}

Are sequential decisions following predecessors regardless of private information? Return ONLY valid JSON."""


class EpistemicSocialInformationCascadeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        sequential_decision: str,
        *,
        herding_behavior: str = "",
        private_info_suppression: str = "",
        fragile_consensus: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_INFORMATION_CASCADE_PROMPT.format(
                sequential_decision=sequential_decision,
                herding_behavior=herding_behavior or "Not specified",
                private_info_suppression=private_info_suppression or "Not specified",
                fragile_consensus=fragile_consensus or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_INFORMATION_CASCADE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "sequential_decision": sequential_decision[:200],
            "information_cascade_detected": data.get("information_cascade_detected", False),
            "severity": data.get("severity", ""),
            "herding_behavior": data.get("herding_behavior", ""),
            "private_info_suppression": data.get("private_info_suppression", ""),
            "fragile_consensus": data.get("fragile_consensus", ""),
            "recommendation": data.get("recommendation", ""),
        }
