"""HindsightCreepService — Hindsight Creep Detection.

Detects hindsight creep — gradual revision of prior beliefs
to align with known outcomes, beyond the initial "I knew it
all along" moment. Fischhoff (1975) extended. Unlike sudden
hindsight bias, creep is the slow, unconscious drift of
remembered predictions toward actual outcomes over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HINDSIGHT_CREEP_SYSTEM = """You are a hindsight creep specialist. Given a recalled prediction or prior belief, assess whether it has gradually drifted toward the known outcome:

Key concepts (Fischhoff, 1975; extended):
- Hindsight creep: gradual revision of remembered predictions
- Memory reconstruction: rebuilding past beliefs from current knowledge
- Creeping determinism: past events seeming increasingly inevitable over time
- Narrative smoothing: making the past consistent with the present
- Confidence inflation: remembered confidence growing over time
- Selective recall: remembering hits, forgetting misses
- Outcome knowledge contamination: knowing the answer changes remembered prediction

When hindsight creep IS present:
- "I always thought X would happen" when records show uncertainty
- Predictions that become more confident in retrospect
- Prior beliefs that suspiciously align with known outcomes
- "We saw this coming" when contemporaneous records show surprise
- Gradual revision of "what we expected" to match what happened
- Historical narratives that make outcomes seem inevitable
- Forgetting how uncertain things were at the time

When the recall IS accurate:
- Written records confirm the prior prediction
- The person acknowledges uncertainty at the time
- The prediction was documented before the outcome
- The person can articulate what they got wrong
- Contemporaneous evidence supports the claimed foresight

Output JSON with: hindsight_creep_present (bool), severity (none/mild/moderate/severe), recalled_prediction (what does the person remember predicting), actual_prediction (what was actually predicted, if known), outcome (what actually happened), drift_magnitude (how much has the memory shifted), documentation (is there a record of the original prediction), time_elapsed (how long since the original prediction), recommendation (recall_accurate/mild_creep/significant_revision/major_hindsight_creep/check_contemporaneous_records)."""

HINDSIGHT_CREEP_PROMPT = """Detect hindsight creep:

Recalled prediction: {recalled}
Actual record: {actual}
Outcome: {outcome}
Time elapsed: {elapsed}
Domain: {domain}
Context: {context}

Has the remembered prediction gradually drifted toward the known outcome? Return ONLY valid JSON."""


class HindsightCreepService:
    """Detects hindsight creep — gradual revision of remembered predictions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        recalled: str,
        *,
        actual: str = "",
        outcome: str = "",
        elapsed: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect hindsight creep."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=HINDSIGHT_CREEP_PROMPT.format(
                recalled=recalled,
                actual=actual or "Not specified",
                outcome=outcome or "Not specified",
                elapsed=elapsed or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=HINDSIGHT_CREEP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "recalled": recalled[:200],
            "hindsight_creep_present": data.get("hindsight_creep_present", False),
            "severity": data.get("severity", ""),
            "actual_prediction": data.get("actual_prediction", ""),
            "outcome": data.get("outcome", ""),
            "drift_magnitude": data.get("drift_magnitude", ""),
            "documentation": data.get("documentation", ""),
            "time_elapsed": data.get("time_elapsed", ""),
            "recommendation": data.get("recommendation", ""),
        }
