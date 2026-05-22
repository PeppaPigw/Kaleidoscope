"""EpistemicTaphonomyService — Epistemic Taphonomy Detection.

Detects epistemic taphonomy — the processes by which ideas become
preserved or destroyed after their initial creation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TAPHONOMY_SYSTEM = """You are an epistemic taphonomy specialist. Given an idea preservation pattern, assess how ideas are preserved or destroyed after creation:

Key concepts:
- Epistemic taphonomy: processes of idea preservation or destruction
- Preservation bias: some ideas preserved more than others
- Decay: ideas degrading after creation
- Fossilization: ideas becoming permanently preserved
- Diagenesis: ideas being altered during preservation
- Completeness: how much of original idea survives
- Taphonomic filter: what determines which ideas survive

When epistemic taphonomy IS present:
- Clear processes determining which ideas survive
- Some ideas preserved more readily than others
- Ideas degrading after their initial creation
- Some ideas becoming permanently preserved in record
- Ideas being altered during the preservation process
- Original ideas only partially surviving
- Filters determining which ideas make it into the record

When equal preservation is present:
- All ideas equally likely to survive
- No preservation bias
- Ideas not degrading after creation
- No permanent preservation needed
- Ideas remaining in original form
- Complete ideas surviving intact
- No filtering of which ideas survive

Output JSON with: taphonomy_present (bool), severity (none/mild/moderate/severe), preservation (what ideas are preserved), decay (what ideas decay), bias (what preservation bias exists), filter (what determines survival), recommendation (equal_preservation/mild_bias/significant_taphonomy/major_preservation_bias/account_for_preservation_bias)."""

EPISTEMIC_TAPHONOMY_PROMPT = """Detect epistemic taphonomy:

Preservation: {preservation}
Decay: {decay}
Bias: {bias}
Filter: {filter_type}
Domain: {domain}
Context: {context}

Are there processes determining which ideas are preserved or destroyed after creation? Return ONLY valid JSON."""


class EpistemicTaphonomyService:
    """Detects epistemic taphonomy — processes of idea preservation or destruction."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        preservation: str,
        *,
        decay: str = "",
        bias: str = "",
        filter_type: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic taphonomy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TAPHONOMY_PROMPT.format(
                preservation=preservation,
                decay=decay or "Not specified",
                bias=bias or "Not specified",
                filter_type=filter_type or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TAPHONOMY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "preservation": preservation[:200],
            "taphonomy_present": data.get("taphonomy_present", False),
            "severity": data.get("severity", ""),
            "decay": data.get("decay", ""),
            "bias": data.get("bias", ""),
            "filter": data.get("filter", ""),
            "recommendation": data.get("recommendation", ""),
        }
