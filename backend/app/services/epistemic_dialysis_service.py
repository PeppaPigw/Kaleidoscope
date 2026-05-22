"""EpistemicDialysisService — Epistemic Dialysis Detection.

Detects epistemic dialysis — artificial external filtration of ideas
when natural intellectual filtering systems have failed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DIALYSIS_SYSTEM = """You are an epistemic dialysis specialist. Given an intellectual system with failed filtration, assess whether artificial external filtering is needed:

Key concepts:
- Epistemic dialysis: artificial external filtration when natural systems fail
- Hemodialysis: external machine filtering intellectual blood
- Peritoneal dialysis: using internal membrane with external solution
- Dialysate: solution used to draw out waste ideas
- Clearance: rate of waste removal
- Uremia: toxic buildup from failed filtration
- Vascular access: connection point for external filtering

When epistemic dialysis IS present:
- Artificial external filtration compensating for failure
- External systems filtering intellectual content
- Internal membranes used with external solutions
- Solutions drawing out waste ideas
- Measurable rate of waste removal
- Toxic buildup from failed natural filtration
- Connection points for external filtering systems

When healthy filtration is present:
- Natural filtration working properly
- No external systems needed
- Internal membranes functioning alone
- No external solutions required
- Natural clearance adequate
- No toxic buildup
- No external access needed

Output JSON with: dialysis_present (bool), severity (none/mild/moderate/severe), hemodialysis (what external machine filtering), peritoneal (what internal membrane use), uremia (what toxic buildup), clearance (what removal rate), recommendation (healthy_filtration/mild_dialysis/significant_dialysis/major_filtration_failure/restore_natural_filtration)."""

EPISTEMIC_DIALYSIS_PROMPT = """Detect epistemic dialysis:

Hemodialysis: {hemodialysis}
Peritoneal: {peritoneal}
Uremia: {uremia}
Clearance: {clearance}
Domain: {domain}
Context: {context}

Is artificial external filtration needed because natural intellectual filtering has failed? Return ONLY valid JSON."""


class EpistemicDialysisService:
    """Detects epistemic dialysis — artificial external filtration for failed systems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        hemodialysis: str,
        *,
        peritoneal: str = "",
        uremia: str = "",
        clearance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic dialysis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DIALYSIS_PROMPT.format(
                hemodialysis=hemodialysis,
                peritoneal=peritoneal or "Not specified",
                uremia=uremia or "Not specified",
                clearance=clearance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DIALYSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "hemodialysis": hemodialysis[:200],
            "dialysis_present": data.get("dialysis_present", False),
            "severity": data.get("severity", ""),
            "peritoneal": data.get("peritoneal", ""),
            "uremia": data.get("uremia", ""),
            "clearance": data.get("clearance", ""),
            "recommendation": data.get("recommendation", ""),
        }
