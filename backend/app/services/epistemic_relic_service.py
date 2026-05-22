"""EpistemicRelicService — Epistemic Relic Detection.

Detects epistemic relics — outdated knowledge artifacts that
persist in current thinking without serving current needs.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_RELIC_SYSTEM = """You are an epistemic relic specialist. Given a knowledge artifact, assess whether it persists without serving current needs:

Key concepts:
- Epistemic relic: outdated knowledge persisting without purpose
- Vestigial knowledge: knowledge that no longer serves function
- Anachronistic belief: belief from another era persisting
- Functional obsolescence: knowledge functionally obsolete
- Inertial persistence: persisting through inertia not utility
- Tradition without function: maintained by tradition not need
- Cognitive archaeology: identifying relics in current thinking

When epistemic relic IS present:
- Outdated knowledge persisting without serving current needs
- Knowledge that no longer serves any function
- Beliefs from another era persisting inappropriately
- Knowledge functionally obsolete but still present
- Persisting through inertia rather than utility
- Maintained by tradition rather than need
- Identifiable as relic from earlier thinking

When living knowledge is present:
- Knowledge actively serving current needs
- Knowledge with clear current function
- Beliefs appropriate to current context
- Knowledge functionally relevant
- Maintained because of ongoing utility
- Serving genuine current needs
- Part of active current thinking

Output JSON with: relic_present (bool), severity (none/mild/moderate/severe), artifact (what knowledge is a relic), era (what era it comes from), obsolescence (why it is obsolete), persistence (why it persists), recommendation (living_knowledge/mild_anachronism/significant_relic/major_vestigial_persistence/retire_or_update)."""

EPISTEMIC_RELIC_PROMPT = """Detect epistemic relic:

Artifact: {artifact}
Era: {era}
Obsolescence: {obsolescence}
Persistence: {persistence}
Domain: {domain}
Context: {context}

Is this outdated knowledge persisting without serving current needs? Return ONLY valid JSON."""


class EpistemicRelicService:
    """Detects epistemic relics — outdated knowledge persisting without purpose."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        artifact: str,
        *,
        era: str = "",
        obsolescence: str = "",
        persistence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic relic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_RELIC_PROMPT.format(
                artifact=artifact,
                era=era or "Not specified",
                obsolescence=obsolescence or "Not specified",
                persistence=persistence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_RELIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "artifact": artifact[:200],
            "relic_present": data.get("relic_present", False),
            "severity": data.get("severity", ""),
            "era": data.get("era", ""),
            "obsolescence": data.get("obsolescence", ""),
            "persistence": data.get("persistence", ""),
            "recommendation": data.get("recommendation", ""),
        }
