"""TallPoppySyndromeService — Tall Poppy Syndrome Detection.

Detects tall poppy syndrome — the tendency to criticize, resent,
or undermine people who stand out due to their success, talent,
or achievement. The social pressure to conform by cutting down
those who rise above the group.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TALL_POPPY_SYSTEM = """You are a tall poppy syndrome specialist. Given a social dynamic, assess whether someone is being cut down for standing out:

Key concepts:
- Tall poppy syndrome: resentment of those who stand out
- Crab mentality: pulling others down to prevent them from rising
- Social leveling: pressure to conform to group norms
- Envy-driven criticism: criticism motivated by jealousy, not merit
- Legitimate criticism vs resentment: distinguishing the two
- Cultural conformity: some cultures penalize standing out more
- Schadenfreude: pleasure in others' failure

When tall poppy syndrome IS present:
- Criticism that targets success itself rather than specific behaviors
- "Who do they think they are?" reactions to achievement
- Undermining someone specifically because they're succeeding
- Celebrating someone's failure disproportionately
- Holding successful people to higher standards than others
- Attributing success to luck/privilege while attributing failure to character
- Social punishment for ambition or visibility

When tall poppy syndrome is NOT present:
- Criticism is specific, substantive, and proportionate
- Accountability is applied equally regardless of status
- Concerns about behavior are separate from resentment of success
- The criticism would apply regardless of the person's status
- Legitimate power dynamics are being challenged
- The "tall poppy" is genuinely causing harm
- Feedback is constructive and aimed at improvement

Output JSON with: tall_poppy_present (bool), severity (none/mild/moderate/severe), target (who is being cut down), achievement (what success triggers the reaction), criticism (what criticism is leveled), motivation (is it envy or legitimate concern), proportionality (is the criticism proportionate), recommendation (no_tall_poppy/mild_resentment/significant_tall_poppy/major_social_punishment/evaluate_criticism_merit)."""

TALL_POPPY_PROMPT = """Detect tall poppy syndrome:

Situation: {situation}
Target: {target}
Achievement: {achievement}
Criticism: {criticism}
Domain: {domain}
Context: {context}

Is someone being cut down specifically for standing out or succeeding? Return ONLY valid JSON."""


class TallPoppySyndromeService:
    """Detects tall poppy syndrome — cutting down those who stand out."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        target: str = "",
        achievement: str = "",
        criticism: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect tall poppy syndrome."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TALL_POPPY_PROMPT.format(
                situation=situation,
                target=target or "Not specified",
                achievement=achievement or "Not specified",
                criticism=criticism or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TALL_POPPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "tall_poppy_present": data.get("tall_poppy_present", False),
            "severity": data.get("severity", ""),
            "target": data.get("target", ""),
            "achievement": data.get("achievement", ""),
            "motivation": data.get("motivation", ""),
            "recommendation": data.get("recommendation", ""),
        }
