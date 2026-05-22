"""FalseEquivalenceFramingService — False Equivalence Framing Detection.

Detects false equivalence framing — presenting unequal things as
equivalent through framing choices, giving equal weight to
positions with vastly different evidential support.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FALSE_EQUIVALENCE_FRAMING_SYSTEM = """You are a false equivalence framing specialist. Given a comparison or presentation, assess whether unequal things are being framed as equivalent:

Key concepts:
- False equivalence: treating unequal things as equal
- Both-sides framing: giving equal weight to unequal positions
- Balance bias: artificial balance between strong and weak positions
- Symmetry imposition: forcing symmetry on asymmetric situations
- Weight of evidence: ignoring differential evidential support
- False balance: media presenting fringe views alongside mainstream
- Moral equivalence: equating morally different actions

When false equivalence framing IS present:
- Unequal positions given equal weight or space
- Vastly different evidence bases treated as equivalent
- Artificial symmetry imposed on asymmetric situations
- "Both sides" framing obscures real differences
- Fringe positions elevated to equal mainstream
- Moral differences flattened through equivalence framing
- Differential evidence ignored in presentation

When comparison is appropriate:
- Positions genuinely comparable in evidence/merit
- Differences in evidence base acknowledged
- Asymmetries preserved in presentation
- Weight given proportional to evidence
- Genuine disagreement among qualified experts
- Comparison illuminates rather than obscures
- Differences in kind acknowledged

Output JSON with: equivalence_present (bool), severity (none/mild/moderate/severe), comparison (what is being compared), asymmetry (what real differences exist), framing (how equivalence is created), evidence_gap (how evidence differs between positions), recommendation (appropriate_comparison/mild_false_balance/significant_equivalence_framing/major_false_equivalence/acknowledge_asymmetry)."""

FALSE_EQUIVALENCE_FRAMING_PROMPT = """Detect false equivalence framing:

Presentation: {presentation}
Position A: {position_a}
Position B: {position_b}
Evidence comparison: {evidence}
Domain: {domain}
Context: {context}

Are unequal things being presented as equivalent through framing? Return ONLY valid JSON."""


class FalseEquivalenceFramingService:
    """Detects false equivalence framing — unequal things presented as equivalent."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        presentation: str,
        *,
        position_a: str = "",
        position_b: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect false equivalence framing."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FALSE_EQUIVALENCE_FRAMING_PROMPT.format(
                presentation=presentation,
                position_a=position_a or "Not specified",
                position_b=position_b or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FALSE_EQUIVALENCE_FRAMING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "presentation": presentation[:200],
            "equivalence_present": data.get("equivalence_present", False),
            "severity": data.get("severity", ""),
            "asymmetry": data.get("asymmetry", ""),
            "framing": data.get("framing", ""),
            "evidence_gap": data.get("evidence_gap", ""),
            "recommendation": data.get("recommendation", ""),
        }
