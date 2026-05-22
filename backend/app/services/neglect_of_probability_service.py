"""NeglectOfProbabilityService — Neglect of Probability Detection.

Detects neglect of probability — ignoring probability
information when making decisions under uncertainty, focusing
instead on the magnitude of outcomes. People fear plane
crashes (low probability, high magnitude) more than car
accidents (high probability, lower magnitude per event).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NEGLECT_PROBABILITY_SYSTEM = """You are a neglect of probability specialist. Given a risk assessment or decision under uncertainty, assess whether probability information is being properly incorporated:

Key concepts:
- Neglect of probability: focusing on outcome magnitude while ignoring likelihood
- Possibility effect: overweighting small probabilities (lottery, terrorism)
- Certainty effect: overweighting certainty vs. high probability
- Dread risk: low-probability catastrophic events get disproportionate attention
- Expected value neglect: not multiplying probability × magnitude
- Binary thinking: treating uncertain events as either "will happen" or "won't"
- Probability insensitivity: not distinguishing between 1% and 10%

When probability neglect IS present:
- Fearing rare catastrophes while ignoring common dangers
- Making decisions based on worst case without considering its likelihood
- "It could happen" treated the same regardless of probability
- Not distinguishing between 0.1% and 10% probability
- Buying insurance for unlikely events while ignoring likely ones
- Security theater: addressing dramatic but improbable threats

When ignoring probability IS appropriate:
- The outcome is truly catastrophic and irreversible (existential risk)
- The probability is genuinely unknown (deep uncertainty)
- Precautionary principle applies (novel, potentially catastrophic)
- The cost of addressing the risk is trivial relative to the outcome
- Regulatory requirements mandate addressing regardless of probability

Output JSON with: probability_neglect_present (bool), severity (none/mild/moderate/severe), decision (what decision is being made), outcome_feared (what outcome is being considered), probability (what is the actual probability?), magnitude (what is the outcome magnitude?), expected_value (probability × magnitude), probability_incorporated (bool — is probability properly weighted?), binary_thinking (bool — is it treated as will/won't rather than probability?), comparison_risks (what more probable risks are being ignored?), recommendation (probability_considered/mild_neglect/significant_probability_blindness/major_magnitude_fixation/incorporate_probability)."""

NEGLECT_PROBABILITY_PROMPT = """Detect neglect of probability:

Decision: {decision}
Risk: {risk}
Probability: {probability}
Response: {response}
Domain: {domain}
Context: {context}

Is probability information being properly incorporated into this decision? Return ONLY valid JSON."""


class NeglectOfProbabilityService:
    """Detects neglect of probability — ignoring likelihood in risk decisions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        risk: str = "",
        probability: str = "",
        response: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect neglect of probability."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NEGLECT_PROBABILITY_PROMPT.format(
                decision=decision,
                risk=risk or "Not specified",
                probability=probability or "Not specified",
                response=response or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NEGLECT_PROBABILITY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "probability_neglect_present": data.get("probability_neglect_present", False),
            "severity": data.get("severity", ""),
            "outcome_feared": data.get("outcome_feared", ""),
            "probability": data.get("probability", ""),
            "magnitude": data.get("magnitude", ""),
            "expected_value": data.get("expected_value", ""),
            "probability_incorporated": data.get("probability_incorporated", True),
            "binary_thinking": data.get("binary_thinking", False),
            "comparison_risks": data.get("comparison_risks", ""),
            "recommendation": data.get("recommendation", ""),
        }
