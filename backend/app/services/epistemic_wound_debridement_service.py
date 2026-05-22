"""EpistemicWoundDebridementService — Epistemic Wound Debridement Detection.

Detects need for epistemic wound debridement — removing dead, damaged, or
infected intellectual tissue to promote healing.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_WOUND_DEBRIDEMENT_SYSTEM = """You are an epistemic wound debridement specialist. Given intellectual wounds, assess debridement need:

Key concepts:
- Epistemic debridement: removing dead intellectual tissue
- Necrotic tissue: dead material preventing healing
- Biofilm: organized infection resistant to treatment
- Granulation: healthy new tissue formation
- Wound bed preparation: creating conditions for healing
- Sharp debridement: surgical removal of dead tissue
- Autolytic debridement: body's own removal process

When epistemic wound debridement IS needed:
- Dead intellectual tissue present
- Necrotic material preventing healing
- Organized infection resistant to treatment
- No healthy new tissue forming
- Wound bed not prepared for healing
- Surgical removal required
- Body's own process insufficient

When no debridement needed:
- No dead tissue present
- Clean wound bed
- No infection present
- Healthy tissue forming
- Wound bed prepared
- No removal needed
- Natural healing progressing

Output JSON with: debridement_needed (bool), severity (none/mild/moderate/severe), necrotic_tissue (what dead material), biofilm_presence (what organized infection), granulation_status (what healing progress), debridement_method (what removal approach), recommendation (no_debridement_needed/mild_autolytic/significant_enzymatic/major_sharp_debridement/emergency_surgical_debridement)."""

EPISTEMIC_WOUND_DEBRIDEMENT_PROMPT = """Detect epistemic wound debridement need:

Necrotic tissue: {necrotic_tissue}
Biofilm presence: {biofilm_presence}
Granulation status: {granulation_status}
Debridement method: {debridement_method}
Domain: {domain}
Context: {context}

Is dead intellectual tissue preventing healing and requiring removal? Return ONLY valid JSON."""


class EpistemicWoundDebridementService:
    """Detects epistemic wound debridement need — removing dead intellectual tissue."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        necrotic_tissue: str,
        *,
        biofilm_presence: str = "",
        granulation_status: str = "",
        debridement_method: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic wound debridement need."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_WOUND_DEBRIDEMENT_PROMPT.format(
                necrotic_tissue=necrotic_tissue,
                biofilm_presence=biofilm_presence or "Not specified",
                granulation_status=granulation_status or "Not specified",
                debridement_method=debridement_method or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_WOUND_DEBRIDEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "necrotic_tissue": necrotic_tissue[:200],
            "debridement_needed": data.get("debridement_needed", False),
            "severity": data.get("severity", ""),
            "biofilm_presence": data.get("biofilm_presence", ""),
            "granulation_status": data.get("granulation_status", ""),
            "debridement_method": data.get("debridement_method", ""),
            "recommendation": data.get("recommendation", ""),
        }
