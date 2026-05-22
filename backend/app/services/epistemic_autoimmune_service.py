"""EpistemicAutoImmuneService — Epistemic Autoimmune Detection.

Detects epistemic autoimmune responses — knowledge systems
attacking their own valid components.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_AUTOIMMUNE_SYSTEM = """You are an epistemic autoimmune specialist. Given a knowledge system, assess whether it is attacking its own valid components:

Key concepts:
- Epistemic autoimmune: system attacking its own valid parts
- Self-destruction: destroying own legitimate knowledge
- Friendly fire: attacking allies as if enemies
- Internal purge: purging valid ideas as if invalid
- Purity spiral: purity demands destroying valid components
- Self-sabotage: sabotaging own knowledge base
- Misidentification: misidentifying own components as threats

When epistemic autoimmune IS present:
- Knowledge system attacking its own valid components
- Destroying own legitimate knowledge
- Attacking valid ideas as if they were threats
- Purging valid ideas in pursuit of purity
- Purity demands destroying legitimate components
- Sabotaging own knowledge base
- Misidentifying own valid components as threats

When healthy self-correction is present:
- System correctly identifying and removing errors
- Legitimate knowledge preserved
- Only genuinely invalid ideas rejected
- Correction targeted and proportionate
- Valid components recognized and protected
- Self-correction strengthening not weakening
- Accurate identification of actual threats

Output JSON with: autoimmune_present (bool), severity (none/mild/moderate/severe), system (what system is affected), target (what valid component is attacked), misidentification (how misidentification occurs), damage (what damage results), recommendation (healthy_self_correction/mild_overreaction/significant_autoimmune/major_self_destruction/stop_attacking_valid_components)."""

EPISTEMIC_AUTOIMMUNE_PROMPT = """Detect epistemic autoimmune:

System: {system}
Target: {target}
Misidentification: {misidentification}
Damage: {damage}
Domain: {domain}
Context: {context}

Is the knowledge system attacking its own valid components? Return ONLY valid JSON."""


class EpistemicAutoImmuneService:
    """Detects epistemic autoimmune — system attacking own valid components."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        target: str = "",
        misidentification: str = "",
        damage: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic autoimmune."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_AUTOIMMUNE_PROMPT.format(
                system=system,
                target=target or "Not specified",
                misidentification=misidentification or "Not specified",
                damage=damage or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_AUTOIMMUNE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "autoimmune_present": data.get("autoimmune_present", False),
            "severity": data.get("severity", ""),
            "target": data.get("target", ""),
            "misidentification": data.get("misidentification", ""),
            "damage": data.get("damage", ""),
            "recommendation": data.get("recommendation", ""),
        }
