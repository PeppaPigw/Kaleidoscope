"""EpistemicLanguageFalseEquivalenceFramingService - Epistemic Language False Equivalence Framing Detection.

Detects epistemic language false equivalence framing - balanced language
that implies equivalence where evidence or stakes are not equivalent.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_LANGUAGE_FALSE_EQUIVALENCE_FRAMING_SYSTEM = """You are an epistemic language false equivalence framing specialist. Given balanced language framing that creates false equivalence, assess false equivalence framing:

Key concepts:
- Epistemic language false equivalence framing: balanced wording that falsely implies equal evidential status
- Balance as equivalence: treating symmetry of presentation as symmetry of truth
- Both-sides framing: framing positions as parallel regardless of evidence
- Weight of evidence ignored: failing to represent evidential imbalance
- Controversy manufacture: making settled or lopsided questions seem evenly disputed
- Symmetry laundering: laundering asymmetry through balanced language
- Proportion erasure: erasing differences in support, harm, or credibility

When false equivalence framing IS present:
- Balance implies equivalence
- Both-sides framing misleads
- Weight of evidence ignored
- Controversy manufactured
- Symmetry launders asymmetry
- Proportions erased
- Weak positions elevated

When no false equivalence framing:
- Balance does not imply equality
- Evidential asymmetry shown
- Weight of evidence represented
- Controversy not manufactured
- Symmetry avoided when misleading
- Proportions preserved
- Credibility differences clear

Output JSON with: false_equivalence_framing_detected (bool), severity (none/mild/moderate/severe), balance_as_equivalence (what balance implies), both_sides_framing (what both-sides framing used), weight_of_evidence_ignored (what evidence weight ignored), controversy_manufacture (what controversy manufactured), recommendation (no_false_equivalence_framing/mild_weighting_clarification/significant_evidence_rebalancing/major_intensive_frame_correction/emergency_complete_false_equivalence_framing)."""

EPISTEMIC_LANGUAGE_FALSE_EQUIVALENCE_FRAMING_PROMPT = """Detect epistemic language false equivalence framing:

Balance as equivalence: {balance_as_equivalence}
Both-sides framing: {both_sides_framing}
Weight of evidence ignored: {weight_of_evidence_ignored}
Controversy manufacture: {controversy_manufacture}
Domain: {domain}
Context: {context}

Is balanced language creating false equivalence? Return ONLY valid JSON."""


class EpistemicLanguageFalseEquivalenceFramingService:
    """Detects epistemic language false equivalence framing - misleading balance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        balance_as_equivalence: str,
        *,
        both_sides_framing: str = "",
        weight_of_evidence_ignored: str = "",
        controversy_manufacture: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic language false equivalence framing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_LANGUAGE_FALSE_EQUIVALENCE_FRAMING_PROMPT.format(
                balance_as_equivalence=balance_as_equivalence,
                both_sides_framing=both_sides_framing or "Not specified",
                weight_of_evidence_ignored=weight_of_evidence_ignored or "Not specified",
                controversy_manufacture=controversy_manufacture or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_LANGUAGE_FALSE_EQUIVALENCE_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "balance_as_equivalence": balance_as_equivalence[:200],
            "false_equivalence_framing_detected": data.get("false_equivalence_framing_detected", False),
            "severity": data.get("severity", ""),
            "both_sides_framing": data.get("both_sides_framing", ""),
            "weight_of_evidence_ignored": data.get("weight_of_evidence_ignored", ""),
            "controversy_manufacture": data.get("controversy_manufacture", ""),
            "recommendation": data.get("recommendation", ""),
        }
