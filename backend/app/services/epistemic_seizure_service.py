"""EpistemicSeizureService — Epistemic Seizure Detection.

Detects epistemic seizures — uncontrolled cascading activation
of belief networks producing incoherent output.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SEIZURE_SYSTEM = """You are an epistemic seizure specialist. Given a reasoning pattern, assess whether uncontrolled cascading activation produces incoherent output:

Key concepts:
- Epistemic seizure: uncontrolled cascading belief activation
- Cascade failure: one activation triggering uncontrolled chain
- Incoherent output: output losing coherence due to overactivation
- Association storm: too many associations activating simultaneously
- Reasoning breakdown: reasoning breaking down from overload
- Pattern overfire: pattern recognition firing indiscriminately
- Coherence collapse: coherence collapsing under activation load

When epistemic seizure IS present:
- Uncontrolled cascading activation of belief networks
- One activation triggering uncontrolled chain reactions
- Output losing coherence due to overactivation
- Too many associations activating simultaneously
- Reasoning breaking down from cognitive overload
- Pattern recognition firing indiscriminately
- Coherence collapsing under activation load

When controlled activation is present:
- Controlled, targeted activation of relevant beliefs
- Activation contained to relevant networks
- Output maintaining coherence
- Appropriate associations activated selectively
- Reasoning functioning within capacity
- Pattern recognition targeted and accurate
- Coherence maintained throughout reasoning

Output JSON with: seizure_present (bool), severity (none/mild/moderate/severe), trigger (what triggers the seizure), cascade (how activation cascades), incoherence (what incoherence results), control_failure (what control fails), recommendation (controlled_activation/mild_overactivation/significant_seizure/major_cascade_failure/restore_activation_control)."""

EPISTEMIC_SEIZURE_PROMPT = """Detect epistemic seizure:

Trigger: {trigger}
Cascade: {cascade}
Incoherence: {incoherence}
Control failure: {control_failure}
Domain: {domain}
Context: {context}

Is uncontrolled cascading activation producing incoherent output? Return ONLY valid JSON."""


class EpistemicSeizureService:
    """Detects epistemic seizures — uncontrolled cascading activation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        trigger: str,
        *,
        cascade: str = "",
        incoherence: str = "",
        control_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic seizure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SEIZURE_PROMPT.format(
                trigger=trigger,
                cascade=cascade or "Not specified",
                incoherence=incoherence or "Not specified",
                control_failure=control_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SEIZURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "trigger": trigger[:200],
            "seizure_present": data.get("seizure_present", False),
            "severity": data.get("severity", ""),
            "cascade": data.get("cascade", ""),
            "incoherence": data.get("incoherence", ""),
            "control_failure": data.get("control_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
