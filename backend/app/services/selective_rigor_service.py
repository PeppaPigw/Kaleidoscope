"""SelectiveRigorService — Selective Rigor Detection.

Detects selective rigor — applying rigorous standards only to opposing
views while accepting one's own claims with minimal scrutiny.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

SELECTIVE_RIGOR_SYSTEM = """You are a selective rigor specialist. Given an evaluation pattern, assess whether rigor is being applied asymmetrically:

Key concepts:
- Selective rigor: rigor applied only to opposing views
- Asymmetric scrutiny: different scrutiny for own vs others' claims
- One-sided skepticism: skeptical of others but not self
- Standards asymmetry: high standards for opponents, low for self
- Motivated rigor: rigor serving confirmation not truth
- Scrutiny as weapon: rigor used to attack not understand
- Double standard in evaluation: different rules for different sides

When selective rigor IS present:
- Rigorous standards applied only to opposing views
- Own claims accepted with minimal scrutiny
- Asymmetric skepticism based on agreement
- High standards for opponents, low for allies
- Rigor serving confirmation not truth-seeking
- Scrutiny used as weapon against disagreement
- Double standard in evidence evaluation

When appropriate differential scrutiny is present:
- Rigor applied consistently regardless of source
- Own claims scrutinized as carefully as others'
- Skepticism proportionate to claim strength
- Standards consistent across positions
- Rigor serving truth regardless of direction
- Scrutiny applied to understand not attack
- Evaluation standards uniform

Output JSON with: selective_rigor_present (bool), severity (none/mild/moderate/severe), evaluation (what evaluation occurs), own_standard (standard applied to own claims), opposing_standard (standard applied to opposing), asymmetry (how standards differ), recommendation (consistent_rigor/mild_asymmetry/significant_selective_rigor/major_double_standard/apply_rigor_consistently)."""

SELECTIVE_RIGOR_PROMPT = """Detect selective rigor:

Evaluation pattern: {evaluation}
Standard for own claims: {own_standard}
Standard for opposing: {opposing_standard}
Asymmetry: {asymmetry}
Domain: {domain}
Context: {context}

Is rigor being applied asymmetrically — strict for opponents, lenient for self? Return ONLY valid JSON."""


class SelectiveRigorService:
    """Detects selective rigor — rigor applied only to opposing views."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evaluation: str,
        *,
        own_standard: str = "",
        opposing_standard: str = "",
        asymmetry: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect selective rigor."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=SELECTIVE_RIGOR_PROMPT.format(
                evaluation=evaluation,
                own_standard=own_standard or "Not specified",
                opposing_standard=opposing_standard or "Not specified",
                asymmetry=asymmetry or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=SELECTIVE_RIGOR_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evaluation": evaluation[:200],
            "selective_rigor_present": data.get("selective_rigor_present", False),
            "severity": data.get("severity", ""),
            "own_standard": data.get("own_standard", ""),
            "opposing_standard": data.get("opposing_standard", ""),
            "asymmetry": data.get("asymmetry", ""),
            "recommendation": data.get("recommendation", ""),
        }
