"""ComplexityDenialService — Complexity Denial Detection.

Detects complexity denial — refusing to acknowledge genuine
complexity in a system, insisting on simple explanations when
the phenomenon genuinely requires complex understanding.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPLEXITY_DENIAL_SYSTEM = """You are a complexity denial specialist. Given an explanation, assess whether genuine complexity is being inappropriately denied:

Key concepts:
- Complexity denial: refusing to acknowledge genuine complexity
- Forced simplicity: insisting on simple when complex is needed
- Reductionism excess: reducing beyond what's justified
- Monocausal insistence: one cause when many operate
- Linear thinking: assuming linearity in nonlinear systems
- Interaction blindness: ignoring how factors interact
- Emergence denial: refusing to acknowledge emergent properties

When complexity denial IS present:
- Genuine complexity refused acknowledgment
- Simple explanations forced on complex phenomena
- Reduction goes beyond what evidence supports
- Single causes insisted upon for multi-causal phenomena
- Linear models applied to nonlinear systems
- Interactions between factors ignored
- Emergent properties denied or dismissed

When simplification is appropriate:
- Simplification justified by evidence
- Complexity acknowledged even when simplified
- Reduction appropriate to purpose
- Key factors identified without denying others
- Linearity appropriate for the regime
- Interactions accounted for where significant
- Emergence recognized where present

Output JSON with: denial_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is given), complexity_denied (what complexity is denied), evidence_for_complexity (what shows complexity), forced_simplicity (what simplicity is forced), recommendation (appropriate_simplification/mild_complexity_underestimation/significant_complexity_denial/major_forced_simplicity/acknowledge_genuine_complexity)."""

COMPLEXITY_DENIAL_PROMPT = """Detect complexity denial:

Explanation: {explanation}
Phenomenon: {phenomenon}
Complexity evidence: {evidence}
Simplification justification: {justification}
Domain: {domain}
Context: {context}

Is genuine complexity being inappropriately denied or refused? Return ONLY valid JSON."""


class ComplexityDenialService:
    """Detects complexity denial — refusing to acknowledge genuine complexity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        phenomenon: str = "",
        evidence: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect complexity denial."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPLEXITY_DENIAL_PROMPT.format(
                explanation=explanation,
                phenomenon=phenomenon or "Not specified",
                evidence=evidence or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPLEXITY_DENIAL_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "denial_present": data.get("denial_present", False),
            "severity": data.get("severity", ""),
            "complexity_denied": data.get("complexity_denied", ""),
            "evidence_for_complexity": data.get("evidence_for_complexity", ""),
            "forced_simplicity": data.get("forced_simplicity", ""),
            "recommendation": data.get("recommendation", ""),
        }
