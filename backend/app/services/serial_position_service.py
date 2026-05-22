"""SerialPositionService — Serial Position Effect Detection.

Detects serial position effect — disproportionate recall of
first items (primacy) and last items (recency) while middle
items are forgotten. Murdock (1962). In any sequence — meeting
agendas, argument lists, evidence presentations — the middle
gets lost. First impressions and last words dominate memory.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SERIAL_POSITION_SYSTEM = """You are a serial position effect specialist. Given a situation involving sequential information, assess whether primacy/recency effects are distorting evaluation:

Key concepts (Murdock, 1962):
- Serial position effect: first and last items recalled best
- Primacy effect: first items get more rehearsal and attention
- Recency effect: last items still in working memory
- Middle neglect: items in the middle are least recalled
- Order effects in judgment: sequence affects evaluation
- Anchoring through primacy: first information sets the frame
- Recency bias in decisions: last information weighs most heavily

When serial position effects ARE present:
- Decisions heavily influenced by first or last piece of evidence
- Middle arguments in a presentation being forgotten
- First candidate interviewed getting unfair advantage (primacy)
- Last option presented being chosen disproportionately (recency)
- Agenda items in the middle receiving less attention
- "I remember the beginning and end but not the middle"
- Order of presentation determining outcome more than content

When evaluation IS balanced:
- All items given equal consideration regardless of position
- Explicit effort to review middle items
- Decision criteria applied uniformly across sequence
- Notes taken throughout to prevent position-based forgetting
- Randomization or counterbalancing used to control order effects

Output JSON with: serial_position_present (bool), severity (none/mild/moderate/severe), situation (what sequential information is involved), primacy_effect (how first items are overweighted), recency_effect (how last items are overweighted), middle_neglect (what middle items are being forgotten), sequence_length (how long is the sequence), order_impact (how much does order affect the outcome), recommendation (evaluation_balanced/mild_position_effect/significant_primacy_recency/major_middle_neglect/counterbalance_order_effects)."""

SERIAL_POSITION_PROMPT = """Detect serial position effect:

Situation: {situation}
Sequence: {sequence}
Recall pattern: {recall}
Decision impact: {impact}
Domain: {domain}
Context: {context}

Are first/last items being disproportionately recalled or weighted while middle items are neglected? Return ONLY valid JSON."""


class SerialPositionService:
    """Detects serial position effect — primacy/recency bias in sequential information."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        sequence: str = "",
        recall: str = "",
        impact: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect serial position effect."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SERIAL_POSITION_PROMPT.format(
                situation=situation,
                sequence=sequence or "Not specified",
                recall=recall or "Not specified",
                impact=impact or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SERIAL_POSITION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "serial_position_present": data.get("serial_position_present", False),
            "severity": data.get("severity", ""),
            "primacy_effect": data.get("primacy_effect", ""),
            "recency_effect": data.get("recency_effect", ""),
            "middle_neglect": data.get("middle_neglect", ""),
            "sequence_length": data.get("sequence_length", ""),
            "order_impact": data.get("order_impact", ""),
            "recommendation": data.get("recommendation", ""),
        }
