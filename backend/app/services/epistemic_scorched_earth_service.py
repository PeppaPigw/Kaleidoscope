"""EpistemicScorchedEarthService — Epistemic Scorched Earth Detection.

Detects epistemic scorched earth — destroying shared epistemic
resources to prevent others from using them.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SCORCHED_EARTH_SYSTEM = """You are an epistemic scorched earth specialist. Given a knowledge environment, assess whether shared epistemic resources are being destroyed:

Key concepts:
- Epistemic scorched earth: destroying shared epistemic resources
- Knowledge destruction: deliberately destroying useful knowledge
- Trust erosion: deliberately eroding epistemic trust
- Discourse poisoning: poisoning shared discourse to make it unusable
- Evidence destruction: destroying evidence to prevent its use
- Norm destruction: destroying epistemic norms to prevent functioning
- Commons destruction: destroying epistemic commons

When epistemic scorched earth IS present:
- Shared epistemic resources deliberately destroyed
- Knowledge destroyed to prevent others' use
- Trust deliberately eroded to prevent cooperation
- Discourse poisoned to make it unusable
- Evidence destroyed to prevent conclusions
- Epistemic norms destroyed to prevent functioning
- Commons destroyed rather than shared

When natural epistemic change is present:
- Resources evolving through normal processes
- Knowledge updated through legitimate revision
- Trust adjusted based on evidence
- Discourse changing through genuine engagement
- Evidence superseded by better evidence
- Norms evolving through legitimate process
- Commons managed through collective decision

Output JSON with: scorched_earth_present (bool), severity (none/mild/moderate/severe), environment (what environment is affected), destruction (what is being destroyed), method (how destruction occurs), purpose (why destruction is pursued), recommendation (natural_change/mild_degradation/significant_epistemic_scorched_earth/major_commons_destruction/preserve_epistemic_resources)."""

EPISTEMIC_SCORCHED_EARTH_PROMPT = """Detect epistemic scorched earth:

Environment: {environment}
Destruction: {destruction}
Method: {method}
Purpose: {purpose}
Domain: {domain}
Context: {context}

Are shared epistemic resources being deliberately destroyed? Return ONLY valid JSON."""


class EpistemicScorchedEarthService:
    """Detects epistemic scorched earth — destroying shared epistemic resources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        environment: str,
        *,
        destruction: str = "",
        method: str = "",
        purpose: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic scorched earth."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SCORCHED_EARTH_PROMPT.format(
                environment=environment,
                destruction=destruction or "Not specified",
                method=method or "Not specified",
                purpose=purpose or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SCORCHED_EARTH_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "environment": environment[:200],
            "scorched_earth_present": data.get("scorched_earth_present", False),
            "severity": data.get("severity", ""),
            "destruction": data.get("destruction", ""),
            "method": data.get("method", ""),
            "purpose": data.get("purpose", ""),
            "recommendation": data.get("recommendation", ""),
        }
