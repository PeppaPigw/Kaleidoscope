"""EpistemicTunnelingService — Epistemic Tunneling Detection.

Detects epistemic tunneling — bypassing evidential barriers through
quantum-like leaps without traversing the necessary reasoning steps.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_TUNNELING_SYSTEM = """You are an epistemic tunneling specialist. Given a reasoning pattern, assess whether evidential barriers are being bypassed through unjustified leaps:

Key concepts:
- Epistemic tunneling: bypassing evidential barriers without justification
- Reasoning leaps: jumping to conclusions without intermediate steps
- Evidence bypass: reaching conclusions without traversing evidence
- Inferential shortcuts: skipping necessary inferential steps
- Barrier avoidance: avoiding the hard work of building evidence chains
- Conclusion teleportation: arriving at conclusions without the journey
- Justification gap: gap between evidence and conclusion

When epistemic tunneling IS present:
- Evidential barriers bypassed without justification
- Conclusions reached without intermediate reasoning steps
- Evidence requirements skipped or ignored
- Necessary inferential steps omitted
- Hard work of evidence building avoided
- Conclusions arrived at without proper journey
- Significant gap between available evidence and stated conclusion

When legitimate intuition is present:
- Intuition based on deep expertise and pattern recognition
- Shortcuts reflect compressed but valid reasoning
- Leaps can be unpacked into valid steps if challenged
- Expert judgment compressing known valid chains
- Intuition subject to verification
- Shortcuts acknowledged as needing validation
- Gap between evidence and conclusion is bridgeable

Output JSON with: tunneling_present (bool), severity (none/mild/moderate/severe), pattern (what reasoning pattern exists), barrier (what evidential barrier is bypassed), leap (what leap is made), justification_gap (what justification is missing), recommendation (legitimate_intuition/mild_shortcut/significant_tunneling/major_evidence_bypass/build_proper_evidence_chain)."""

EPISTEMIC_TUNNELING_PROMPT = """Detect epistemic tunneling:

Pattern: {pattern}
Barrier: {barrier}
Leap: {leap}
Justification: {justification}
Domain: {domain}
Context: {context}

Are evidential barriers being bypassed through unjustified leaps? Return ONLY valid JSON."""


class EpistemicTunnelingService:
    """Detects epistemic tunneling — bypassing evidential barriers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        pattern: str,
        *,
        barrier: str = "",
        leap: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic tunneling."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_TUNNELING_PROMPT.format(
                pattern=pattern,
                barrier=barrier or "Not specified",
                leap=leap or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_TUNNELING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "pattern": pattern[:200],
            "tunneling_present": data.get("tunneling_present", False),
            "severity": data.get("severity", ""),
            "barrier": data.get("barrier", ""),
            "leap": data.get("leap", ""),
            "justification_gap": data.get("justification_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
