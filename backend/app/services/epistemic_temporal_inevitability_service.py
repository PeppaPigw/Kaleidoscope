"""EpistemicTemporalInevitabilityService — Epistemic Temporal Inevitability Detection.

Detects epistemic temporal inevitability — treating historical outcomes as inevitable
rather than contingent, erasing the role of chance, choice, and alternative paths.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TEMPORAL_INEVITABILITY_SYSTEM = """You are an epistemic temporal inevitability specialist. Given inevitability reasoning, assess contingency erasure:

Key concepts:
- Epistemic temporal inevitability: treating outcomes as predetermined
- Deterministic narrative: framing history as inevitable progression
- Contingency erasure: erasing role of chance and choice
- Path dependency blindness: ignoring how small changes could alter outcomes
- Counterfactual suppression: refusing to consider alternative histories
- Teleological thinking: assuming events aimed toward current outcome
- Winner's narrative: history written to justify current power arrangements

When epistemic temporal inevitability IS present:
- Outcomes treated as predetermined
- History framed as inevitable
- Contingency erased
- Path dependency ignored
- Counterfactuals suppressed
- Teleological thinking applied
- Winner's narrative imposed

When no inevitability bias:
- Outcomes seen as contingent
- History acknowledged as open
- Chance and choice recognized
- Path dependency understood
- Counterfactuals explored
- No teleological assumption
- Multiple narratives considered

Output JSON with: inevitability_detected (bool), severity (none/mild/moderate/severe), deterministic_narrative (what framed as inevitable), contingency_erasure (what contingency erased), counterfactual_suppression (what counterfactuals suppressed), teleological_thinking (what teleology applied), recommendation (no_inevitability/mild_contingency_awareness/significant_counterfactual_exploration/major_intensive_path_analysis/emergency_complete_inevitability)."""

EPISTEMIC_TEMPORAL_INEVITABILITY_PROMPT = """Detect epistemic temporal inevitability:

Deterministic narrative: {deterministic_narrative}
Contingency erasure: {contingency_erasure}
Counterfactual suppression: {counterfactual_suppression}
Teleological thinking: {teleological_thinking}
Domain: {domain}
Context: {context}

Are outcomes being treated as inevitable rather than contingent? Return ONLY valid JSON."""


class EpistemicTemporalInevitabilityService:
    """Detects epistemic temporal inevitability — contingency erasure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        deterministic_narrative: str,
        *,
        contingency_erasure: str = "",
        counterfactual_suppression: str = "",
        teleological_thinking: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic temporal inevitability."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TEMPORAL_INEVITABILITY_PROMPT.format(
                deterministic_narrative=deterministic_narrative,
                contingency_erasure=contingency_erasure or "Not specified",
                counterfactual_suppression=counterfactual_suppression or "Not specified",
                teleological_thinking=teleological_thinking or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TEMPORAL_INEVITABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "deterministic_narrative": deterministic_narrative[:200],
            "inevitability_detected": data.get("inevitability_detected", False),
            "severity": data.get("severity", ""),
            "contingency_erasure": data.get("contingency_erasure", ""),
            "counterfactual_suppression": data.get("counterfactual_suppression", ""),
            "teleological_thinking": data.get("teleological_thinking", ""),
            "recommendation": data.get("recommendation", ""),
        }
