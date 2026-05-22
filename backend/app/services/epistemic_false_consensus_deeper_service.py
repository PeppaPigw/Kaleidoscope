"""EpistemicFalseConsensusDeeperService — Epistemic False Consensus Detection (Deeper).

Detects epistemic false consensus — assuming consensus exists
when it doesn't, projecting agreement onto others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_FALSE_CONSENSUS_DEEPER_SYSTEM = """You are an epistemic false consensus specialist. Given assumed consensus that doesn't exist, assess false consensus:

Key concepts:
- Epistemic false consensus: assuming consensus exists when it doesn't
- Agreement projection: projecting own views onto others
- Silence as agreement: interpreting silence as agreement
- Vocal minority confusion: confusing vocal minority with majority
- Selection bias in sampling: sampling only agreeing voices
- Preference falsification blindness: blind to preference falsification
- Echo chamber consensus: consensus only within echo chamber

When epistemic false consensus IS present:
- Consensus assumed without evidence
- Agreement projected
- Silence read as agreement
- Vocal minority confused with majority
- Only agreeing voices sampled
- Preference falsification missed
- Consensus only in echo chamber

When no false consensus:
- Consensus verified
- Others' views checked
- Silence not assumed as agreement
- Majority actually surveyed
- Diverse voices sampled
- Preference falsification considered
- Consensus tested outside bubble

Output JSON with: false_consensus_detected (bool), severity (none/mild/moderate/severe), agreement_projection (what projected), silence_as_agreement (what silence misread), vocal_minority_confusion (what minority confused), echo_chamber_consensus (what echo chamber), recommendation (no_false_consensus/mild_verification_practice/significant_diversity_sampling/major_intensive_consensus_testing/emergency_complete_false_consensus)."""

EPISTEMIC_FALSE_CONSENSUS_DEEPER_PROMPT = """Detect epistemic false consensus:

Agreement projection: {agreement_projection}
Silence as agreement: {silence_as_agreement}
Vocal minority confusion: {vocal_minority_confusion}
Echo chamber consensus: {echo_chamber_consensus}
Domain: {domain}
Context: {context}

Is consensus being assumed when it doesn't actually exist? Return ONLY valid JSON."""


class EpistemicFalseConsensusDeeperService:
    """Detects epistemic false consensus — assumed agreement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        agreement_projection: str,
        *,
        silence_as_agreement: str = "",
        vocal_minority_confusion: str = "",
        echo_chamber_consensus: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic false consensus."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_FALSE_CONSENSUS_DEEPER_PROMPT.format(
                agreement_projection=agreement_projection,
                silence_as_agreement=silence_as_agreement or "Not specified",
                vocal_minority_confusion=vocal_minority_confusion or "Not specified",
                echo_chamber_consensus=echo_chamber_consensus or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_FALSE_CONSENSUS_DEEPER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "agreement_projection": agreement_projection[:200],
            "false_consensus_detected": data.get("false_consensus_detected", False),
            "severity": data.get("severity", ""),
            "silence_as_agreement": data.get("silence_as_agreement", ""),
            "vocal_minority_confusion": data.get("vocal_minority_confusion", ""),
            "echo_chamber_consensus": data.get("echo_chamber_consensus", ""),
            "recommendation": data.get("recommendation", ""),
        }
