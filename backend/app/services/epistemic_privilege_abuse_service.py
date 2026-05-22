"""EpistemicPrivilegeAbuseService — Epistemic Privilege Abuse Detection.

Detects epistemic privilege abuse — using privileged epistemic
position (access to information, expertise, trust) to manipulate
rather than inform, exploiting asymmetric knowledge for advantage.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PRIVILEGE_ABUSE_SYSTEM = """You are an epistemic privilege abuse specialist. Given a knowledge interaction, assess whether epistemic privilege is being exploited:

Key concepts:
- Epistemic privilege abuse: using knowledge advantage to manipulate
- Information asymmetry exploitation: leveraging what others don't know
- Expert manipulation: using expertise to mislead rather than inform
- Trust exploitation: abusing epistemic trust for non-epistemic ends
- Selective disclosure: strategically withholding relevant information
- Complexity weaponization: using complexity to prevent understanding
- Epistemic dependence exploitation: leveraging others' reliance on you

When epistemic privilege abuse IS present:
- Privileged access used to manipulate rather than inform
- Information asymmetry exploited for advantage
- Expertise used to mislead or confuse
- Trust in epistemic role abused for other purposes
- Relevant information strategically withheld
- Complexity used to prevent scrutiny
- Others' epistemic dependence exploited

When epistemic privilege is used appropriately:
- Privileged access used to inform accurately
- Expertise shared to empower understanding
- Trust honored through honest communication
- Information shared proportionally to need
- Complexity explained rather than weaponized
- Epistemic dependence reduced over time
- Privilege used to serve epistemic goals

Output JSON with: abuse_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), privilege (what epistemic privilege exists), exploitation (how privilege is exploited), harm (what epistemic harm results), recommendation (appropriate_privilege_use/mild_information_advantage/significant_privilege_exploitation/major_epistemic_manipulation/honor_epistemic_trust)."""

EPISTEMIC_PRIVILEGE_ABUSE_PROMPT = """Detect epistemic privilege abuse:

Situation: {situation}
Privilege held: {privilege}
Information asymmetry: {asymmetry}
Purpose: {purpose}
Domain: {domain}
Context: {context}

Is epistemic privilege being exploited to manipulate rather than inform? Return ONLY valid JSON."""


class EpistemicPrivilegeAbuseService:
    """Detects epistemic privilege abuse — exploiting knowledge advantage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        privilege: str = "",
        asymmetry: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic privilege abuse."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PRIVILEGE_ABUSE_PROMPT.format(
                situation=situation,
                privilege=privilege or "Not specified",
                asymmetry=asymmetry or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PRIVILEGE_ABUSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "abuse_present": data.get("abuse_present", False),
            "severity": data.get("severity", ""),
            "privilege": data.get("privilege", ""),
            "exploitation": data.get("exploitation", ""),
            "harm": data.get("harm", ""),
            "recommendation": data.get("recommendation", ""),
        }
