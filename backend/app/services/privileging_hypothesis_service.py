"""PrivilegingHypothesisService — Privileging the Hypothesis Detection.

Detects privileging the hypothesis — singling out one particular
hypothesis for special attention without sufficient justification.
Out of the vast space of possible explanations, one is elevated
to "the hypothesis to test" without explaining why it deserves
that status. The prior probability of any specific hypothesis
is usually very low.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PRIVILEGING_HYPOTHESIS_SYSTEM = """You are a privileging the hypothesis specialist. Given an investigation or inquiry, assess whether one hypothesis is receiving unjustified special attention:

Key concepts (Yudkowsky, 2009):
- Privileging the hypothesis: singling out one explanation without justification
- Prior probability: most specific hypotheses have very low priors
- Hypothesis space: the vast space of possible explanations
- Availability bias interaction: salient hypotheses get privileged
- Cultural privilege: familiar hypotheses get unearned attention
- Narrative privilege: story-like hypotheses get elevated
- Burden of proof: why should THIS hypothesis get tested first?

When privileging IS present:
- Testing one specific hypothesis without explaining why it's more likely
- "What if it's X?" without justifying why X over infinite alternatives
- Giving one explanation detailed consideration while ignoring others
- "We should investigate whether..." without prior probability justification
- Treating a specific hypothesis as the default to be disproven
- Elevating a hypothesis because it's interesting, not because it's likely
- "Could it be that..." for low-prior hypotheses

When focused investigation IS appropriate:
- The hypothesis has genuinely high prior probability
- Evidence specifically points to this hypothesis
- The hypothesis is the simplest explanation (Occam's razor)
- Multiple hypotheses are being considered proportionally
- The focus is justified by specific evidence, not just salience
- Resource constraints require prioritization (acknowledged)

Output JSON with: privileging_present (bool), severity (none/mild/moderate/severe), hypothesis (what hypothesis is being privileged), justification (what justification is given for focus), prior_probability (what is the actual prior probability), alternative_hypotheses (what alternatives are being ignored), privilege_source (why is this hypothesis salient — availability/culture/narrative), evidence_basis (what evidence specifically supports this hypothesis), recommendation (focus_justified/mild_privileging/significant_hypothesis_privilege/major_unjustified_focus/consider_hypothesis_space)."""

PRIVILEGING_HYPOTHESIS_PROMPT = """Detect privileging the hypothesis:

Investigation: {investigation}
Focused hypothesis: {hypothesis}
Justification: {justification}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Is one hypothesis receiving unjustified special attention out of the space of possibilities? Return ONLY valid JSON."""


class PrivilegingHypothesisService:
    """Detects privileging the hypothesis — unjustified focus on one explanation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        investigation: str,
        *,
        hypothesis: str = "",
        justification: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect privileging the hypothesis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PRIVILEGING_HYPOTHESIS_PROMPT.format(
                investigation=investigation,
                hypothesis=hypothesis or "Not specified",
                justification=justification or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PRIVILEGING_HYPOTHESIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "investigation": investigation[:200],
            "privileging_present": data.get("privileging_present", False),
            "severity": data.get("severity", ""),
            "hypothesis": data.get("hypothesis", ""),
            "prior_probability": data.get("prior_probability", ""),
            "alternative_hypotheses": data.get("alternative_hypotheses", ""),
            "privilege_source": data.get("privilege_source", ""),
            "evidence_basis": data.get("evidence_basis", ""),
            "recommendation": data.get("recommendation", ""),
        }
