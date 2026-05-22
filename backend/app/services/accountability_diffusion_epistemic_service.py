"""AccountabilityDiffusionEpistemicService — Epistemic Accountability Diffusion Detection.

Detects epistemic accountability diffusion — responsibility for
knowledge so diffused across an organization that no one effectively
owns it, leading to knowledge gaps that everyone assumes someone else
is handling.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACCOUNTABILITY_DIFFUSION_EPISTEMIC_SYSTEM = """You are an epistemic accountability diffusion specialist. Given an organizational knowledge situation, assess whether responsibility is too diffused:

Key concepts:
- Accountability diffusion: no one owns the knowledge responsibility
- Bystander effect epistemic: everyone assumes someone else knows
- Ownership vacuum: knowledge without clear owner
- Responsibility gaps: spaces between roles where knowledge falls
- Collective assumption: everyone assumes it's handled
- Diffused obligation: obligation so spread it's ineffective
- Knowledge orphans: important knowledge no one maintains

When accountability diffusion IS present:
- No one clearly owns critical knowledge
- Everyone assumes someone else is responsible
- Knowledge falls between organizational roles
- Responsibility so diffused it's ineffective
- Important knowledge has no maintainer
- Gaps exist that everyone assumes are covered
- Collective assumption of coverage without verification

When distributed responsibility is appropriate:
- Clear ownership assigned for each knowledge area
- Overlapping responsibility with explicit coordination
- Gaps identified and assigned
- Assumptions about coverage verified
- Distributed responsibility with accountability
- Knowledge maintenance explicitly assigned
- Regular verification that coverage is complete

Output JSON with: diffusion_present (bool), severity (none/mild/moderate/severe), situation (what situation is analyzed), knowledge_orphaned (what knowledge lacks ownership), assumption (what assumption is made), gap (what gap results), recommendation (appropriate_distributed_responsibility/mild_ownership_ambiguity/significant_accountability_diffusion/major_knowledge_orphaning/assign_clear_ownership)."""

ACCOUNTABILITY_DIFFUSION_EPISTEMIC_PROMPT = """Detect epistemic accountability diffusion:

Situation: {situation}
Knowledge area: {knowledge}
Ownership: {ownership}
Assumptions: {assumptions}
Domain: {domain}
Context: {context}

Is responsibility for knowledge so diffused that no one effectively owns it? Return ONLY valid JSON."""


class AccountabilityDiffusionEpistemicService:
    """Detects epistemic accountability diffusion — knowledge responsibility too diffused."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        ownership: str = "",
        assumptions: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic accountability diffusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACCOUNTABILITY_DIFFUSION_EPISTEMIC_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                ownership=ownership or "Not specified",
                assumptions=assumptions or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACCOUNTABILITY_DIFFUSION_EPISTEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "diffusion_present": data.get("diffusion_present", False),
            "severity": data.get("severity", ""),
            "knowledge_orphaned": data.get("knowledge_orphaned", ""),
            "assumption": data.get("assumption", ""),
            "gap": data.get("gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
