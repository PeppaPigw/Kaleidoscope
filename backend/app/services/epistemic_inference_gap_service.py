"""EpistemicInferenceGapService — Epistemic Inference Gap Detection.

Detects epistemic inference gaps — gaps in inference chains where
conclusions don't follow from premises.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_INFERENCE_GAP_SYSTEM = """You are an epistemic inference gap specialist. Given inference chains with gaps, assess inference gaps:

Key concepts:
- Epistemic inference gap: conclusions not following from premises
- Missing premise: unstated premise needed for conclusion
- Logical leap: jumping to conclusion without intermediate steps
- Non sequitur: conclusion not following from argument
- Enthymeme abuse: relying on unstated assumptions
- Bridge failure: failure to bridge from evidence to conclusion
- Warrant absence: missing warrant connecting data to claim

When epistemic inference gap IS present:
- Conclusions don't follow
- Premises missing
- Logical leaps made
- Non sequiturs present
- Unstated assumptions relied upon
- Bridges missing
- Warrants absent

When no inference gap:
- Conclusions follow from premises
- All premises stated
- Steps connected
- Logic valid
- Assumptions explicit
- Bridges present
- Warrants provided

Output JSON with: inference_gap_detected (bool), severity (none/mild/moderate/severe), missing_premise (what premises missing), logical_leap (what leaps made), non_sequitur (what non sequiturs), warrant_absence (what warrants missing), recommendation (no_inference_gap/mild_premise_checking/significant_chain_repair/major_intensive_logic_reconstruction/emergency_complete_inference_gap)."""

EPISTEMIC_INFERENCE_GAP_PROMPT = """Detect epistemic inference gap:

Missing premise: {missing_premise}
Logical leap: {logical_leap}
Non sequitur: {non_sequitur}
Warrant absence: {warrant_absence}
Domain: {domain}
Context: {context}

Are there gaps in inference chains where conclusions don't follow? Return ONLY valid JSON."""


class EpistemicInferenceGapService:
    """Detects epistemic inference gaps — conclusions not following."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        missing_premise: str,
        *,
        logical_leap: str = "",
        non_sequitur: str = "",
        warrant_absence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic inference gap."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_INFERENCE_GAP_PROMPT.format(
                missing_premise=missing_premise,
                logical_leap=logical_leap or "Not specified",
                non_sequitur=non_sequitur or "Not specified",
                warrant_absence=warrant_absence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_INFERENCE_GAP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "missing_premise": missing_premise[:200],
            "inference_gap_detected": data.get("inference_gap_detected", False),
            "severity": data.get("severity", ""),
            "logical_leap": data.get("logical_leap", ""),
            "non_sequitur": data.get("non_sequitur", ""),
            "warrant_absence": data.get("warrant_absence", ""),
            "recommendation": data.get("recommendation", ""),
        }
