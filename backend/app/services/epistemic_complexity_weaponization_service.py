"""EpistemicComplexityWeaponizationService — Epistemic Complexity Weaponization Detection.

Detects epistemic complexity weaponization — weaponizing complexity
to exclude or intimidate others.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_WEAPONIZATION_SYSTEM = """You are an epistemic complexity weaponization specialist. Given weaponizing complexity to exclude, assess complexity weaponization:

Key concepts:
- Epistemic complexity weaponization: weaponizing complexity to exclude
- Gatekeeping through complexity: making things complex to exclude
- Intimidation through jargon: using jargon to intimidate
- Unnecessary complexity: adding complexity to appear superior
- Exclusion through abstraction: abstracting to exclude non-experts
- Complexity as power: using complexity to maintain power
- Obfuscation as strategy: deliberately making things unclear

When epistemic complexity weaponization IS present:
- Weaponizing complexity to exclude
- Making complex to exclude
- Using jargon to intimidate
- Adding unnecessary complexity
- Abstracting to exclude
- Using complexity for power
- Deliberately making unclear

When no complexity weaponization:
- Appropriate complexity
- Inclusive communication
- Jargon used appropriately
- Necessary complexity only
- Accessible abstraction
- Complexity for understanding
- Clarity as goal

Output JSON with: complexity_weaponization_detected (bool), severity (none/mild/moderate/severe), gatekeeping_through_complexity (what making complex to exclude), intimidation_through_jargon (what using to intimidate), unnecessary_complexity (what adding complexity to), obfuscation_as_strategy (what deliberately making unclear), recommendation (no_complexity_weaponization/mild_clarity_practice/significant_inclusion_building/major_intensive_accessibility_work/emergency_complete_complexity_weaponization)."""

EPISTEMIC_COMPLEXITY_WEAPONIZATION_PROMPT = """Detect epistemic complexity weaponization:

Gatekeeping through complexity: {gatekeeping_through_complexity}
Intimidation through jargon: {intimidation_through_jargon}
Unnecessary complexity: {unnecessary_complexity}
Obfuscation as strategy: {obfuscation_as_strategy}
Domain: {domain}
Context: {context}

Is there weaponizing complexity to exclude or intimidate others? Return ONLY valid JSON."""


class EpistemicComplexityWeaponizationService:
    """Detects epistemic complexity weaponization — weaponizing complexity to exclude."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gatekeeping_through_complexity: str,
        *,
        intimidation_through_jargon: str = "",
        unnecessary_complexity: str = "",
        obfuscation_as_strategy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity weaponization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_WEAPONIZATION_PROMPT.format(
                gatekeeping_through_complexity=gatekeeping_through_complexity,
                intimidation_through_jargon=intimidation_through_jargon or "Not specified",
                unnecessary_complexity=unnecessary_complexity or "Not specified",
                obfuscation_as_strategy=obfuscation_as_strategy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_WEAPONIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gatekeeping_through_complexity": gatekeeping_through_complexity[:200],
            "complexity_weaponization_detected": data.get("complexity_weaponization_detected", False),
            "severity": data.get("severity", ""),
            "intimidation_through_jargon": data.get("intimidation_through_jargon", ""),
            "unnecessary_complexity": data.get("unnecessary_complexity", ""),
            "obfuscation_as_strategy": data.get("obfuscation_as_strategy", ""),
            "recommendation": data.get("recommendation", ""),
        }
