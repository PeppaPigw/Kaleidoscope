"""StrategicVaguenessService — Strategic Vagueness Detection.

Detects strategic vagueness — deliberate use of vague language
to avoid commitment, accountability, or falsifiability while
appearing to communicate substantively.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

STRATEGIC_VAGUENESS_SYSTEM = """You are a strategic vagueness specialist. Given a communication, assess whether vagueness is being used strategically to avoid commitment:

Key concepts:
- Strategic ambiguity: deliberate vagueness serving speaker's interests
- Commitment avoidance: language that sounds definitive but commits to nothing
- Accountability evasion: vagueness making it impossible to be held accountable
- Weasel language: qualifiers that empty statements of content
- Plausible deniability: vagueness allowing multiple interpretations
- Pseudo-specificity: appearing specific while remaining vague
- Unfalsifiable vagueness: claims too vague to be wrong

When strategic vagueness IS present:
- Language deliberately vague to avoid commitment
- Statements sound meaningful but commit to nothing specific
- Accountability impossible due to vagueness
- Multiple contradictory interpretations possible
- Vagueness serves speaker's interests
- Specificity avoided where it would create accountability
- Pseudo-specific language masking actual vagueness

When vagueness is appropriate:
- Genuine uncertainty warrants imprecise language
- Early-stage thinking appropriately tentative
- Complexity genuinely resists simple formulation
- Vagueness acknowledged rather than hidden
- Specificity provided where possible
- Commitment made where evidence supports it
- Vagueness not serving strategic purpose

Output JSON with: vagueness_present (bool), severity (none/mild/moderate/severe), communication (what is communicated), vague_elements (what is strategically vague), purpose (what strategic purpose vagueness serves), specific_alternative (what specific statement could replace it), recommendation (appropriate_tentativeness/mild_strategic_vagueness/significant_commitment_avoidance/major_accountability_evasion/demand_specificity)."""

STRATEGIC_VAGUENESS_PROMPT = """Detect strategic vagueness:

Communication: {communication}
Claims made: {claims}
Commitments: {commitments}
Accountability: {accountability}
Domain: {domain}
Context: {context}

Is vagueness being used strategically to avoid commitment or accountability? Return ONLY valid JSON."""


class StrategicVaguenessService:
    """Detects strategic vagueness — deliberate vagueness avoiding commitment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        communication: str,
        *,
        claims: str = "",
        commitments: str = "",
        accountability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect strategic vagueness."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=STRATEGIC_VAGUENESS_PROMPT.format(
                communication=communication,
                claims=claims or "Not specified",
                commitments=commitments or "Not specified",
                accountability=accountability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=STRATEGIC_VAGUENESS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "communication": communication[:200],
            "vagueness_present": data.get("vagueness_present", False),
            "severity": data.get("severity", ""),
            "vague_elements": data.get("vague_elements", ""),
            "purpose": data.get("purpose", ""),
            "specific_alternative": data.get("specific_alternative", ""),
            "recommendation": data.get("recommendation", ""),
        }
