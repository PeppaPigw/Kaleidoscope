"""WeaponizedComplexityService — Weaponized Complexity Detection.

Detects weaponized complexity — using complexity as a weapon to
exclude, confuse, or prevent understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WEAPONIZED_COMPLEXITY_SYSTEM = """You are a weaponized complexity specialist. Given a discourse or explanation, assess whether complexity is being used as a weapon:

Key concepts:
- Weaponized complexity: complexity used to exclude or confuse
- Gatekeeping through jargon: using technical language to exclude
- Obfuscation through complexity: hiding simple ideas in complex language
- Complexity as authority: using complexity to claim expertise
- Deliberate obscurantism: making things unclear on purpose
- Exclusionary expertise: using expertise to exclude rather than include
- Complexity theater: performing complexity without substance

When weaponized complexity IS present:
- Complexity used to exclude rather than explain
- Jargon deployed to gatekeep not communicate
- Simple ideas hidden in unnecessarily complex language
- Complexity used to claim unwarranted authority
- Deliberate obscurantism preventing understanding
- Expertise used to exclude rather than include
- Complexity performed without serving understanding

When appropriate complexity is present:
- Complexity proportionate to subject matter
- Technical language used for precision
- Complex ideas explained as clearly as possible
- Expertise shared to include and educate
- Difficulty inherent to the material
- Complexity serving understanding not preventing it

Output JSON with: weaponized_present (bool), severity (none/mild/moderate/severe), discourse (what discourse occurs), complexity_type (what type of complexity is used), exclusion_effect (who is excluded), purpose (what purpose complexity serves), recommendation (appropriate_complexity/mild_obscurantism/significant_weaponized_complexity/major_deliberate_exclusion/communicate_clearly)."""

WEAPONIZED_COMPLEXITY_PROMPT = """Detect weaponized complexity:

Discourse: {discourse}
Complexity type: {complexity_type}
Exclusion effect: {exclusion}
Purpose served: {purpose}
Domain: {domain}
Context: {context}

Is complexity being used as a weapon to exclude or confuse? Return ONLY valid JSON."""


class WeaponizedComplexityService:
    """Detects weaponized complexity — complexity used to exclude or confuse."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        complexity_type: str = "",
        exclusion: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect weaponized complexity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WEAPONIZED_COMPLEXITY_PROMPT.format(
                discourse=discourse,
                complexity_type=complexity_type or "Not specified",
                exclusion=exclusion or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WEAPONIZED_COMPLEXITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "weaponized_present": data.get("weaponized_present", False),
            "severity": data.get("severity", ""),
            "complexity_type": data.get("complexity_type", ""),
            "exclusion_effect": data.get("exclusion_effect", ""),
            "purpose": data.get("purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
