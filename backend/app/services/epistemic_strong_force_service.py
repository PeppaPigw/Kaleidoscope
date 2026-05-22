"""EpistemicStrongForceService — Epistemic Strong Force Detection.

Detects epistemic strong force — a force that binds ideas together more
tightly the further apart they are pulled, preventing separation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_STRONG_FORCE_SYSTEM = """You are an epistemic strong force specialist. Given an intellectual binding, assess whether ideas are bound more tightly at distance:

Key concepts:
- Epistemic strong force: force binding ideas more tightly at distance
- Gluon: carrier of the binding force
- Color confinement: bound ideas must be color-neutral
- Asymptotic freedom: force weakening at close range
- Flux tube: string-like force between separated ideas
- Running coupling: force strength changing with distance
- Residual force: leftover binding between composites

When epistemic strong force IS present:
- Force binding ideas more tightly when pulled apart
- Specific carriers of the binding force
- Bound combinations must satisfy neutrality
- Force weakening at very close examination
- String-like connection between separated ideas
- Force strength changing with intellectual distance
- Leftover binding between composite ideas

When weak binding is present:
- Force weakening with distance
- No specific binding carriers
- No neutrality requirement
- Force constant at all ranges
- No string-like connections
- Constant force strength
- No residual binding

Output JSON with: strong_force_present (bool), severity (none/mild/moderate/severe), gluon (what binding carrier), confinement (what neutrality requirement), asymptotic_freedom (what close-range weakening), flux_tube (what string-like connection), recommendation (weak_binding/mild_strong_force/significant_strong_force/major_confinement/work_within_bound_states)."""

EPISTEMIC_STRONG_FORCE_PROMPT = """Detect epistemic strong force:

Gluon: {gluon}
Confinement: {confinement}
Asymptotic freedom: {asymptotic_freedom}
Flux tube: {flux_tube}
Domain: {domain}
Context: {context}

Is a force binding ideas together more tightly the further apart they are pulled, preventing separation? Return ONLY valid JSON."""


class EpistemicStrongForceService:
    """Detects epistemic strong force — force binding ideas more tightly at distance."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        gluon: str,
        *,
        confinement: str = "",
        asymptotic_freedom: str = "",
        flux_tube: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic strong force."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_STRONG_FORCE_PROMPT.format(
                gluon=gluon,
                confinement=confinement or "Not specified",
                asymptotic_freedom=asymptotic_freedom or "Not specified",
                flux_tube=flux_tube or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_STRONG_FORCE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "gluon": gluon[:200],
            "strong_force_present": data.get("strong_force_present", False),
            "severity": data.get("severity", ""),
            "confinement": data.get("confinement", ""),
            "asymptotic_freedom": data.get("asymptotic_freedom", ""),
            "flux_tube": data.get("flux_tube", ""),
            "recommendation": data.get("recommendation", ""),
        }
