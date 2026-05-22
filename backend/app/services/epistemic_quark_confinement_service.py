"""EpistemicQuarkConfinementService — Epistemic Quark Confinement Detection.

Detects epistemic quark confinement — ideas that can never be isolated
individually, only observed in bound combinations with other ideas.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_QUARK_CONFINEMENT_SYSTEM = """You are an epistemic quark confinement specialist. Given an intellectual concept, assess whether ideas can never be isolated individually:

Key concepts:
- Epistemic quark confinement: ideas never isolated, only in combinations
- Color charge: hidden property requiring neutralization
- Hadronization: free ideas immediately binding into composites
- String breaking: attempting to separate creates new pairs
- Asymptotic freedom: ideas free at very short distances
- Flux tube: force increasing with separation
- Jet: spray of bound ideas from high-energy separation attempt

When epistemic quark confinement IS present:
- Ideas never observable in isolation
- Hidden properties requiring combination for neutralization
- Free ideas immediately binding into composites
- Separation attempts creating new bound pairs
- Ideas appearing free only at very close examination
- Force between ideas increasing with distance
- Sprays of bound ideas from forced separation

When free ideas is present:
- Ideas freely observable in isolation
- No hidden properties requiring combination
- Ideas stable alone
- Separation succeeding cleanly
- Ideas equally free at all distances
- Force decreasing with distance
- Clean separation without sprays

Output JSON with: quark_confinement_present (bool), severity (none/mild/moderate/severe), color_charge (what hidden property), hadronization (what binding), string_breaking (what pair creation), asymptotic_freedom (what close-range freedom), recommendation (free_ideas/mild_confinement/significant_quark_confinement/major_binding/accept_composite_nature)."""

EPISTEMIC_QUARK_CONFINEMENT_PROMPT = """Detect epistemic quark confinement:

Color charge: {color_charge}
Hadronization: {hadronization}
String breaking: {string_breaking}
Asymptotic freedom: {asymptotic_freedom}
Domain: {domain}
Context: {context}

Are ideas unable to be isolated individually, only observable in bound combinations? Return ONLY valid JSON."""


class EpistemicQuarkConfinementService:
    """Detects epistemic quark confinement — ideas never isolated, only in combinations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        color_charge: str,
        *,
        hadronization: str = "",
        string_breaking: str = "",
        asymptotic_freedom: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic quark confinement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_QUARK_CONFINEMENT_PROMPT.format(
                color_charge=color_charge,
                hadronization=hadronization or "Not specified",
                string_breaking=string_breaking or "Not specified",
                asymptotic_freedom=asymptotic_freedom or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_QUARK_CONFINEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "color_charge": color_charge[:200],
            "quark_confinement_present": data.get("quark_confinement_present", False),
            "severity": data.get("severity", ""),
            "hadronization": data.get("hadronization", ""),
            "string_breaking": data.get("string_breaking", ""),
            "asymptotic_freedom": data.get("asymptotic_freedom", ""),
            "recommendation": data.get("recommendation", ""),
        }
