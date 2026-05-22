"""EpistemicIdentitySystemJustificationService — Epistemic Identity System Justification Detection.

Detects system justification bias where existing arrangements are defended
through distorted evidence evaluation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IDENTITY_SYSTEM_JUSTIFICATION_SYSTEM = """You are an epistemic identity system justification specialist. Given status-quo defense patterns, assess system-justifying distortion:

Key concepts:
- System justification bias: existing arrangements are defended as legitimate
- Status quo rationalization: current arrangements are explained as deserved or optimal
- Just-world belief: outcomes are assumed to reflect justice or merit
- Victim blaming: harmed parties are blamed to preserve system legitimacy
- Meritocracy myth: unequal outcomes are treated as proof of unequal merit

When system justification IS present:
- Status quo is rationalized
- Existing arrangements are treated as natural or deserved
- Just-world assumptions replace evidence
- Victims are blamed for systemic harms
- Meritocracy claims shield the system

When no system justification:
- Status quo is evaluated as one option
- System legitimacy is tested
- Outcomes are separated from desert
- Victim blaming is avoided
- Merit claims are empirically checked

Output JSON with: system_justification_detected (bool), severity (none/mild/moderate/severe), just_world_belief (what outcomes are treated as deserved), victim_blaming (where harm is blamed on victims), meritocracy_myth (what unequal outcome is naturalized), recommendation (no_system_justification/mild_status_quo_check/significant_structural_review/major_legitimacy_audit/emergency_complete_system_justification_debiasing)."""

EPISTEMIC_IDENTITY_SYSTEM_JUSTIFICATION_PROMPT = """Detect epistemic identity system justification:

Status quo rationalization: {status_quo_rationalization}
Just-world belief: {just_world_belief}
Victim blaming: {victim_blaming}
Meritocracy myth: {meritocracy_myth}
Domain: {domain}
Context: {context}

Is defense of existing arrangements distorting evidence evaluation? Return ONLY valid JSON."""


class EpistemicIdentitySystemJustificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        status_quo_rationalization: str,
        *,
        just_world_belief: str = "",
        victim_blaming: str = "",
        meritocracy_myth: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IDENTITY_SYSTEM_JUSTIFICATION_PROMPT.format(
                status_quo_rationalization=status_quo_rationalization,
                just_world_belief=just_world_belief or "Not specified",
                victim_blaming=victim_blaming or "Not specified",
                meritocracy_myth=meritocracy_myth or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IDENTITY_SYSTEM_JUSTIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "status_quo_rationalization": status_quo_rationalization[:200],
            "system_justification_detected": data.get("system_justification_detected", False),
            "severity": data.get("severity", ""),
            "just_world_belief": data.get("just_world_belief", ""),
            "victim_blaming": data.get("victim_blaming", ""),
            "meritocracy_myth": data.get("meritocracy_myth", ""),
            "recommendation": data.get("recommendation", ""),
        }
