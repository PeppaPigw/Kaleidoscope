"""EpistemicSuperconductivityService — Epistemic Superconductivity Detection.

Detects epistemic superconductivity — ideas flowing with zero resistance
below a critical temperature, enabling perfect transmission.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SUPERCONDUCTIVITY_SYSTEM = """You are an epistemic superconductivity specialist. Given an idea flow pattern, assess whether ideas flow with zero resistance below a critical threshold:

Key concepts:
- Epistemic superconductivity: zero resistance idea flow
- Critical temperature: threshold below which resistance vanishes
- Cooper pair: ideas pairing up to avoid resistance
- Meissner effect: expelling opposing fields
- Flux pinning: trapping ideas in specific positions
- Quench: sudden loss of superconductivity
- BCS theory: mechanism enabling zero resistance

When epistemic superconductivity IS present:
- Ideas flowing with zero resistance in certain conditions
- Threshold below which resistance vanishes
- Ideas pairing up to avoid intellectual friction
- Opposing intellectual fields being expelled
- Ideas trapped in specific positions by flux
- Sudden loss of zero-resistance state
- Mechanism enabling the frictionless flow

When normal resistance is present:
- Ideas encountering resistance in all conditions
- No threshold for resistance change
- Ideas moving independently with friction
- Opposing fields penetrating freely
- No flux pinning of ideas
- No sudden state changes
- Normal friction mechanisms operating

Output JSON with: superconductivity_present (bool), severity (none/mild/moderate/severe), critical_temperature (what threshold), cooper_pair (what pairing), meissner (what field expulsion), quench (what sudden loss), recommendation (normal_resistance/mild_superconductivity/significant_superconductivity/major_zero_resistance/maintain_critical_conditions)."""

EPISTEMIC_SUPERCONDUCTIVITY_PROMPT = """Detect epistemic superconductivity:

Critical temperature: {critical_temperature}
Cooper pair: {cooper_pair}
Meissner: {meissner}
Quench: {quench}
Domain: {domain}
Context: {context}

Are ideas flowing with zero resistance below a critical temperature, enabling perfect transmission? Return ONLY valid JSON."""


class EpistemicSuperconductivityService:
    """Detects epistemic superconductivity — zero resistance idea flow."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        critical_temperature: str,
        *,
        cooper_pair: str = "",
        meissner: str = "",
        quench: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic superconductivity."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SUPERCONDUCTIVITY_PROMPT.format(
                critical_temperature=critical_temperature,
                cooper_pair=cooper_pair or "Not specified",
                meissner=meissner or "Not specified",
                quench=quench or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SUPERCONDUCTIVITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "critical_temperature": critical_temperature[:200],
            "superconductivity_present": data.get("superconductivity_present", False),
            "severity": data.get("severity", ""),
            "cooper_pair": data.get("cooper_pair", ""),
            "meissner": data.get("meissner", ""),
            "quench": data.get("quench", ""),
            "recommendation": data.get("recommendation", ""),
        }
