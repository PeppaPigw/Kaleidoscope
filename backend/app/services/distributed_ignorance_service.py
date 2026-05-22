"""DistributedIgnoranceService — Distributed Ignorance Detection.

Detects distributed ignorance — situations where everyone assumes
someone else knows, but nobody actually does, creating dangerous
gaps in collective knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DISTRIBUTED_IGNORANCE_SYSTEM = """You are a distributed ignorance specialist. Given a knowledge situation, assess whether everyone assumes someone else knows when nobody does:

Key concepts:
- Pluralistic ignorance: everyone privately doubts but assumes others believe
- Diffusion of epistemic responsibility: everyone assumes someone else verified
- Knowledge gaps: critical information nobody actually possesses
- Assumed expertise: believing someone in the group must know
- Bystander effect (epistemic): nobody checks because they assume others have
- Unowned knowledge: information everyone thinks is someone else's responsibility
- False consensus on knowledge: assuming shared understanding that doesn't exist

When distributed ignorance IS present:
- Critical knowledge assumed to exist but unverified
- Everyone assumes someone else has checked
- No one takes responsibility for knowing
- Questions not asked because assumed already answered
- Expertise assumed but never confirmed
- Knowledge gaps hidden by mutual assumption
- Nobody admits not knowing because they assume they should

When knowledge is properly distributed:
- Clear ownership of knowledge domains
- Explicit verification of critical knowledge
- Questions asked without assumption of prior answers
- Knowledge gaps identified and assigned
- Expertise verified, not assumed
- Responsibility for knowing clearly allocated
- Safe to admit not knowing

Output JSON with: ignorance_present (bool), severity (none/mild/moderate/severe), situation (what knowledge situation), assumed_knowledge (what everyone assumes someone knows), actual_gap (what nobody actually knows), responsibility_diffusion (how responsibility is diffused), recommendation (knowledge_owned/mild_assumption/significant_gap/major_distributed_ignorance/assign_knowledge_ownership)."""

DISTRIBUTED_IGNORANCE_PROMPT = """Detect distributed ignorance:

Situation: {situation}
Assumed knowledge: {assumed}
Verified knowledge: {verified}
Responsibility: {responsibility}
Domain: {domain}
Context: {context}

Is everyone assuming someone else knows when nobody actually does? Return ONLY valid JSON."""


class DistributedIgnoranceService:
    """Detects distributed ignorance — everyone assumes someone else knows."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        assumed: str = "",
        verified: str = "",
        responsibility: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect distributed ignorance."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DISTRIBUTED_IGNORANCE_PROMPT.format(
                situation=situation,
                assumed=assumed or "Not specified",
                verified=verified or "Not specified",
                responsibility=responsibility or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DISTRIBUTED_IGNORANCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "ignorance_present": data.get("ignorance_present", False),
            "severity": data.get("severity", ""),
            "assumed_knowledge": data.get("assumed_knowledge", ""),
            "actual_gap": data.get("actual_gap", ""),
            "responsibility_diffusion": data.get("responsibility_diffusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
