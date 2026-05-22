"""DarkPatternService — Dark Pattern Detection.

Detects dark patterns — deceptive design choices in communication,
interfaces, or processes that trick people into unintended actions
or decisions. The design exploits cognitive biases and psychological
vulnerabilities rather than serving the user's interests.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DARK_PATTERN_SYSTEM = """You are a dark pattern specialist. Given a design or communication choice, assess whether it exploits cognitive biases to trick people into unintended actions:

Key concepts:
- Dark pattern: deceptive design exploiting psychological vulnerabilities
- Misdirection: drawing attention away from important information
- Hidden costs: concealing true costs until commitment is made
- Forced continuity: making it hard to cancel or opt out
- Confirmshaming: using guilt to manipulate choices
- Roach motel: easy to get in, hard to get out
- Trick questions: confusing wording that leads to unintended choices
- Disguised ads: content that looks informative but is promotional

When dark pattern IS present:
- Design makes the undesired choice easier than the desired one
- Important information is hidden or de-emphasized
- Opt-out is significantly harder than opt-in
- Emotional manipulation replaces informed choice
- The design benefits the designer at the user's expense
- Confusion is a feature, not a bug
- Default settings exploit inertia against user interests

When persuasive design IS appropriate:
- The design serves the user's stated interests
- Information is presented clearly and completely
- Both options are equally accessible
- Defaults reflect genuine user preferences
- The design helps users achieve their own goals
- Persuasion is transparent, not deceptive
- Users can easily reverse their choices

Output JSON with: dark_pattern_present (bool), severity (none/mild/moderate/severe), design (what design choice is analyzed), pattern_type (what type of dark pattern), exploitation (what cognitive bias is exploited), user_interest (what would serve the user), designer_interest (what serves the designer), recommendation (design_appropriate/mild_nudge/significant_dark_pattern/major_deceptive_design/redesign_for_user_interest)."""

DARK_PATTERN_PROMPT = """Detect dark pattern:

Design: {design}
Choice architecture: {architecture}
User interest: {user_interest}
Designer interest: {designer_interest}
Domain: {domain}
Context: {context}

Does this design exploit cognitive biases to trick people into unintended actions? Return ONLY valid JSON."""


class DarkPatternService:
    """Detects dark patterns — deceptive design exploiting biases."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        design: str,
        *,
        architecture: str = "",
        user_interest: str = "",
        designer_interest: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect dark pattern."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DARK_PATTERN_PROMPT.format(
                design=design,
                architecture=architecture or "Not specified",
                user_interest=user_interest or "Not specified",
                designer_interest=designer_interest or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DARK_PATTERN_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "design": design[:200],
            "dark_pattern_present": data.get("dark_pattern_present", False),
            "severity": data.get("severity", ""),
            "pattern_type": data.get("pattern_type", ""),
            "exploitation": data.get("exploitation", ""),
            "user_interest": data.get("user_interest", ""),
            "recommendation": data.get("recommendation", ""),
        }
