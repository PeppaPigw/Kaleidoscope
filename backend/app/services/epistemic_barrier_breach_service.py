"""EpistemicBarrierBreachService — Epistemic Barrier Breach Detection.

Detects epistemic barrier breach — breakdown of intellectual skin allowing
unfiltered external input to penetrate without proper screening.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_BARRIER_BREACH_SYSTEM = """You are an epistemic barrier breach specialist. Given intellectual boundaries, assess whether breakdown allows unfiltered input:

Key concepts:
- Epistemic barrier breach: breakdown allowing unfiltered external input
- Stratum corneum failure: outermost protective layer compromised
- Transepidermal water loss: internal resources leaking out
- Pathogen entry: harmful ideas entering through breach
- Tight junction disruption: connections between barrier cells failing
- Inflammatory response: reaction to breach
- Barrier repair: restoring protective function

When epistemic barrier breach IS present:
- Breakdown of intellectual skin allowing unfiltered input
- Outermost protective layer compromised
- Internal intellectual resources leaking outward
- Harmful ideas entering through the breach
- Connections between barrier elements failing
- Inflammatory reaction to the breach
- Need for barrier restoration

When healthy barrier is present:
- Intact intellectual boundary
- Strong outermost layer
- No resource leakage
- Harmful ideas screened out
- Strong inter-element connections
- No inflammatory response
- No repair needed

Output JSON with: barrier_breach_present (bool), severity (none/mild/moderate/severe), stratum_corneum_failure (what outer layer compromise), transepidermal_loss (what resource leakage), pathogen_entry (what harmful penetration), tight_junction_disruption (what connection failure), recommendation (healthy_barrier/mild_breach/significant_barrier_breach/major_boundary_breakdown/restore_intellectual_barrier)."""

EPISTEMIC_BARRIER_BREACH_PROMPT = """Detect epistemic barrier breach:

Stratum corneum failure: {stratum_corneum_failure}
Transepidermal loss: {transepidermal_loss}
Pathogen entry: {pathogen_entry}
Tight junction disruption: {tight_junction_disruption}
Domain: {domain}
Context: {context}

Has the intellectual boundary broken down, allowing unfiltered external input? Return ONLY valid JSON."""


class EpistemicBarrierBreachService:
    """Detects epistemic barrier breach — boundary breakdown allowing unfiltered input."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        stratum_corneum_failure: str,
        *,
        transepidermal_loss: str = "",
        pathogen_entry: str = "",
        tight_junction_disruption: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic barrier breach."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_BARRIER_BREACH_PROMPT.format(
                stratum_corneum_failure=stratum_corneum_failure,
                transepidermal_loss=transepidermal_loss or "Not specified",
                pathogen_entry=pathogen_entry or "Not specified",
                tight_junction_disruption=tight_junction_disruption or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_BARRIER_BREACH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "stratum_corneum_failure": stratum_corneum_failure[:200],
            "barrier_breach_present": data.get("barrier_breach_present", False),
            "severity": data.get("severity", ""),
            "transepidermal_loss": data.get("transepidermal_loss", ""),
            "pathogen_entry": data.get("pathogen_entry", ""),
            "tight_junction_disruption": data.get("tight_junction_disruption", ""),
            "recommendation": data.get("recommendation", ""),
        }
