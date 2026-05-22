"""EpistemicMaxwellDemonService — Epistemic Maxwell's Demon Detection.

Detects epistemic Maxwell's demon — an intellectual gatekeeper that
appears to violate the second law by selectively filtering information.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_MAXWELL_DEMON_SYSTEM = """You are an epistemic Maxwell's demon specialist. Given an intellectual filtering pattern, assess whether selective gatekeeping appears to violate entropy:

Key concepts:
- Epistemic Maxwell's demon: selective filtering appearing to violate entropy
- Information cost: energy required to observe and decide
- Landauer's principle: erasing information generates heat
- Szilard engine: extracting work from single bit
- Measurement problem: observation itself has cost
- Feedback control: using information to reduce entropy
- Thermodynamic cost: hidden entropy generation

When epistemic Maxwell's demon IS present:
- Selective filtering appearing to create order from disorder
- Hidden cost of observation and decision-making
- Information erasure generating intellectual heat
- Extracting useful work from minimal information
- Observation itself having hidden costs
- Using information to reduce apparent entropy
- Hidden entropy generation elsewhere in system

When honest filtering is present:
- Filtering with acknowledged costs
- Visible cost of observation
- No hidden information erasure
- No apparent free energy extraction
- Observation costs accounted for
- Entropy reduction balanced by generation
- No hidden entropy elsewhere

Output JSON with: maxwell_demon_present (bool), severity (none/mild/moderate/severe), information_cost (what hidden observation cost), landauer (what erasure heat), feedback (what entropy reduction), hidden_entropy (what generation elsewhere), recommendation (honest_filtering/mild_demon/significant_maxwell_demon/major_entropy_violation/account_for_information_cost)."""

EPISTEMIC_MAXWELL_DEMON_PROMPT = """Detect epistemic Maxwell's demon:

Information cost: {information_cost}
Landauer: {landauer}
Feedback: {feedback}
Hidden entropy: {hidden_entropy}
Domain: {domain}
Context: {context}

Is an intellectual gatekeeper selectively filtering information in a way that appears to violate the second law? Return ONLY valid JSON."""


class EpistemicMaxwellDemonService:
    """Detects epistemic Maxwell's demon — selective filtering violating entropy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        information_cost: str,
        *,
        landauer: str = "",
        feedback: str = "",
        hidden_entropy: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic Maxwell's demon."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_MAXWELL_DEMON_PROMPT.format(
                information_cost=information_cost,
                landauer=landauer or "Not specified",
                feedback=feedback or "Not specified",
                hidden_entropy=hidden_entropy or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_MAXWELL_DEMON_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "information_cost": information_cost[:200],
            "maxwell_demon_present": data.get("maxwell_demon_present", False),
            "severity": data.get("severity", ""),
            "landauer": data.get("landauer", ""),
            "feedback": data.get("feedback", ""),
            "hidden_entropy": data.get("hidden_entropy", ""),
            "recommendation": data.get("recommendation", ""),
        }
