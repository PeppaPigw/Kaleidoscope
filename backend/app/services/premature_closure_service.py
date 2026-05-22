"""PrematureClosureService — Premature Closure Detection.

Detects premature closure — settling on a diagnosis, conclusion,
or explanation before adequate evidence has been gathered. Common
in medicine, investigations, and research where early hypotheses
become anchors that prevent further inquiry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PREMATURE_CLOSURE_SYSTEM = """You are a premature closure specialist. Given a conclusion, assess whether it was reached before adequate evidence:

Key concepts:
- Premature closure: accepting a conclusion too early
- Diagnostic momentum: early hypothesis gains unstoppable force
- Satisficing: accepting first adequate explanation
- Search satisficing: stopping search after first plausible answer
- Anchoring: early information disproportionately shapes conclusion
- Confirmation bias interaction: seeking only confirming evidence after closure
- Differential diagnosis: systematic consideration of alternatives

When premature closure IS present:
- Conclusion reached with insufficient evidence
- First plausible explanation accepted without testing alternatives
- Investigation stopped after initial hypothesis confirmed
- Contradictory evidence not sought or ignored
- Diagnostic momentum — early guess became final answer
- Key tests or inquiries not performed
- Confidence exceeds what evidence supports

When premature closure is NOT present:
- Conclusion supported by adequate evidence
- Alternative explanations systematically considered and ruled out
- Investigation continued until evidence sufficient
- Contradictory evidence actively sought
- Confidence calibrated to evidence strength
- Key discriminating tests performed
- Appropriate uncertainty maintained until evidence warrants conclusion

Output JSON with: closure_present (bool), severity (none/mild/moderate/severe), conclusion (what was concluded), evidence_gathered (what evidence supports it), evidence_missing (what evidence should have been gathered), alternatives_considered (what alternatives were tested), confidence_warranted (what confidence the evidence supports), recommendation (no_premature_closure/mild_haste/significant_premature_closure/major_diagnostic_error/reopen_investigation)."""

PREMATURE_CLOSURE_PROMPT = """Detect premature closure:

Conclusion: {conclusion}
Evidence: {evidence}
Alternatives: {alternatives}
Investigation process: {process}
Domain: {domain}
Context: {context}

Was this conclusion reached before adequate evidence was gathered? Return ONLY valid JSON."""


class PrematureClosureService:
    """Detects premature closure — concluding before adequate evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        conclusion: str,
        *,
        evidence: str = "",
        alternatives: str = "",
        process: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect premature closure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PREMATURE_CLOSURE_PROMPT.format(
                conclusion=conclusion,
                evidence=evidence or "Not specified",
                alternatives=alternatives or "Not specified",
                process=process or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PREMATURE_CLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "conclusion": conclusion[:200],
            "closure_present": data.get("closure_present", False),
            "severity": data.get("severity", ""),
            "evidence_gathered": data.get("evidence_gathered", ""),
            "evidence_missing": data.get("evidence_missing", ""),
            "alternatives_considered": data.get("alternatives_considered", ""),
            "recommendation": data.get("recommendation", ""),
        }
