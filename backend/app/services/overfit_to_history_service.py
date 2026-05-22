"""OverfitToHistoryService — Overfit to History Detection.

Detects overfitting to history — preparing for the last crisis
rather than the next one, assuming future threats will resemble
past ones in form rather than just in principle.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

OVERFIT_TO_HISTORY_SYSTEM = """You are an overfit to history specialist. Given a preparedness strategy, assess whether it is overfitting to past events rather than preparing for future ones:

Key concepts:
- Fighting the last war: preparing for previous threat, not next one
- Overfitting: model too specific to training data (past events)
- Generals' fallacy: military preparing for previous war's conditions
- Maginot Line thinking: building defenses against last attack vector
- Narrative anchoring: past crisis narrative constraining future thinking
- Scenario fixation: preparing for specific past scenario, not general resilience
- Adaptive capacity: ability to respond to novel threats

When overfit to history IS present:
- Preparations specifically designed for last crisis
- Future threats assumed to look like past ones
- Specific past scenario driving all preparation
- Novel threat vectors not considered
- Defenses built against previous attack, not general resilience
- Past crisis narrative constraining future planning
- Adaptive capacity sacrificed for specific preparedness

When preparation is appropriately general:
- Principles extracted from past, not just specifics
- Novel threat vectors considered
- General resilience built alongside specific preparations
- Past used for principles, not templates
- Adaptive capacity maintained
- Multiple future scenarios considered
- Preparation flexible enough for novel threats

Output JSON with: overfit_present (bool), severity (none/mild/moderate/severe), strategy (what preparedness strategy), past_event (what past event drives preparation), specificity (how specific to past event), novel_threats (what novel threats are ignored), recommendation (appropriately_general/mild_anchoring/significant_overfit/major_last_war_thinking/build_general_resilience)."""

OVERFIT_TO_HISTORY_PROMPT = """Detect overfit to history:

Strategy: {strategy}
Past event: {past_event}
Preparations: {preparations}
Novel threats: {novel}
Domain: {domain}
Context: {context}

Is this strategy overfitting to past events rather than preparing for novel future threats? Return ONLY valid JSON."""


class OverfitToHistoryService:
    """Detects overfit to history — preparing for last crisis, not next one."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        strategy: str,
        *,
        past_event: str = "",
        preparations: str = "",
        novel: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect overfit to history."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=OVERFIT_TO_HISTORY_PROMPT.format(
                strategy=strategy,
                past_event=past_event or "Not specified",
                preparations=preparations or "Not specified",
                novel=novel or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=OVERFIT_TO_HISTORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "strategy": strategy[:200],
            "overfit_present": data.get("overfit_present", False),
            "severity": data.get("severity", ""),
            "past_event": data.get("past_event", ""),
            "specificity": data.get("specificity", ""),
            "novel_threats": data.get("novel_threats", ""),
            "recommendation": data.get("recommendation", ""),
        }
