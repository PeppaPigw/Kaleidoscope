"""EpistemicMannerOfDeathService — Epistemic Manner of Death Detection.

Detects epistemic manner of death — classifying whether intellectual failure
was natural, accidental, self-inflicted, or externally caused.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MANNER_OF_DEATH_SYSTEM = """You are an epistemic manner of death specialist. Given intellectual failure circumstances, classify the manner:

Key concepts:
- Epistemic manner of death: classification of how failure occurred
- Natural: failure from internal disease process
- Accidental: failure from unintentional external event
- Self-inflicted: failure from deliberate self-harm
- Homicide: failure caused by another's actions
- Undetermined: insufficient evidence to classify
- Pending: investigation still ongoing

When epistemic manner of death IS classifiable:
- Clear classification of how failure occurred
- Internal disease process identified (natural)
- Unintentional external event identified (accidental)
- Deliberate self-harm identified (self-inflicted)
- Another's actions identified (homicide)
- Or insufficient evidence (undetermined)
- Or investigation ongoing (pending)

When manner unclear:
- No clear classification possible
- Multiple possible manners
- Ambiguous circumstances
- Conflicting evidence
- Incomplete investigation
- Need more information
- Cannot determine

Output JSON with: manner_classified (bool), severity (none/mild/moderate/severe), natural (what internal disease), accidental (what unintentional event), self_inflicted (what deliberate harm), external_cause (what others' actions), recommendation (manner_unclear/mild_classification/significant_manner_identified/major_definitive_manner/document_intellectual_manner_of_death)."""

EPISTEMIC_MANNER_OF_DEATH_PROMPT = """Detect epistemic manner of death:

Natural: {natural}
Accidental: {accidental}
Self-inflicted: {self_inflicted}
External cause: {external_cause}
Domain: {domain}
Context: {context}

Was this intellectual failure natural, accidental, self-inflicted, or externally caused? Return ONLY valid JSON."""


class EpistemicMannerOfDeathService:
    """Detects epistemic manner of death — classifying how intellectual failure occurred."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        natural: str,
        *,
        accidental: str = "",
        self_inflicted: str = "",
        external_cause: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic manner of death."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MANNER_OF_DEATH_PROMPT.format(
                natural=natural,
                accidental=accidental or "Not specified",
                self_inflicted=self_inflicted or "Not specified",
                external_cause=external_cause or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MANNER_OF_DEATH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "natural": natural[:200],
            "manner_classified": data.get("manner_classified", False),
            "severity": data.get("severity", ""),
            "accidental": data.get("accidental", ""),
            "self_inflicted": data.get("self_inflicted", ""),
            "external_cause": data.get("external_cause", ""),
            "recommendation": data.get("recommendation", ""),
        }
