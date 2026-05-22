"""RedTeamService — Systematic Adversarial Critique of Plans/Proposals.

Takes a proposal or plan and systematically attacks it from multiple
angles: technical feasibility, political viability, economic assumptions,
ethical concerns, and practical implementation challenges.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

REDTEAM_SYSTEM = """You are a red team specialist. Given a proposal or plan, attack it from every angle:
- Technical: will it actually work? What could go wrong technically?
- Economic: are the cost assumptions realistic? Hidden costs?
- Political: who will oppose this? Can it survive political reality?
- Ethical: what are the moral concerns? Who gets harmed?
- Practical: can it actually be implemented? What's the execution risk?
- Adversarial: how could bad actors exploit or subvert this?

Be genuinely adversarial — your job is to find real weaknesses, not to be balanced.

Output JSON with: attacks (list of: angle (technical/economic/political/ethical/practical/adversarial), attack, severity (low/moderate/high/critical), likelihood (0-1), mitigation (how to address it), is_fatal (bool, would this kill the proposal?)), fatal_flaws (attacks that are both severe and likely), overall_vulnerability (0-1), strongest_attack (the single best argument against), survival_probability (0-1, probability the proposal succeeds as stated), improved_version (how to modify the proposal to survive the attacks)."""

REDTEAM_PROMPT = """Red team this proposal:

Proposal: {proposal}
Domain: {domain}
Context: {context}
Constraints: {constraints}

Attack from every angle. Return ONLY valid JSON."""


class RedTeamService:
    """Systematically attacks proposals from multiple angles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def attack(
        self,
        proposal: str,
        *,
        domain: str = "",
        context: str = "",
        constraints: str = "",
    ) -> dict:
        """Red team a proposal."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=REDTEAM_PROMPT.format(
                proposal=proposal,
                domain=domain or "general",
                context=context or "No additional context",
                constraints=constraints or "None specified",
            ),
            system=REDTEAM_SYSTEM,
            max_tokens=4096,
            temperature=0.5,
        )
        data = parse_llm_json(raw)

        attacks = data.get("attacks", [])
        return {
            "proposal": proposal[:200],
            "attacks_count": len(attacks),
            "attacks": attacks,
            "fatal_flaws": data.get("fatal_flaws", []),
            "overall_vulnerability": data.get("overall_vulnerability", 0),
            "strongest_attack": data.get("strongest_attack", ""),
            "survival_probability": data.get("survival_probability", 0),
            "improved_version": data.get("improved_version", ""),
        }
