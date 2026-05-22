"""PrematureEpistemicClosureService — Premature Epistemic Closure Detection.

Detects premature epistemic closure — closing inquiry too early
before sufficient evidence has been gathered.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PREMATURE_EPISTEMIC_CLOSURE_SYSTEM = """You are a premature epistemic closure specialist. Given an inquiry process, assess whether closure is occurring too early:

Key concepts:
- Premature epistemic closure: closing inquiry before sufficient evidence
- Early conclusion: reaching conclusions before adequate investigation
- Insufficient evidence closure: closing with insufficient evidence
- Inquiry truncation: truncating inquiry before completion
- Satisfaction threshold: too-low threshold for concluding
- Evidence impatience: impatient with evidence gathering
- Closure pressure: pressure to close inquiry prematurely

When premature epistemic closure IS present:
- Inquiry closed before sufficient evidence gathered
- Conclusions reached before adequate investigation
- Evidence insufficient for the conclusions drawn
- Inquiry truncated before natural completion
- Satisfaction threshold too low for the question
- Impatience with evidence gathering process
- Pressure to close driving premature conclusions

When appropriate closure is present:
- Inquiry closed after sufficient evidence
- Conclusions proportionate to investigation
- Evidence adequate for conclusions drawn
- Inquiry completed at natural endpoint
- Satisfaction threshold appropriate
- Patience with evidence gathering
- Closure driven by evidence not pressure

Output JSON with: premature_closure_present (bool), severity (none/mild/moderate/severe), inquiry (what inquiry is closed), evidence_status (what evidence exists), closure_reason (why closure occurs), missing_evidence (what evidence is still needed), recommendation (appropriate_closure/mild_impatience/significant_premature_closure/major_inquiry_truncation/continue_gathering_evidence)."""

PREMATURE_EPISTEMIC_CLOSURE_PROMPT = """Detect premature epistemic closure:

Inquiry: {inquiry}
Evidence status: {evidence}
Closure reason: {reason}
Missing evidence: {missing}
Domain: {domain}
Context: {context}

Is inquiry being closed too early before sufficient evidence? Return ONLY valid JSON."""


class PrematureEpistemicClosureService:
    """Detects premature epistemic closure — closing inquiry too early."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        inquiry: str,
        *,
        evidence: str = "",
        reason: str = "",
        missing: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect premature epistemic closure."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PREMATURE_EPISTEMIC_CLOSURE_PROMPT.format(
                inquiry=inquiry,
                evidence=evidence or "Not specified",
                reason=reason or "Not specified",
                missing=missing or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PREMATURE_EPISTEMIC_CLOSURE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "inquiry": inquiry[:200],
            "premature_closure_present": data.get("premature_closure_present", False),
            "severity": data.get("severity", ""),
            "evidence_status": data.get("evidence_status", ""),
            "closure_reason": data.get("closure_reason", ""),
            "missing_evidence": data.get("missing_evidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
