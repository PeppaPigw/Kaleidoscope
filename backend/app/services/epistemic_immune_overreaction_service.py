"""EpistemicImmuneOverreactionService — Epistemic Immune Overreaction Detection.

Detects epistemic immune overreaction — disproportionate rejection
of benign new ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_IMMUNE_OVERREACTION_SYSTEM = """You are an epistemic immune overreaction specialist. Given a knowledge system's response to new ideas, assess whether rejection is disproportionate:

Key concepts:
- Epistemic immune overreaction: disproportionate rejection of benign ideas
- Overprotection: protecting against non-threats
- Novelty rejection: rejecting ideas simply because they are new
- Threat inflation: inflating threat level of benign ideas
- Defensive excess: excessive defensive response
- Innovation suppression: suppressing innovation through overreaction
- False alarm: treating benign ideas as dangerous

When epistemic immune overreaction IS present:
- Disproportionate rejection of benign new ideas
- Protecting against ideas that pose no threat
- Rejecting ideas simply because they are new
- Inflating threat level of benign ideas
- Excessive defensive response to novelty
- Suppressing innovation through overreaction
- Treating benign ideas as if dangerous

When appropriate caution is present:
- Rejection proportionate to actual threat
- Protection targeted at genuine threats
- New ideas evaluated on merits
- Threat assessment accurate
- Defensive response proportionate
- Innovation welcomed with appropriate scrutiny
- Genuine threats correctly identified

Output JSON with: overreaction_present (bool), severity (none/mild/moderate/severe), system (what system overreacts), idea (what idea is rejected), threat_level (actual vs perceived threat), proportionality (how disproportionate), recommendation (appropriate_caution/mild_overreaction/significant_immune_overreaction/major_innovation_suppression/calibrate_response)."""

EPISTEMIC_IMMUNE_OVERREACTION_PROMPT = """Detect epistemic immune overreaction:

System: {system}
Idea: {idea}
Threat level: {threat_level}
Proportionality: {proportionality}
Domain: {domain}
Context: {context}

Is rejection of new ideas disproportionate to actual threat? Return ONLY valid JSON."""


class EpistemicImmuneOverreactionService:
    """Detects epistemic immune overreaction — disproportionate rejection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        system: str,
        *,
        idea: str = "",
        threat_level: str = "",
        proportionality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic immune overreaction."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_IMMUNE_OVERREACTION_PROMPT.format(
                system=system,
                idea=idea or "Not specified",
                threat_level=threat_level or "Not specified",
                proportionality=proportionality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_IMMUNE_OVERREACTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "system": system[:200],
            "overreaction_present": data.get("overreaction_present", False),
            "severity": data.get("severity", ""),
            "idea": data.get("idea", ""),
            "threat_level": data.get("threat_level", ""),
            "proportionality": data.get("proportionality", ""),
            "recommendation": data.get("recommendation", ""),
        }
