"""EpistemicGroupStatusHierarchyService — Epistemic Group Status Hierarchy Detection.

Detects epistemic group status hierarchy — status hierarchies suppressing
lower-status knowledge and amplifying higher-status opinions.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROUP_STATUS_HIERARCHY_SYSTEM = """You are an epistemic group status hierarchy specialist. Given status hierarchy effects, assess knowledge suppression:

Key concepts:
- Epistemic status hierarchy: status suppressing lower-status knowledge
- HiPPO effect: highest paid person's opinion dominating
- Deference cascade: lower-status members deferring to higher-status
- Status-based credibility: credibility assigned by status not evidence
- Expertise-status confusion: conflating organizational status with expertise
- Voice suppression: lower-status voices suppressed in discussion
- Status-based attention: attention allocated by status not relevance

When epistemic status hierarchy IS present:
- Status suppressing knowledge
- HiPPO effect active
- Deference cascading
- Credibility by status
- Status confused with expertise
- Lower voices suppressed
- Attention by status

When no status hierarchy effect:
- Knowledge valued regardless of status
- All voices heard
- Credibility by evidence
- Expertise distinguished from status
- Lower-status contributions valued
- Attention by relevance
- Hierarchy not distorting knowledge

Output JSON with: status_hierarchy_detected (bool), severity (none/mild/moderate/severe), hippo_effect (what HiPPO effect), deference_cascade (what deference cascading), status_credibility (what status-based credibility), voice_suppression (what voices suppressed), recommendation (no_status_hierarchy/mild_voice_equalization/significant_status_separation/major_intensive_hierarchy_neutralization/emergency_complete_status_hierarchy)."""

EPISTEMIC_GROUP_STATUS_HIERARCHY_PROMPT = """Detect epistemic group status hierarchy:

HiPPO effect: {hippo_effect}
Deference cascade: {deference_cascade}
Status credibility: {status_credibility}
Voice suppression: {voice_suppression}
Domain: {domain}
Context: {context}

Is status hierarchy suppressing lower-status knowledge? Return ONLY valid JSON."""


class EpistemicGroupStatusHierarchyService:
    """Detects epistemic status hierarchy — knowledge suppression by status."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hippo_effect: str,
        *,
        deference_cascade: str = "",
        status_credibility: str = "",
        voice_suppression: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic group status hierarchy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROUP_STATUS_HIERARCHY_PROMPT.format(
                hippo_effect=hippo_effect,
                deference_cascade=deference_cascade or "Not specified",
                status_credibility=status_credibility or "Not specified",
                voice_suppression=voice_suppression or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROUP_STATUS_HIERARCHY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hippo_effect": hippo_effect[:200],
            "status_hierarchy_detected": data.get("status_hierarchy_detected", False),
            "severity": data.get("severity", ""),
            "deference_cascade": data.get("deference_cascade", ""),
            "status_credibility": data.get("status_credibility", ""),
            "voice_suppression": data.get("voice_suppression", ""),
            "recommendation": data.get("recommendation", ""),
        }
