"""EpistemicTsunamiService — Epistemic Tsunami Detection.

Detects epistemic tsunamis — overwhelming waves of information
destroying existing knowledge structures.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TSUNAMI_SYSTEM = """You are an epistemic tsunami specialist. Given an information environment, assess whether overwhelming waves of information are destroying existing structures:

Key concepts:
- Epistemic tsunami: overwhelming wave of information
- Structure destruction: existing knowledge structures destroyed
- Information overwhelm: overwhelmed by volume of information
- Framework collapse: frameworks collapsing under information weight
- Recovery difficulty: difficulty recovering after overwhelm
- Warning signs: signs of approaching information tsunami
- Aftermath rebuilding: rebuilding after destruction

When epistemic tsunami IS present:
- Overwhelming wave of information destroying structures
- Existing knowledge structures destroyed by volume
- Overwhelmed by sheer volume of information
- Frameworks collapsing under information weight
- Difficulty recovering from information overwhelm
- Warning signs of approaching overwhelm present
- Need to rebuild after destruction

When manageable influx is present:
- Information arriving at manageable rate
- Existing structures accommodating new information
- Volume manageable with current frameworks
- Frameworks adapting to new information
- Recovery not needed as structures intact
- No warning signs of overwhelm
- Integration rather than destruction

Output JSON with: tsunami_present (bool), severity (none/mild/moderate/severe), environment (what environment is affected), wave (what information wave exists), destruction (what structures are destroyed), recovery (what recovery is needed), recommendation (manageable_influx/mild_overwhelm/significant_tsunami/major_structure_destruction/build_resilient_frameworks)."""

EPISTEMIC_TSUNAMI_PROMPT = """Detect epistemic tsunami:

Environment: {environment}
Wave: {wave}
Destruction: {destruction}
Recovery: {recovery}
Domain: {domain}
Context: {context}

Is an overwhelming wave of information destroying existing knowledge structures? Return ONLY valid JSON."""


class EpistemicTsunamiService:
    """Detects epistemic tsunamis — overwhelming information destroying structures."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        wave: str = "",
        destruction: str = "",
        recovery: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tsunami."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TSUNAMI_PROMPT.format(
                environment=environment,
                wave=wave or "Not specified",
                destruction=destruction or "Not specified",
                recovery=recovery or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TSUNAMI_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "tsunami_present": data.get("tsunami_present", False),
            "severity": data.get("severity", ""),
            "wave": data.get("wave", ""),
            "destruction": data.get("destruction", ""),
            "recovery": data.get("recovery", ""),
            "recommendation": data.get("recommendation", ""),
        }
