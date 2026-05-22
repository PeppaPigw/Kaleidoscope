"""EpistemicDrugInteractionService — Epistemic Drug Interaction Detection.

Detects epistemic drug interactions — harmful interactions between
intellectual interventions that amplify toxicity or cancel effectiveness.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DRUG_INTERACTION_SYSTEM = """You are an epistemic drug interaction specialist. Given intellectual interventions, assess whether harmful interactions exist:

Key concepts:
- Epistemic drug interaction: harmful interaction between intellectual interventions
- Synergistic toxicity: combined effect worse than sum
- Antagonism: one intervention canceling another
- Potentiation: one intervention amplifying another dangerously
- Contraindication: interventions that must never combine
- Therapeutic window: narrow range between effective and toxic
- Polypharmacy: too many interventions simultaneously

When epistemic drug interaction IS present:
- Harmful interactions between intellectual interventions
- Combined effect worse than individual sum
- One intervention canceling another's benefit
- One intervention dangerously amplifying another
- Interventions that should never combine
- Narrow range between helpful and harmful
- Too many simultaneous interventions

When safe combination is present:
- No harmful interactions
- Additive beneficial effects
- No cancellation
- No dangerous amplification
- Compatible interventions
- Wide therapeutic window
- Appropriate number of interventions

Output JSON with: drug_interaction_present (bool), severity (none/mild/moderate/severe), synergistic_toxicity (what combined harm), antagonism (what cancellation), potentiation (what amplification), polypharmacy (what excess), recommendation (safe_combination/mild_interaction/significant_drug_interaction/major_contraindication/reduce_intellectual_polypharmacy)."""

EPISTEMIC_DRUG_INTERACTION_PROMPT = """Detect epistemic drug interaction:

Synergistic toxicity: {synergistic_toxicity}
Antagonism: {antagonism}
Potentiation: {potentiation}
Polypharmacy: {polypharmacy}
Domain: {domain}
Context: {context}

Are there harmful interactions between intellectual interventions? Return ONLY valid JSON."""


class EpistemicDrugInteractionService:
    """Detects epistemic drug interactions — harmful intellectual intervention combinations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        synergistic_toxicity: str,
        *,
        antagonism: str = "",
        potentiation: str = "",
        polypharmacy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic drug interaction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DRUG_INTERACTION_PROMPT.format(
                synergistic_toxicity=synergistic_toxicity,
                antagonism=antagonism or "Not specified",
                potentiation=potentiation or "Not specified",
                polypharmacy=polypharmacy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DRUG_INTERACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "synergistic_toxicity": synergistic_toxicity[:200],
            "drug_interaction_present": data.get("drug_interaction_present", False),
            "severity": data.get("severity", ""),
            "antagonism": data.get("antagonism", ""),
            "potentiation": data.get("potentiation", ""),
            "polypharmacy": data.get("polypharmacy", ""),
            "recommendation": data.get("recommendation", ""),
        }
