"""EpistemicGroupSharedInformationBiasService — Epistemic Shared Information Bias Detection.

Detects epistemic group shared information bias — groups spending time discussing
shared information while ignoring unique information held by individuals.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROUP_SHARED_INFORMATION_BIAS_SYSTEM = """You are an epistemic group shared information bias specialist. Given shared information bias, assess unique info neglect:

Key concepts:
- Epistemic shared information bias: groups discussing shared info, ignoring unique
- Common knowledge effect: shared info dominating discussion
- Hidden profile problem: optimal solution requiring unshared info never found
- Repetition advantage: shared info repeated more, seeming more important
- Social validation: shared info validated by multiple members
- Unique info devaluation: unique info from single member devalued
- Discussion time allocation: disproportionate time on shared vs unique info

When epistemic shared information bias IS present:
- Shared info dominating discussion
- Common knowledge effect active
- Hidden profiles not discovered
- Repetition creating importance
- Social validation biasing
- Unique info devalued
- Time disproportionately on shared

When no shared information bias:
- Unique info actively elicited
- Hidden profiles discovered
- Repetition not equated with importance
- All sources valued equally
- Unique perspectives sought
- Time allocated to novel info
- Discussion structured for unique info

Output JSON with: shared_information_bias_detected (bool), severity (none/mild/moderate/severe), common_knowledge_dominance (what common knowledge dominating), hidden_profile_failure (what hidden profiles missed), unique_info_devaluation (what unique info devalued), time_allocation_bias (what time allocation biased), recommendation (no_shared_info_bias/mild_unique_info_elicitation/significant_structured_sharing/major_intensive_hidden_profile_search/emergency_complete_shared_info_bias)."""

EPISTEMIC_GROUP_SHARED_INFORMATION_BIAS_PROMPT = """Detect epistemic group shared information bias:

Common knowledge dominance: {common_knowledge_dominance}
Hidden profile failure: {hidden_profile_failure}
Unique info devaluation: {unique_info_devaluation}
Time allocation bias: {time_allocation_bias}
Domain: {domain}
Context: {context}

Is the group discussing shared information while ignoring unique information? Return ONLY valid JSON."""


class EpistemicGroupSharedInformationBiasService:
    """Detects epistemic shared information bias — unique info neglected."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        common_knowledge_dominance: str,
        *,
        hidden_profile_failure: str = "",
        unique_info_devaluation: str = "",
        time_allocation_bias: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic group shared information bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROUP_SHARED_INFORMATION_BIAS_PROMPT.format(
                common_knowledge_dominance=common_knowledge_dominance,
                hidden_profile_failure=hidden_profile_failure or "Not specified",
                unique_info_devaluation=unique_info_devaluation or "Not specified",
                time_allocation_bias=time_allocation_bias or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROUP_SHARED_INFORMATION_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "common_knowledge_dominance": common_knowledge_dominance[:200],
            "shared_information_bias_detected": data.get("shared_information_bias_detected", False),
            "severity": data.get("severity", ""),
            "hidden_profile_failure": data.get("hidden_profile_failure", ""),
            "unique_info_devaluation": data.get("unique_info_devaluation", ""),
            "time_allocation_bias": data.get("time_allocation_bias", ""),
            "recommendation": data.get("recommendation", ""),
        }
