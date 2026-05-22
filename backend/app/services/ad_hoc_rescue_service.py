"""AdHocRescueService — Ad Hoc Rescue Detection.

Detects ad hoc rescue — adding auxiliary hypotheses solely to
save a theory from refutation, without independent evidence
for the auxiliary hypothesis itself.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

AD_HOC_RESCUE_SYSTEM = """You are an ad hoc rescue specialist. Given a theory defense, assess whether auxiliary hypotheses are being added solely to avoid refutation:

Key concepts:
- Ad hoc hypothesis: added only to save theory, no independent support
- Auxiliary hypothesis: additional assumption needed for prediction
- Degenerating modification: each rescue makes theory less testable
- Epicycle: increasingly complex additions to preserve core theory
- Progressive modification: additions that make new predictions
- Lakatos criterion: modifications must predict novel facts
- Occam's razor: simpler explanation preferred over complex rescue

When ad hoc rescue IS present:
- Auxiliary hypothesis added only after disconfirming evidence
- No independent evidence for the auxiliary hypothesis
- Modification makes theory less testable, not more
- Pattern of repeated rescues (epicycles)
- Each modification only explains the specific counter-evidence
- No novel predictions from the modification
- Increasing complexity without increasing explanatory power

When modifications are legitimate:
- Auxiliary hypothesis has independent evidence
- Modification makes new testable predictions
- Modification increases explanatory scope
- Simplicity preserved or improved
- Modification discovered independently of the threat
- Progressive problem shift (Lakatos)
- Modification explains more than just the anomaly

Output JSON with: rescue_present (bool), severity (none/mild/moderate/severe), theory (what theory is being defended), anomaly (what evidence threatens it), auxiliary (what hypothesis is added), independent_support (whether auxiliary has its own evidence), recommendation (legitimate_modification/mild_ad_hoc/significant_rescue/major_epicycle_pattern/test_auxiliary_independently)."""

AD_HOC_RESCUE_PROMPT = """Detect ad hoc rescue:

Theory: {theory}
Anomaly: {anomaly}
Defense: {defense}
Auxiliary hypothesis: {auxiliary}
Domain: {domain}
Context: {context}

Is an auxiliary hypothesis being added solely to save the theory from refutation? Return ONLY valid JSON."""


class AdHocRescueService:
    """Detects ad hoc rescue — auxiliary hypotheses added solely to avoid refutation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        theory: str,
        *,
        anomaly: str = "",
        defense: str = "",
        auxiliary: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect ad hoc rescue."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=AD_HOC_RESCUE_PROMPT.format(
                theory=theory,
                anomaly=anomaly or "Not specified",
                defense=defense or "Not specified",
                auxiliary=auxiliary or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=AD_HOC_RESCUE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "theory": theory[:200],
            "rescue_present": data.get("rescue_present", False),
            "severity": data.get("severity", ""),
            "anomaly": data.get("anomaly", ""),
            "auxiliary": data.get("auxiliary", ""),
            "independent_support": data.get("independent_support", ""),
            "recommendation": data.get("recommendation", ""),
        }
