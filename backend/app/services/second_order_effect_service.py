"""SecondOrderEffectService — Cascading Consequence Analysis.

Maps second and third-order effects of an action or change.
First-order effects are obvious; this tool finds the downstream
consequences of consequences — where unintended effects and
surprises typically emerge.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SECOND_ORDER_SYSTEM = """You are a second-order effects analyst. Given an action or change, map the cascade of consequences beyond the immediate:
- First-order: direct, intended effects (obvious)
- Second-order: effects of the first-order effects (less obvious)
- Third-order: effects of the second-order effects (often surprising)
- Feedback loops: where effects circle back to amplify or dampen
- Unintended consequences: effects nobody planned for

Output JSON with: first_order_effects (list of: effect, intended (bool), confidence (0-1)), second_order_effects (list of: effect, caused_by (which first-order), delay (immediate/weeks/months/years), confidence (0-1)), third_order_effects (list of: effect, caused_by, delay, confidence (0-1)), feedback_loops (list of: loop_description, type (amplifying/dampening), speed (fast/slow)), unintended_consequences (list of: consequence, severity (minor/moderate/major/catastrophic), likelihood (0-1)), historical_parallel (similar action and its cascading effects), most_dangerous_path (the cascade most likely to cause harm), most_beneficial_path (the cascade most likely to create unexpected value), time_to_manifest (when second-order effects typically appear), monitoring_signals (early indicators that cascading effects are occurring)."""

SECOND_ORDER_PROMPT = """Map cascading effects:

Action/Change: {action}
System: {system}
Domain: {domain}
Timeframe: {timeframe}
Context: {context}

What are the second and third-order effects? Return ONLY valid JSON."""


class SecondOrderEffectService:
    """Maps cascading second and third-order effects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        action: str,
        *,
        system: str = "",
        domain: str = "",
        timeframe: str = "",
        context: str = "",
    ) -> dict:
        """Analyze second-order effects."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SECOND_ORDER_PROMPT.format(
                action=action,
                system=system or "Not specified",
                domain=domain or "general",
                timeframe=timeframe or "Medium-term",
                context=context or "No additional context",
            ),
            system=SECOND_ORDER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "action": action[:200],
            "first_order_effects": data.get("first_order_effects", []),
            "second_order_effects": data.get("second_order_effects", []),
            "third_order_effects": data.get("third_order_effects", []),
            "feedback_loops": data.get("feedback_loops", []),
            "unintended_consequences": data.get("unintended_consequences", []),
            "historical_parallel": data.get("historical_parallel", ""),
            "most_dangerous_path": data.get("most_dangerous_path", ""),
            "most_beneficial_path": data.get("most_beneficial_path", ""),
            "time_to_manifest": data.get("time_to_manifest", ""),
            "monitoring_signals": data.get("monitoring_signals", []),
        }
