"""EpistemicEndemicService — Epistemic Endemic Detection.

Detects epistemic endemics — harmful beliefs that have become
permanently established in a population's baseline thinking.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ENDEMIC_SYSTEM = """You are an epistemic endemic specialist. Given a belief pattern, assess whether harmful beliefs have become permanently established in baseline thinking:

Key concepts:
- Epistemic endemic: harmful belief permanently in baseline thinking
- Permanent establishment: belief now part of background assumptions
- Baseline integration: harmful belief integrated into normal thinking
- Invisible harm: harm invisible because belief is normalized
- Cultural embedding: harmful belief embedded in culture
- Generational transmission: harmful belief transmitted across generations
- Resistance to eradication: belief resistant to removal

When epistemic endemic IS present:
- Harmful beliefs permanently established in baseline thinking
- Belief now part of unquestioned background assumptions
- Harmful belief integrated into normal everyday thinking
- Harm invisible because belief is completely normalized
- Harmful belief deeply embedded in cultural fabric
- Harmful belief transmitted across generations automatically
- Belief resistant to eradication efforts

When healthy baseline is present:
- Baseline beliefs regularly examined and updated
- Background assumptions questioned periodically
- Normal thinking based on evidence
- Potential harms visible and addressed
- Cultural beliefs examined critically
- Generational transmission includes critical evaluation
- Beliefs updated when evidence warrants

Output JSON with: endemic_present (bool), severity (none/mild/moderate/severe), belief (what belief is endemic), establishment (how it became established), invisibility (how harm is invisible), resistance (resistance to eradication), recommendation (healthy_baseline/mild_normalization/significant_endemic/major_permanent_establishment/surface_and_examine)."""

EPISTEMIC_ENDEMIC_PROMPT = """Detect epistemic endemic:

Belief: {belief}
Establishment: {establishment}
Invisibility: {invisibility}
Resistance: {resistance}
Domain: {domain}
Context: {context}

Has this harmful belief become permanently established in baseline thinking? Return ONLY valid JSON."""


class EpistemicEndemicService:
    """Detects epistemic endemics — harmful beliefs permanently in baseline thinking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        belief: str,
        *,
        establishment: str = "",
        invisibility: str = "",
        resistance: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic endemic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ENDEMIC_PROMPT.format(
                belief=belief,
                establishment=establishment or "Not specified",
                invisibility=invisibility or "Not specified",
                resistance=resistance or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ENDEMIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "belief": belief[:200],
            "endemic_present": data.get("endemic_present", False),
            "severity": data.get("severity", ""),
            "establishment": data.get("establishment", ""),
            "invisibility": data.get("invisibility", ""),
            "resistance": data.get("resistance", ""),
            "recommendation": data.get("recommendation", ""),
        }
