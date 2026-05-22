"""SymmetryBiasService — Symmetry Bias Detection.

Detects symmetry bias — preferring symmetric explanations regardless
of whether evidence supports symmetry.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SYMMETRY_BIAS_SYSTEM = """You are a symmetry bias specialist. Given an explanation or argument, assess whether symmetry is being imposed without evidential support:

Key concepts:
- Symmetry bias: preferring symmetric explanations without evidence
- False balance: imposing balance where none exists
- Both-sides-ism: treating asymmetric situations as symmetric
- Proportionality assumption: assuming proportional causes for effects
- Mirror image fallacy: assuming opposing sides are mirror images
- Equilibrium assumption: assuming systems tend toward balance
- Duality imposition: imposing dualities on non-dual phenomena

When symmetry bias IS present:
- Symmetric explanation preferred without evidence
- False balance imposed on asymmetric reality
- Both sides treated equally despite asymmetric evidence
- Proportional causes assumed without basis
- Mirror image structure imposed on different phenomena
- Equilibrium assumed without evidence
- Dualities imposed on non-dual phenomena

When genuine symmetry is present:
- Symmetry supported by evidence
- Balance reflecting actual proportions
- Both sides treated according to evidence
- Proportionality demonstrated not assumed
- Mirror structure reflecting genuine similarity
- Equilibrium demonstrated empirically
- Dualities reflecting genuine structure

Output JSON with: symmetry_bias_present (bool), severity (none/mild/moderate/severe), explanation (what explanation is preferred), imposed_symmetry (what symmetry is imposed), evidence_status (what evidence actually shows), asymmetric_reality (what asymmetric reality exists), recommendation (genuine_symmetry/mild_balance_preference/significant_symmetry_bias/major_false_balance/follow_evidence_not_aesthetics)."""

SYMMETRY_BIAS_PROMPT = """Detect symmetry bias:

Explanation: {explanation}
Imposed symmetry: {symmetry}
Evidence: {evidence}
Asymmetric reality: {reality}
Domain: {domain}
Context: {context}

Is symmetry being imposed without evidential support? Return ONLY valid JSON."""


class SymmetryBiasService:
    """Detects symmetry bias — preferring symmetric explanations without evidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        symmetry: str = "",
        evidence: str = "",
        reality: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect symmetry bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SYMMETRY_BIAS_PROMPT.format(
                explanation=explanation,
                symmetry=symmetry or "Not specified",
                evidence=evidence or "Not specified",
                reality=reality or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SYMMETRY_BIAS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "symmetry_bias_present": data.get("symmetry_bias_present", False),
            "severity": data.get("severity", ""),
            "imposed_symmetry": data.get("imposed_symmetry", ""),
            "evidence_status": data.get("evidence_status", ""),
            "asymmetric_reality": data.get("asymmetric_reality", ""),
            "recommendation": data.get("recommendation", ""),
        }
