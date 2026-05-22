"""EpistemicGrowthSabotageService — Epistemic Growth Sabotage Detection.

Detects epistemic growth sabotage — unconsciously sabotaging one's own
intellectual growth through self-defeating patterns.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_GROWTH_SABOTAGE_SYSTEM = """You are an epistemic growth sabotage specialist. Given unconsciously sabotaging growth, assess growth sabotage:

Key concepts:
- Epistemic growth sabotage: unconsciously sabotaging own intellectual growth
- Self-defeating patterns: patterns that defeat own growth
- Success avoidance: avoiding intellectual success
- Breakthrough prevention: preventing own breakthroughs
- Understanding sabotage: sabotaging own understanding
- Progress undermining: undermining own progress
- Growth self-destruction: destroying own growth opportunities

When epistemic growth sabotage IS present:
- Unconsciously sabotaging growth
- Self-defeating patterns active
- Avoiding intellectual success
- Preventing own breakthroughs
- Sabotaging own understanding
- Undermining own progress
- Destroying growth opportunities

When no growth sabotage:
- Supporting own growth
- Self-enhancing patterns
- Welcoming success
- Allowing breakthroughs
- Supporting own understanding
- Building on progress
- Nurturing growth opportunities

Output JSON with: growth_sabotage_detected (bool), severity (none/mild/moderate/severe), self_defeating_patterns (what patterns defeating growth), success_avoidance (what success avoiding), breakthrough_prevention (what breakthroughs preventing), progress_undermining (what progress undermining), recommendation (no_growth_sabotage/mild_pattern_awareness/significant_self_support_building/major_intensive_sabotage_interruption/emergency_complete_growth_sabotage)."""

EPISTEMIC_GROWTH_SABOTAGE_PROMPT = """Detect epistemic growth sabotage:

Self defeating patterns: {self_defeating_patterns}
Success avoidance: {success_avoidance}
Breakthrough prevention: {breakthrough_prevention}
Progress undermining: {progress_undermining}
Domain: {domain}
Context: {context}

Is there unconsciously sabotaging one's own intellectual growth? Return ONLY valid JSON."""


class EpistemicGrowthSabotageService:
    """Detects epistemic growth sabotage — unconsciously sabotaging growth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        self_defeating_patterns: str,
        *,
        success_avoidance: str = "",
        breakthrough_prevention: str = "",
        progress_undermining: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic growth sabotage."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_GROWTH_SABOTAGE_PROMPT.format(
                self_defeating_patterns=self_defeating_patterns,
                success_avoidance=success_avoidance or "Not specified",
                breakthrough_prevention=breakthrough_prevention or "Not specified",
                progress_undermining=progress_undermining or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_GROWTH_SABOTAGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "self_defeating_patterns": self_defeating_patterns[:200],
            "growth_sabotage_detected": data.get("growth_sabotage_detected", False),
            "severity": data.get("severity", ""),
            "success_avoidance": data.get("success_avoidance", ""),
            "breakthrough_prevention": data.get("breakthrough_prevention", ""),
            "progress_undermining": data.get("progress_undermining", ""),
            "recommendation": data.get("recommendation", ""),
        }
