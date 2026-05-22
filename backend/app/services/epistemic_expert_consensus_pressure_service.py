"""EpistemicExpertConsensusPressureService — Epistemic Expert Consensus Pressure Detection.

Detects epistemic expert consensus pressure — pressure to conform to expert
consensus suppressing valid dissent and alternative perspectives.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERT_CONSENSUS_PRESSURE_SYSTEM = """You are an epistemic expert consensus pressure specialist. Given pressure to conform to expert consensus, assess consensus pressure:

Key concepts:
- Epistemic expert consensus pressure: pressure suppressing valid dissent
- Conformity enforcement: enforcing conformity to consensus view
- Dissent suppression: suppressing legitimate disagreement
- Career threat: career consequences for challenging consensus
- Publication bias: difficulty publishing dissenting views
- Social exclusion: exclusion from expert community for dissent
- Orthodoxy enforcement: enforcing orthodoxy over inquiry

When epistemic expert consensus pressure IS present:
- Pressure to conform
- Conformity enforced
- Dissent suppressed
- Career threatened
- Publication biased
- Social exclusion threatened
- Orthodoxy enforced

When no consensus pressure:
- Dissent welcomed
- Conformity not enforced
- Disagreement legitimate
- Career not threatened by dissent
- Publication open
- Community inclusive
- Inquiry over orthodoxy

Output JSON with: expert_consensus_pressure_detected (bool), severity (none/mild/moderate/severe), conformity_enforcement (what conformity enforced), dissent_suppression (what dissent suppressed), career_threat (what career threatened), orthodoxy_enforcement (what orthodoxy enforced), recommendation (no_consensus_pressure/mild_dissent_protection/significant_pluralism_recovery/major_intensive_orthodoxy_challenge/emergency_complete_consensus_pressure)."""

EPISTEMIC_EXPERT_CONSENSUS_PRESSURE_PROMPT = """Detect epistemic expert consensus pressure:

Conformity enforcement: {conformity_enforcement}
Dissent suppression: {dissent_suppression}
Career threat: {career_threat}
Orthodoxy enforcement: {orthodoxy_enforcement}
Domain: {domain}
Context: {context}

Is there pressure to conform to expert consensus suppressing valid dissent? Return ONLY valid JSON."""


class EpistemicExpertConsensusPressureService:
    """Detects epistemic expert consensus pressure — dissent suppression."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conformity_enforcement: str,
        *,
        dissent_suppression: str = "",
        career_threat: str = "",
        orthodoxy_enforcement: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expert consensus pressure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERT_CONSENSUS_PRESSURE_PROMPT.format(
                conformity_enforcement=conformity_enforcement,
                dissent_suppression=dissent_suppression or "Not specified",
                career_threat=career_threat or "Not specified",
                orthodoxy_enforcement=orthodoxy_enforcement or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERT_CONSENSUS_PRESSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conformity_enforcement": conformity_enforcement[:200],
            "expert_consensus_pressure_detected": data.get("expert_consensus_pressure_detected", False),
            "severity": data.get("severity", ""),
            "dissent_suppression": data.get("dissent_suppression", ""),
            "career_threat": data.get("career_threat", ""),
            "orthodoxy_enforcement": data.get("orthodoxy_enforcement", ""),
            "recommendation": data.get("recommendation", ""),
        }
