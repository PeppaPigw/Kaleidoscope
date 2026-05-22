"""EpistemicChromosomalDeletionService — Epistemic Chromosomal Deletion Detection.

Detects epistemic chromosomal deletion — loss of entire intellectual segments
from lineage, creating gaps in inherited knowledge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CHROMOSOMAL_DELETION_SYSTEM = """You are an epistemic chromosomal deletion specialist. Given intellectual lineage gaps, assess whether entire segments have been lost:

Key concepts:
- Epistemic chromosomal deletion: loss of entire intellectual segments
- Contiguous gene syndrome: multiple adjacent functions lost together
- Haploinsufficiency: remaining copy insufficient
- Microdeletion: small but critical segment lost
- Terminal deletion: loss from end of intellectual chromosome
- Interstitial deletion: loss from middle of chromosome
- Ring chromosome: ends joining after terminal deletions

When epistemic chromosomal deletion IS present:
- Entire intellectual segments lost from lineage
- Multiple adjacent functions lost together
- Remaining copy insufficient for normal function
- Small but critical segments missing
- Loss from end of intellectual lineage
- Loss from middle of intellectual lineage
- Ends joining creating circular limitations

When complete lineage is present:
- All intellectual segments intact
- All adjacent functions present
- Both copies sufficient
- No critical segments missing
- Complete ends
- Complete middle
- Linear intact structure

Output JSON with: chromosomal_deletion_present (bool), severity (none/mild/moderate/severe), contiguous_gene_loss (what adjacent functions lost), haploinsufficiency (what remaining insufficiency), microdeletion (what small critical loss), deletion_location (what position), recommendation (complete_lineage/mild_deletion/significant_chromosomal_deletion/major_segment_loss/reconstruct_intellectual_lineage)."""

EPISTEMIC_CHROMOSOMAL_DELETION_PROMPT = """Detect epistemic chromosomal deletion:

Contiguous gene loss: {contiguous_gene_loss}
Haploinsufficiency: {haploinsufficiency}
Microdeletion: {microdeletion}
Deletion location: {deletion_location}
Domain: {domain}
Context: {context}

Have entire intellectual segments been lost from the lineage? Return ONLY valid JSON."""


class EpistemicChromosomalDeletionService:
    """Detects epistemic chromosomal deletion — loss of intellectual segments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        contiguous_gene_loss: str,
        *,
        haploinsufficiency: str = "",
        microdeletion: str = "",
        deletion_location: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic chromosomal deletion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CHROMOSOMAL_DELETION_PROMPT.format(
                contiguous_gene_loss=contiguous_gene_loss,
                haploinsufficiency=haploinsufficiency or "Not specified",
                microdeletion=microdeletion or "Not specified",
                deletion_location=deletion_location or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CHROMOSOMAL_DELETION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "contiguous_gene_loss": contiguous_gene_loss[:200],
            "chromosomal_deletion_present": data.get("chromosomal_deletion_present", False),
            "severity": data.get("severity", ""),
            "haploinsufficiency": data.get("haploinsufficiency", ""),
            "microdeletion": data.get("microdeletion", ""),
            "deletion_location": data.get("deletion_location", ""),
            "recommendation": data.get("recommendation", ""),
        }
