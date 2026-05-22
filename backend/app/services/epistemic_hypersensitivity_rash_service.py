"""EpistemicHypersensitivityRashService — Epistemic Hypersensitivity Rash Detection.

Detects epistemic hypersensitivity rash — overreaction to benign intellectual
contact, where harmless ideas trigger disproportionate defensive response.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_HYPERSENSITIVITY_RASH_SYSTEM = """You are an epistemic hypersensitivity rash specialist. Given intellectual contact reactions, assess whether overreaction to benign input occurs:

Key concepts:
- Epistemic hypersensitivity rash: overreaction to benign intellectual contact
- Contact dermatitis: reaction from touching harmless ideas
- Urticaria: rapid swelling response to intellectual allergen
- Sensitization: becoming reactive after prior exposure
- Patch testing: identifying which ideas trigger reaction
- Antihistamine: dampening the overreactive response
- Desensitization: gradually reducing reactivity

When epistemic hypersensitivity rash IS present:
- Overreaction to benign intellectual contact
- Reaction from touching harmless ideas
- Rapid defensive swelling to intellectual allergens
- Becoming reactive after prior exposure
- Identifiable trigger ideas
- Need to dampen overreactive response
- Potential for gradual desensitization

When healthy response is present:
- Proportionate reaction to contact
- No reaction to harmless ideas
- No defensive swelling
- No sensitization
- No trigger identification needed
- No dampening needed
- Normal tolerance

Output JSON with: hypersensitivity_rash_present (bool), severity (none/mild/moderate/severe), contact_dermatitis (what harmless reaction), urticaria (what rapid swelling), sensitization (what prior exposure reactivity), trigger_identification (what allergen), recommendation (healthy_response/mild_rash/significant_hypersensitivity_rash/major_overreaction/desensitize_intellectual_response)."""

EPISTEMIC_HYPERSENSITIVITY_RASH_PROMPT = """Detect epistemic hypersensitivity rash:

Contact dermatitis: {contact_dermatitis}
Urticaria: {urticaria}
Sensitization: {sensitization}
Trigger identification: {trigger_identification}
Domain: {domain}
Context: {context}

Is there overreaction to benign intellectual contact, with harmless ideas triggering disproportionate response? Return ONLY valid JSON."""


class EpistemicHypersensitivityRashService:
    """Detects epistemic hypersensitivity rash — overreaction to benign contact."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contact_dermatitis: str,
        *,
        urticaria: str = "",
        sensitization: str = "",
        trigger_identification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic hypersensitivity rash."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_HYPERSENSITIVITY_RASH_PROMPT.format(
                contact_dermatitis=contact_dermatitis,
                urticaria=urticaria or "Not specified",
                sensitization=sensitization or "Not specified",
                trigger_identification=trigger_identification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_HYPERSENSITIVITY_RASH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contact_dermatitis": contact_dermatitis[:200],
            "hypersensitivity_rash_present": data.get("hypersensitivity_rash_present", False),
            "severity": data.get("severity", ""),
            "urticaria": data.get("urticaria", ""),
            "sensitization": data.get("sensitization", ""),
            "trigger_identification": data.get("trigger_identification", ""),
            "recommendation": data.get("recommendation", ""),
        }
