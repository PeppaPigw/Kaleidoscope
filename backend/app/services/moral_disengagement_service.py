"""MoralDisengagementService — Moral Disengagement Detection.

Detects moral disengagement — cognitive mechanisms that allow
people to behave unethically without feeling guilty. Bandura
(1999). Includes moral justification, euphemistic labeling,
displacement of responsibility, diffusion of responsibility,
dehumanization, and attribution of blame to victims.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

MORAL_DISENGAGEMENT_SYSTEM = """You are a moral disengagement specialist. Given a justification for potentially unethical behavior, assess whether moral disengagement mechanisms are being employed:

Key concepts (Bandura, 1999):
- Moral justification: reframing harmful acts as serving a moral purpose
- Euphemistic labeling: using sanitized language to obscure harm
- Advantageous comparison: comparing to worse acts to make own seem acceptable
- Displacement of responsibility: "I was just following orders"
- Diffusion of responsibility: "everyone does it" / "it's the system"
- Disregard of consequences: minimizing or ignoring harm caused
- Dehumanization: reducing victims' humanity to reduce guilt
- Attribution of blame: blaming victims for their own suffering

When moral disengagement IS present:
- Euphemisms hiding the nature of harmful actions
- "It's just business" to justify harm to people
- Blaming victims for consequences they didn't cause
- "Everyone does it" as justification for unethical behavior
- Minimizing harm: "it's not that bad" without evidence
- Dehumanizing language about those affected
- "I had no choice" when choices existed

When the justification IS legitimate:
- The action genuinely serves a greater good (documented, proportionate)
- Responsibility genuinely lies elsewhere (verified chain of command)
- The harm is genuinely minimal (evidence-based, not minimized)
- The comparison to worse alternatives is relevant and accurate
- The person acknowledges the ethical dimension while explaining constraints

Output JSON with: moral_disengagement_present (bool), severity (none/mild/moderate/severe), behavior (what behavior is being justified), justification (how is it being justified), mechanism (which disengagement mechanism — justification/euphemism/displacement/diffusion/minimization/dehumanization/blame), harm_caused (what harm results), harm_acknowledged (bool — is the harm acknowledged?), euphemisms_used (what sanitized language is used?), responsibility_displaced (bool — is responsibility shifted elsewhere?), victim_blamed (bool — are victims blamed?), recommendation (justification_legitimate/mild_disengagement/significant_rationalization/major_moral_disengagement/acknowledge_harm_directly)."""

MORAL_DISENGAGEMENT_PROMPT = """Detect moral disengagement:

Behavior: {behavior}
Justification: {justification}
Harm: {harm}
Language: {language}
Domain: {domain}
Context: {context}

Are moral disengagement mechanisms being used to rationalize harmful behavior? Return ONLY valid JSON."""


class MoralDisengagementService:
    """Detects moral disengagement — rationalizing unethical behavior."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        behavior: str,
        *,
        justification: str = "",
        harm: str = "",
        language: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect moral disengagement."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=MORAL_DISENGAGEMENT_PROMPT.format(
                behavior=behavior,
                justification=justification or "Not specified",
                harm=harm or "Not specified",
                language=language or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=MORAL_DISENGAGEMENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "behavior": behavior[:200],
            "moral_disengagement_present": data.get("moral_disengagement_present", False),
            "severity": data.get("severity", ""),
            "mechanism": data.get("mechanism", ""),
            "harm_caused": data.get("harm_caused", ""),
            "harm_acknowledged": data.get("harm_acknowledged", True),
            "euphemisms_used": data.get("euphemisms_used", ""),
            "responsibility_displaced": data.get("responsibility_displaced", False),
            "victim_blamed": data.get("victim_blamed", False),
            "recommendation": data.get("recommendation", ""),
        }
