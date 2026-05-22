"""ProportionalityHeuristicService — Proportionality Heuristic Detection.

Detects the proportionality heuristic — the assumption that big
effects must have big causes and small effects must have small
causes. This leads to rejecting simple explanations for complex
phenomena and conspiracy thinking (big events need big conspiracies).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROPORTIONALITY_HEURISTIC_SYSTEM = """You are a proportionality heuristic specialist. Given a causal attribution, assess whether the proportionality assumption is distorting judgment:

Key concepts:
- Proportionality heuristic: big effects need big causes
- Conspiracy ideation: major events demand major explanations
- Simplicity rejection: simple causes for complex effects feel wrong
- Magnitude matching: cause magnitude should match effect magnitude
- Narrative satisfaction: proportional explanations feel more complete
- Complexity bias: preferring complex explanations over simple ones
- Causal asymmetry: accepting disproportionate causes in one direction

When proportionality heuristic IS distorting:
- Rejecting simple explanations for major events
- "Something this big couldn't be caused by something so small"
- Assuming complex outcomes require complex causes
- Conspiracy theories filling the proportionality gap
- Dismissing mundane explanations for dramatic outcomes
- Overcomplicating causal models to match effect magnitude
- Ignoring how small causes can cascade into large effects

When proportional reasoning IS appropriate:
- The causal mechanism genuinely requires proportional input
- Energy conservation or physical constraints apply
- The simple explanation has been genuinely ruled out
- There is evidence for a more complex causal chain
- The domain has validated proportionality relationships

Output JSON with: proportionality_heuristic_present (bool), severity (none/mild/moderate/severe), event (what effect is being explained), proposed_cause (what cause is being considered), proportionality_gap (how disproportionate are cause and effect), rejected_explanation (what simpler explanation was rejected), cascade_potential (could small cause cascade to large effect), evidence_basis (what evidence supports the causal claim), recommendation (proportional_reasoning_valid/mild_magnitude_matching/significant_proportionality_bias/major_complexity_inflation/consider_simpler_causes)."""

PROPORTIONALITY_HEURISTIC_PROMPT = """Detect proportionality heuristic:

Event: {event}
Proposed cause: {proposed_cause}
Alternative: {alternative}
Reasoning: {reasoning}
Domain: {domain}
Context: {context}

Is the proportionality assumption (big effects need big causes) distorting causal reasoning? Return ONLY valid JSON."""


class ProportionalityHeuristicService:
    """Detects proportionality heuristic — magnitude matching in causal reasoning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        event: str,
        *,
        proposed_cause: str = "",
        alternative: str = "",
        reasoning: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect proportionality heuristic."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROPORTIONALITY_HEURISTIC_PROMPT.format(
                event=event,
                proposed_cause=proposed_cause or "Not specified",
                alternative=alternative or "Not specified",
                reasoning=reasoning or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROPORTIONALITY_HEURISTIC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "event": event[:200],
            "proportionality_heuristic_present": data.get("proportionality_heuristic_present", False),
            "severity": data.get("severity", ""),
            "proposed_cause": data.get("proposed_cause", ""),
            "proportionality_gap": data.get("proportionality_gap", ""),
            "rejected_explanation": data.get("rejected_explanation", ""),
            "cascade_potential": data.get("cascade_potential", ""),
            "evidence_basis": data.get("evidence_basis", ""),
            "recommendation": data.get("recommendation", ""),
        }
