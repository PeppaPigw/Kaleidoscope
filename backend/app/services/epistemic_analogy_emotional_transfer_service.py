"""EpistemicAnalogyEmotionalTransferService — Epistemic Analogy Emotional Transfer Detection.

Detects epistemic analogy emotional transfer — analogies chosen to transfer emotional
valence rather than illuminate structural relationships between domains.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_ANALOGY_EMOTIONAL_TRANSFER_SYSTEM = """You are an epistemic analogy emotional transfer specialist. Given emotionally-loaded analogies, assess valence transfer:

Key concepts:
- Epistemic emotional transfer: analogies chosen for emotional impact
- Valence hijacking: using analogy to transfer positive/negative feelings
- Guilt by association: negative analogy creating guilt transfer
- Glory by association: positive analogy creating unearned positive valence
- Emotional framing: analogy chosen to frame emotionally not structurally
- Visceral override: emotional response from analogy overriding analysis
- Connotation smuggling: smuggling connotations through analogy choice

When epistemic emotional transfer IS present:
- Analogies chosen for emotional impact
- Valence being transferred
- Guilt by association operating
- Glory by association operating
- Emotional framing over structural
- Visceral responses overriding analysis
- Connotations smuggled

When no emotional transfer:
- Analogies chosen for illumination
- Valence neutral
- No guilt transfer
- No glory transfer
- Structural framing primary
- Analysis not overridden
- Connotations acknowledged

Output JSON with: emotional_transfer_detected (bool), severity (none/mild/moderate/severe), valence_hijacking (what valence transferred), guilt_by_association (what guilt transferred), visceral_override (what visceral responses overriding), connotation_smuggling (what connotations smuggled), recommendation (no_emotional_transfer/mild_valence_awareness/significant_structural_refocusing/major_intensive_analogy_neutralization/emergency_complete_emotional_transfer)."""

EPISTEMIC_ANALOGY_EMOTIONAL_TRANSFER_PROMPT = """Detect epistemic analogy emotional transfer:

Valence hijacking: {valence_hijacking}
Guilt by association: {guilt_by_association}
Visceral override: {visceral_override}
Connotation smuggling: {connotation_smuggling}
Domain: {domain}
Context: {context}

Are analogies chosen to transfer emotional valence rather than illuminate structure? Return ONLY valid JSON."""


class EpistemicAnalogyEmotionalTransferService:
    """Detects epistemic analogy emotional transfer — valence over structure."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        valence_hijacking: str,
        *,
        guilt_by_association: str = "",
        visceral_override: str = "",
        connotation_smuggling: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic analogy emotional transfer."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_ANALOGY_EMOTIONAL_TRANSFER_PROMPT.format(
                valence_hijacking=valence_hijacking,
                guilt_by_association=guilt_by_association or "Not specified",
                visceral_override=visceral_override or "Not specified",
                connotation_smuggling=connotation_smuggling or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_ANALOGY_EMOTIONAL_TRANSFER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "valence_hijacking": valence_hijacking[:200],
            "emotional_transfer_detected": data.get("emotional_transfer_detected", False),
            "severity": data.get("severity", ""),
            "guilt_by_association": data.get("guilt_by_association", ""),
            "visceral_override": data.get("visceral_override", ""),
            "connotation_smuggling": data.get("connotation_smuggling", ""),
            "recommendation": data.get("recommendation", ""),
        }
