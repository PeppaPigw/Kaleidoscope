"""MotivatedStoppingService — Motivated Stopping Detection.

Detects motivated stopping — ceasing to search for evidence once
a satisfying conclusion has been reached, rather than continuing
to search until the evidence is actually sufficient. The search
stops not because enough evidence has been found, but because
the desired conclusion has been reached.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MOTIVATED_STOPPING_SYSTEM = """You are a motivated stopping specialist. Given a search or investigation process, assess whether the search stopped because a desired conclusion was reached rather than because evidence was sufficient:

Key concepts:
- Motivated stopping: stopping search when desired conclusion is found
- Satisficing vs optimizing: stopping at "good enough" vs best answer
- Confirmation stop: stopping at first confirming evidence
- Asymmetric search termination: searching longer for unwanted conclusions
- Evidence sufficiency: when is evidence actually enough?
- Premature closure: concluding before adequate investigation
- One-sided search: looking only until you find what you want

When motivated stopping IS present:
- Stopping research after finding the first supporting source
- "I found evidence for X, so X must be true" (without looking for counter-evidence)
- Searching longer and harder when initial results are unwanted
- Declaring investigation complete when desired conclusion is reached
- Not checking whether counter-evidence exists
- "I've seen enough" said much sooner for preferred conclusions
- Asymmetric effort: easy acceptance of wanted conclusions, hard scrutiny of unwanted

When stopping IS appropriate:
- Genuine evidence sufficiency has been reached
- The same stopping criterion is applied regardless of conclusion
- Counter-evidence has been actively sought
- The stopping point was determined in advance
- Resource constraints require stopping (acknowledged)
- The conclusion is robust to additional evidence

Output JSON with: motivated_stopping_present (bool), severity (none/mild/moderate/severe), search (what was being investigated), stopping_point (when did the search stop), conclusion_reached (what conclusion was reached), desired_conclusion (was this the desired conclusion), counter_evidence_sought (was counter-evidence actively sought), stopping_criterion (what criterion determined stopping), asymmetry (would search have continued if conclusion were different), recommendation (stopping_justified/mild_premature_closure/significant_motivated_stopping/major_one_sided_search/continue_searching_symmetrically)."""

MOTIVATED_STOPPING_PROMPT = """Detect motivated stopping:

Investigation: {investigation}
Conclusion: {conclusion}
Search effort: {effort}
Counter-evidence: {counter_evidence}
Domain: {domain}
Context: {context}

Did the search stop because a desired conclusion was reached rather than because evidence was sufficient? Return ONLY valid JSON."""


class MotivatedStoppingService:
    """Detects motivated stopping — stopping search at desired conclusion."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investigation: str,
        *,
        conclusion: str = "",
        effort: str = "",
        counter_evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect motivated stopping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MOTIVATED_STOPPING_PROMPT.format(
                investigation=investigation,
                conclusion=conclusion or "Not specified",
                effort=effort or "Not specified",
                counter_evidence=counter_evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MOTIVATED_STOPPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investigation": investigation[:200],
            "motivated_stopping_present": data.get("motivated_stopping_present", False),
            "severity": data.get("severity", ""),
            "stopping_point": data.get("stopping_point", ""),
            "conclusion_reached": data.get("conclusion_reached", ""),
            "desired_conclusion": data.get("desired_conclusion", ""),
            "counter_evidence_sought": data.get("counter_evidence_sought", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
