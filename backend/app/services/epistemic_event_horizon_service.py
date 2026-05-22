"""EpistemicEventHorizonService — Epistemic Event Horizon Detection.

Detects epistemic event horizon — a boundary beyond which intellectual
information cannot escape, creating a point of no return in reasoning.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EVENT_HORIZON_SYSTEM = """You are an epistemic event horizon specialist. Given an intellectual boundary, assess whether information cannot escape beyond it:

Key concepts:
- Epistemic event horizon: boundary beyond which information cannot escape
- Schwarzschild radius: size of the no-return boundary
- Information paradox: what happens to trapped information
- Hawking radiation: slow leakage from the boundary
- Singularity: point of infinite density inside
- Penrose diagram: mapping the causal structure
- Firewall: violent boundary experience

When epistemic event horizon IS present:
- Boundary beyond which information cannot escape
- Definite size of the no-return region
- Trapped information with uncertain fate
- Slow leakage of degraded information
- Point of infinite intellectual density inside
- Causal structure preventing escape
- Violent experience at the boundary

When open boundary is present:
- No boundary trapping information
- No no-return region
- Information freely flowing in all directions
- No leakage needed since nothing trapped
- No singularity
- Open causal structure
- Smooth boundary experience

Output JSON with: event_horizon_present (bool), severity (none/mild/moderate/severe), schwarzschild (what boundary size), information_paradox (what trapped fate), hawking (what slow leakage), singularity (what infinite density), recommendation (open_boundary/mild_horizon/significant_event_horizon/major_information_trap/extract_hawking_radiation)."""

EPISTEMIC_EVENT_HORIZON_PROMPT = """Detect epistemic event horizon:

Schwarzschild: {schwarzschild}
Information paradox: {information_paradox}
Hawking: {hawking}
Singularity: {singularity}
Domain: {domain}
Context: {context}

Is there a boundary beyond which intellectual information cannot escape, creating a point of no return? Return ONLY valid JSON."""


class EpistemicEventHorizonService:
    """Detects epistemic event horizon — boundary trapping information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        schwarzschild: str,
        *,
        information_paradox: str = "",
        hawking: str = "",
        singularity: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic event horizon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EVENT_HORIZON_PROMPT.format(
                schwarzschild=schwarzschild,
                information_paradox=information_paradox or "Not specified",
                hawking=hawking or "Not specified",
                singularity=singularity or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EVENT_HORIZON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "schwarzschild": schwarzschild[:200],
            "event_horizon_present": data.get("event_horizon_present", False),
            "severity": data.get("severity", ""),
            "information_paradox": data.get("information_paradox", ""),
            "hawking": data.get("hawking", ""),
            "singularity": data.get("singularity", ""),
            "recommendation": data.get("recommendation", ""),
        }
