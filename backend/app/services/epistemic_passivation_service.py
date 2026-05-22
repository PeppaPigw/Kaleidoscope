"""EpistemicPassivationService — Epistemic Passivation Detection.

Detects epistemic passivation — ideas forming a thin protective oxide
layer that prevents further reaction with the environment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PASSIVATION_SYSTEM = """You are an epistemic passivation specialist. Given an idea protection pattern, assess whether ideas form protective layers preventing further reaction:

Key concepts:
- Epistemic passivation: protective layer preventing further reaction
- Oxide layer: thin protective film formed by initial reaction
- Self-healing: layer reforming when damaged
- Breakdown potential: voltage at which protection fails
- Pitting: localized failure of the protective layer
- Transpassive: region where protection dissolves
- Chromium analogy: specific elements enabling passivation

When epistemic passivation IS present:
- Ideas forming thin protective layers preventing further reaction
- Initial reaction creating a protective film
- Protection reforming when damaged
- Threshold at which protection fails
- Localized failures in the protective layer
- Conditions where protection dissolves entirely
- Specific elements enabling the passivation

When active reaction is present:
- Ideas reacting freely with environment
- No protective film forming
- No self-healing protection
- No breakdown threshold
- No localized failures (uniform reaction)
- Continuous reaction with environment
- No passivating elements present

Output JSON with: passivation_present (bool), severity (none/mild/moderate/severe), oxide_layer (what protective film), self_healing (what reforms when damaged), breakdown (what causes failure), pitting (what localized failures), recommendation (active_reaction/mild_passivation/significant_passivation/major_protective_layer/controlled_depassivation)."""

EPISTEMIC_PASSIVATION_PROMPT = """Detect epistemic passivation:

Oxide layer: {oxide_layer}
Self-healing: {self_healing}
Breakdown: {breakdown}
Pitting: {pitting}
Domain: {domain}
Context: {context}

Are ideas forming a thin protective oxide layer that prevents further reaction with the environment? Return ONLY valid JSON."""


class EpistemicPassivationService:
    """Detects epistemic passivation — protective layer preventing reaction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        oxide_layer: str,
        *,
        self_healing: str = "",
        breakdown: str = "",
        pitting: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic passivation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PASSIVATION_PROMPT.format(
                oxide_layer=oxide_layer,
                self_healing=self_healing or "Not specified",
                breakdown=breakdown or "Not specified",
                pitting=pitting or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PASSIVATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "oxide_layer": oxide_layer[:200],
            "passivation_present": data.get("passivation_present", False),
            "severity": data.get("severity", ""),
            "self_healing": data.get("self_healing", ""),
            "breakdown": data.get("breakdown", ""),
            "pitting": data.get("pitting", ""),
            "recommendation": data.get("recommendation", ""),
        }
