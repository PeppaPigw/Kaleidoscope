"""EpistemicSocialPluralisticIgnoranceService - Pluralistic Ignorance Detection.

Detects pluralistic ignorance where private doubts are hidden due to perceived consensus.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SOCIAL_PLURALISTIC_IGNORANCE_SYSTEM = """You are an epistemic social pluralistic ignorance specialist. Given group dynamics, assess whether private doubts are hidden due to perceived consensus:

Key concepts:
- Pluralistic ignorance: majority privately disagrees but assumes others agree
- False consensus maintenance: everyone conforms to what they think others believe
- Preference falsification: hiding true beliefs to match perceived norm
- Spiral of silence: dissent suppressed by fear of isolation

When pluralistic ignorance IS present:
- Private doubts hidden
- False consensus maintained
- Preferences falsified
- Dissent suppressed
- Actual majority opinion invisible

When no pluralistic ignorance:
- Private views expressed
- Actual consensus measured
- Preferences honestly stated
- Dissent welcomed
- Majority opinion visible

Output JSON with: pluralistic_ignorance_detected (bool), severity (none/mild/moderate/severe), false_consensus_maintenance (what false consensus), preference_falsification (what preference falsified), spiral_of_silence (what silence spiral), recommendation (no_pluralistic_ignorance/mild_preference_check/significant_dissent_surfacing/major_consensus_reconstruction/emergency_complete_pluralistic_ignorance)."""

EPISTEMIC_SOCIAL_PLURALISTIC_IGNORANCE_PROMPT = """Detect epistemic social pluralistic ignorance:

Group dynamic: {group_dynamic}
False consensus maintenance: {false_consensus_maintenance}
Preference falsification: {preference_falsification}
Spiral of silence: {spiral_of_silence}
Domain: {domain}
Context: {context}

Are private doubts being hidden due to perceived consensus? Return ONLY valid JSON."""


class EpistemicSocialPluralisticIgnoranceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        group_dynamic: str,
        *,
        false_consensus_maintenance: str = "",
        preference_falsification: str = "",
        spiral_of_silence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SOCIAL_PLURALISTIC_IGNORANCE_PROMPT.format(
                group_dynamic=group_dynamic,
                false_consensus_maintenance=false_consensus_maintenance or "Not specified",
                preference_falsification=preference_falsification or "Not specified",
                spiral_of_silence=spiral_of_silence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SOCIAL_PLURALISTIC_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "group_dynamic": group_dynamic[:200],
            "pluralistic_ignorance_detected": data.get("pluralistic_ignorance_detected", False),
            "severity": data.get("severity", ""),
            "false_consensus_maintenance": data.get("false_consensus_maintenance", ""),
            "preference_falsification": data.get("preference_falsification", ""),
            "spiral_of_silence": data.get("spiral_of_silence", ""),
            "recommendation": data.get("recommendation", ""),
        }
