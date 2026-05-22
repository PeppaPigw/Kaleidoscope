"""EpistemicParadigmBereavementService — Epistemic Paradigm Bereavement Detection.

Detects epistemic paradigm bereavement — bereavement over abandoned
paradigms that once structured one's intellectual life.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_PARADIGM_BEREAVEMENT_SYSTEM = """You are an epistemic paradigm bereavement specialist. Given bereavement over abandoned paradigms, assess paradigm bereavement:

Key concepts:
- Epistemic paradigm bereavement: bereavement over abandoned paradigms
- Investment loss: years invested in now-abandoned framework
- Community severance: cut off from paradigm's community
- Skill obsolescence: expertise in dead paradigm worthless
- Identity reconstruction: rebuilding self after paradigm death
- Sunk cost grief: mourning irrecoverable investment
- Intellectual homelessness: between paradigms with no home

When epistemic paradigm bereavement IS present:
- Bereavement over abandoned paradigms
- Years invested lost
- Cut off from community
- Expertise now worthless
- Rebuilding self
- Mourning investment
- Between paradigms homeless

When no paradigm bereavement:
- Paradigms evolving naturally
- Investment transferable
- Community adapting
- Expertise translating
- Identity continuous
- Investment building
- Paradigm home stable

Output JSON with: paradigm_bereavement_detected (bool), severity (none/mild/moderate/severe), investment_loss (what years invested in), community_severance (what cut off from), skill_obsolescence (what expertise now worthless), intellectual_homelessness (what between), recommendation (no_paradigm_bereavement/mild_transition_support/significant_bereavement_processing/major_intensive_paradigm_grief/emergency_severe_intellectual_homelessness)."""

EPISTEMIC_PARADIGM_BEREAVEMENT_PROMPT = """Detect epistemic paradigm bereavement:

Investment loss: {investment_loss}
Community severance: {community_severance}
Skill obsolescence: {skill_obsolescence}
Intellectual homelessness: {intellectual_homelessness}
Domain: {domain}
Context: {context}

Is there bereavement over abandoned paradigms? Return ONLY valid JSON."""


class EpistemicParadigmBereavementService:
    """Detects epistemic paradigm bereavement — bereavement over abandoned paradigms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investment_loss: str,
        *,
        community_severance: str = "",
        skill_obsolescence: str = "",
        intellectual_homelessness: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic paradigm bereavement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_PARADIGM_BEREAVEMENT_PROMPT.format(
                investment_loss=investment_loss,
                community_severance=community_severance or "Not specified",
                skill_obsolescence=skill_obsolescence or "Not specified",
                intellectual_homelessness=intellectual_homelessness or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_PARADIGM_BEREAVEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investment_loss": investment_loss[:200],
            "paradigm_bereavement_detected": data.get("paradigm_bereavement_detected", False),
            "severity": data.get("severity", ""),
            "community_severance": data.get("community_severance", ""),
            "skill_obsolescence": data.get("skill_obsolescence", ""),
            "intellectual_homelessness": data.get("intellectual_homelessness", ""),
            "recommendation": data.get("recommendation", ""),
        }
