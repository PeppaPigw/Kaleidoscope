"""KnowledgePowerConflationService — Knowledge-Power Conflation Detection.

Detects knowledge-power conflation — treating power to define
knowledge as evidence of truth, confusing authority to declare
with authority to know.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

KNOWLEDGE_POWER_CONFLATION_SYSTEM = """You are a knowledge-power conflation specialist. Given a knowledge claim, assess whether power is being confused with epistemic authority:

Key concepts:
- Knowledge-power conflation: power to define treated as truth
- Foucault's power/knowledge: power shapes what counts as knowledge
- Institutional truth: truth defined by institutional authority
- Might makes right epistemically: powerful define what's true
- Definitional authority: power to define confused with knowledge
- Hegemonic knowledge: dominant knowledge treated as only knowledge
- Power as evidence: being powerful treated as being right

When knowledge-power conflation IS present:
- Power to define treated as evidence of truth
- Institutional authority confused with epistemic authority
- Dominant position treated as proof of correctness
- Power to enforce a definition confused with truth of definition
- Hegemonic knowledge treated as only valid knowledge
- Challenges to powerful dismissed as wrong by definition
- Authority to declare confused with authority to know

When institutional knowledge is appropriate:
- Institutional authority based on genuine expertise
- Power and knowledge distinguished
- Institutional claims open to challenge
- Authority earned through epistemic merit
- Power acknowledged as separate from truth
- Institutional knowledge subject to revision
- Multiple sources of knowledge recognized

Output JSON with: conflation_present (bool), severity (none/mild/moderate/severe), claim (what is claimed), power_source (what power backs the claim), epistemic_basis (what epistemic basis exists), confusion (how power and knowledge are confused), recommendation (appropriate_institutional_knowledge/mild_authority_conflation/significant_power_knowledge_conflation/major_might_makes_right/distinguish_power_from_truth)."""

KNOWLEDGE_POWER_CONFLATION_PROMPT = """Detect knowledge-power conflation:

Claim: {claim}
Authority source: {authority}
Epistemic basis: {basis}
Power dynamics: {power}
Domain: {domain}
Context: {context}

Is power to define being confused with epistemic authority? Return ONLY valid JSON."""


class KnowledgePowerConflationService:
    """Detects knowledge-power conflation — confusing power with epistemic authority."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        claim: str,
        *,
        authority: str = "",
        basis: str = "",
        power: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect knowledge-power conflation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=KNOWLEDGE_POWER_CONFLATION_PROMPT.format(
                claim=claim,
                authority=authority or "Not specified",
                basis=basis or "Not specified",
                power=power or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=KNOWLEDGE_POWER_CONFLATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "claim": claim[:200],
            "conflation_present": data.get("conflation_present", False),
            "severity": data.get("severity", ""),
            "power_source": data.get("power_source", ""),
            "epistemic_basis": data.get("epistemic_basis", ""),
            "confusion": data.get("confusion", ""),
            "recommendation": data.get("recommendation", ""),
        }
