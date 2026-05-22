"""EpistemicAlchemyService — Epistemic Alchemy Detection.

Detects epistemic alchemy — attempting to transmute low-quality
evidence into high-quality conclusions through rhetorical means.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ALCHEMY_SYSTEM = """You are an epistemic alchemy specialist. Given a reasoning pattern, assess whether low-quality evidence is being transmuted into high-quality conclusions:

Key concepts:
- Epistemic alchemy: transmuting low-quality evidence into high conclusions
- Evidence inflation: inflating evidence quality through rhetoric
- Rhetorical transmutation: using rhetoric to upgrade evidence
- Quality laundering: laundering low-quality evidence
- Conclusion overreach: conclusions far exceeding evidence
- Appearance of rigor: appearing rigorous without substance
- Gold from lead: claiming gold conclusions from lead evidence

When epistemic alchemy IS present:
- Low-quality evidence transmuted into high-quality conclusions
- Evidence quality inflated through rhetorical means
- Rhetoric used to upgrade evidence quality
- Low-quality evidence laundered to appear high-quality
- Conclusions far exceeding what evidence supports
- Appearing rigorous without substantive evidence
- Claiming strong conclusions from weak evidence

When genuine reasoning is present:
- Conclusions proportionate to evidence quality
- Evidence quality honestly represented
- Rhetoric matches evidence strength
- Evidence quality transparent
- Conclusions appropriately modest given evidence
- Genuine rigor with substantive evidence
- Conclusions matched to evidence strength

Output JSON with: alchemy_present (bool), severity (none/mild/moderate/severe), evidence (what low-quality evidence is used), transmutation (how transmutation occurs), conclusion (what inflated conclusion results), rhetoric (what rhetoric is used), recommendation (genuine_reasoning/mild_overreach/significant_alchemy/major_evidence_laundering/match_conclusions_to_evidence)."""

EPISTEMIC_ALCHEMY_PROMPT = """Detect epistemic alchemy:

Evidence: {evidence}
Transmutation: {transmutation}
Conclusion: {conclusion}
Rhetoric: {rhetoric}
Domain: {domain}
Context: {context}

Is low-quality evidence being transmuted into high-quality conclusions through rhetoric? Return ONLY valid JSON."""


class EpistemicAlchemyService:
    """Detects epistemic alchemy — transmuting low evidence into high conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        evidence: str,
        *,
        transmutation: str = "",
        conclusion: str = "",
        rhetoric: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic alchemy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ALCHEMY_PROMPT.format(
                evidence=evidence,
                transmutation=transmutation or "Not specified",
                conclusion=conclusion or "Not specified",
                rhetoric=rhetoric or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ALCHEMY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "evidence": evidence[:200],
            "alchemy_present": data.get("alchemy_present", False),
            "severity": data.get("severity", ""),
            "transmutation": data.get("transmutation", ""),
            "conclusion": data.get("conclusion", ""),
            "rhetoric": data.get("rhetoric", ""),
            "recommendation": data.get("recommendation", ""),
        }
