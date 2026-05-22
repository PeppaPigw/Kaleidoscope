"""EpistemicCognitiveSwitchingService — Epistemic Cognitive Switching Detection.

Detects epistemic cognitive switching — context switching degrading
depth of understanding and epistemic quality.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COGNITIVE_SWITCHING_SYSTEM = """You are an epistemic cognitive switching specialist. Given context switching degrading understanding, assess cognitive switching:

Key concepts:
- Epistemic cognitive switching: context switching degrading depth of understanding
- Task switching cost: losing depth when switching between tasks
- Context loss: losing context when switching domains
- Depth sacrifice: sacrificing depth for breadth of switching
- Continuity break: breaking continuity of thought
- Momentum loss: losing intellectual momentum from switching
- Fragmented understanding: understanding fragmented across switches

When epistemic cognitive switching IS present:
- Context switching degrading depth
- Task switching costly
- Context being lost
- Depth sacrificed for switching
- Continuity broken
- Momentum lost
- Understanding fragmented

When no cognitive switching:
- Context maintained across switches
- Task switching managed
- Context preserved
- Depth maintained
- Continuity preserved
- Momentum sustained
- Understanding integrated

Output JSON with: cognitive_switching_detected (bool), severity (none/mild/moderate/severe), task_switching_cost (what depth lost from switching), context_loss (what context lost), depth_sacrifice (what depth sacrificed), momentum_loss (what momentum lost), recommendation (no_cognitive_switching/mild_batching_practice/significant_focus_blocks/major_intensive_single_tasking/emergency_complete_cognitive_switching)."""

EPISTEMIC_COGNITIVE_SWITCHING_PROMPT = """Detect epistemic cognitive switching:

Task switching cost: {task_switching_cost}
Context loss: {context_loss}
Depth sacrifice: {depth_sacrifice}
Momentum loss: {momentum_loss}
Domain: {domain}
Context: {context}

Is context switching degrading depth of understanding? Return ONLY valid JSON."""


class EpistemicCognitiveSwitchingService:
    """Detects epistemic cognitive switching — context switching degrading depth."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        task_switching_cost: str,
        *,
        context_loss: str = "",
        depth_sacrifice: str = "",
        momentum_loss: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cognitive switching."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COGNITIVE_SWITCHING_PROMPT.format(
                task_switching_cost=task_switching_cost,
                context_loss=context_loss or "Not specified",
                depth_sacrifice=depth_sacrifice or "Not specified",
                momentum_loss=momentum_loss or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COGNITIVE_SWITCHING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "task_switching_cost": task_switching_cost[:200],
            "cognitive_switching_detected": data.get("cognitive_switching_detected", False),
            "severity": data.get("severity", ""),
            "context_loss": data.get("context_loss", ""),
            "depth_sacrifice": data.get("depth_sacrifice", ""),
            "momentum_loss": data.get("momentum_loss", ""),
            "recommendation": data.get("recommendation", ""),
        }
