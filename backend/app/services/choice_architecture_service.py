"""ChoiceArchitectureService — Choice Architecture Detection.

Detects manipulative choice architecture — when the way choices
are structured, ordered, or presented is designed to steer
decisions toward a particular outcome rather than facilitate
informed choice.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CHOICE_ARCHITECTURE_SYSTEM = """You are a choice architecture specialist. Given a decision context, assess whether choice presentation is manipulative:

Key concepts:
- Choice architecture: how options are structured and presented
- Nudging: subtle design choices that influence behavior
- Dark patterns: manipulative design that tricks users
- Libertarian paternalism: preserving choice while steering
- Asymmetric paternalism: helping those who need it without harming others
- Sludge: friction added to discourage certain choices
- Boost: helping people make better decisions vs nudging them

When choice architecture IS manipulative:
- Options structured to steer toward predetermined choice
- Friction added to disfavored options (sludge)
- Favorable option made easiest to select
- Information asymmetry between options
- Decoy options added to make target look better
- Time pressure or scarcity cues manufactured
- Comparison made difficult for disfavored options

When choice architecture is appropriate:
- Options presented clearly and comparably
- Equal friction for all options
- Information provided symmetrically
- No manufactured urgency or scarcity
- Defaults chosen for user benefit, not provider benefit
- Easy to compare all options
- Architecture helps informed choice rather than steering

Output JSON with: manipulative (bool), severity (none/mild/moderate/severe), architecture (how choices are structured), steering_toward (what option is being favored), techniques (what manipulation techniques are used), user_benefit (whether architecture serves user or provider), recommendation (helpful_architecture/mild_nudging/significant_manipulation/major_dark_pattern/redesign_for_informed_choice)."""

CHOICE_ARCHITECTURE_PROMPT = """Detect manipulative choice architecture:

Decision context: {decision}
Options presented: {options}
Presentation method: {presentation}
Friction patterns: {friction}
Domain: {domain}
Context: {context}

Is the choice architecture manipulative rather than helpful? Return ONLY valid JSON."""


class ChoiceArchitectureService:
    """Detects manipulative choice architecture."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        options: str = "",
        presentation: str = "",
        friction: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect manipulative choice architecture."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CHOICE_ARCHITECTURE_PROMPT.format(
                decision=decision,
                options=options or "Not specified",
                presentation=presentation or "Not specified",
                friction=friction or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CHOICE_ARCHITECTURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "manipulative": data.get("manipulative", False),
            "severity": data.get("severity", ""),
            "steering_toward": data.get("steering_toward", ""),
            "techniques": data.get("techniques", ""),
            "user_benefit": data.get("user_benefit", ""),
            "recommendation": data.get("recommendation", ""),
        }
