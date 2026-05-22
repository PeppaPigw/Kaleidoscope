"""EpistemicMemoryWeaponizationService — Epistemic Memory Weaponization Detection.

Detects epistemic memory weaponization — weaponizing memory of past
statements against others to win arguments or undermine credibility.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MEMORY_WEAPONIZATION_SYSTEM = """You are an epistemic memory weaponization specialist. Given weaponizing memory of past statements, assess memory weaponization:

Key concepts:
- Epistemic memory weaponization: weaponizing memory of past statements against others
- Gotcha archaeology: digging up past statements to use as gotchas
- Consistency policing: policing others' consistency unfairly
- Context stripping: stripping context from past statements to weaponize
- Growth punishment: punishing others for changing their minds
- Quote mining: mining past quotes to undermine
- Position freezing: freezing others in past positions

When epistemic memory weaponization IS present:
- Weaponizing past statements
- Digging up gotchas
- Policing consistency unfairly
- Stripping context from past
- Punishing mind-changing
- Mining quotes to undermine
- Freezing in past positions

When no memory weaponization:
- Respecting intellectual evolution
- No gotcha archaeology
- Fair consistency expectations
- Maintaining context
- Allowing mind-changing
- Fair quoting
- Allowing position evolution

Output JSON with: memory_weaponization_detected (bool), severity (none/mild/moderate/severe), gotcha_archaeology (what past statements dug up), consistency_policing (what consistency policed unfairly), context_stripping (what context stripped from), growth_punishment (what mind-changing punished), recommendation (no_memory_weaponization/mild_fairness_practice/significant_respect_building/major_intensive_weaponization_cessation/emergency_complete_memory_weaponization)."""

EPISTEMIC_MEMORY_WEAPONIZATION_PROMPT = """Detect epistemic memory weaponization:

Gotcha archaeology: {gotcha_archaeology}
Consistency policing: {consistency_policing}
Context stripping: {context_stripping}
Growth punishment: {growth_punishment}
Domain: {domain}
Context: {context}

Is there weaponizing memory of past statements against others? Return ONLY valid JSON."""


class EpistemicMemoryWeaponizationService:
    """Detects epistemic memory weaponization — weaponizing past statements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gotcha_archaeology: str,
        *,
        consistency_policing: str = "",
        context_stripping: str = "",
        growth_punishment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic memory weaponization."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MEMORY_WEAPONIZATION_PROMPT.format(
                gotcha_archaeology=gotcha_archaeology,
                consistency_policing=consistency_policing or "Not specified",
                context_stripping=context_stripping or "Not specified",
                growth_punishment=growth_punishment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MEMORY_WEAPONIZATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gotcha_archaeology": gotcha_archaeology[:200],
            "memory_weaponization_detected": data.get("memory_weaponization_detected", False),
            "severity": data.get("severity", ""),
            "consistency_policing": data.get("consistency_policing", ""),
            "context_stripping": data.get("context_stripping", ""),
            "growth_punishment": data.get("growth_punishment", ""),
            "recommendation": data.get("recommendation", ""),
        }
