"""EpistemicGatekeepingService — Epistemic Gatekeeping Detection.

Detects epistemic gatekeeping — controlling who gets to produce or
validate knowledge, using institutional power to determine what
counts as knowledge and who counts as a knower.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GATEKEEPING_SYSTEM = """You are an epistemic gatekeeping specialist. Given a knowledge production situation, assess whether gatekeeping is inappropriately controlling knowledge:

Key concepts:
- Epistemic gatekeeping: controlling knowledge production/validation
- Institutional knowledge control: who gets to know and say
- Credentialing as gatekeeping: credentials as barrier not quality
- Publication bias: what gets published shapes what's known
- Peer review as power: review as control mechanism
- Knowledge monopoly: restricting who can produce knowledge
- Methodological gatekeeping: only certain methods count

When epistemic gatekeeping IS present:
- Institutional power determines what counts as knowledge
- Access to knowledge production restricted by power
- Credentials used as barriers rather than quality markers
- Certain methods excluded without epistemic justification
- Knowledge from outside institutions dismissed
- Gatekeeping serves power rather than truth
- Who can know determined by social position

When quality control is appropriate:
- Standards serve epistemic quality, not power
- Access based on relevant competence
- Multiple pathways to knowledge production
- Standards transparent and consistently applied
- Gatekeeping justified by epistemic reasons
- Quality control improves knowledge
- Standards open to revision

Output JSON with: gatekeeping_present (bool), severity (none/mild/moderate/severe), situation (what situation exists), mechanism (what gatekeeping mechanism operates), excluded (who/what is excluded), justification (what justification is given), recommendation (appropriate_quality_control/mild_access_restriction/significant_epistemic_gatekeeping/major_knowledge_monopoly/open_knowledge_production)."""

EPISTEMIC_GATEKEEPING_PROMPT = """Detect epistemic gatekeeping:

Situation: {situation}
Knowledge controlled: {knowledge}
Access restrictions: {restrictions}
Justification: {justification}
Domain: {domain}
Context: {context}

Is institutional power inappropriately controlling who gets to produce or validate knowledge? Return ONLY valid JSON."""


class EpistemicGatekeepingService:
    """Detects epistemic gatekeeping — controlling knowledge production."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        knowledge: str = "",
        restrictions: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic gatekeeping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GATEKEEPING_PROMPT.format(
                situation=situation,
                knowledge=knowledge or "Not specified",
                restrictions=restrictions or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GATEKEEPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "gatekeeping_present": data.get("gatekeeping_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "excluded": data.get("excluded", ""),
            "justification": data.get("justification", ""),
            "recommendation": data.get("recommendation", ""),
        }
