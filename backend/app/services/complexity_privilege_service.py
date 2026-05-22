"""ComplexityPrivilegeService — Complexity Privilege Detection.

Detects complexity privilege — assuming that more complex explanations
are more sophisticated or correct, when simpler ones may be more
accurate. The inverse of Occam's razor.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COMPLEXITY_PRIVILEGE_SYSTEM = """You are a complexity privilege specialist. Given an explanation choice, assess whether complexity is being privileged over simplicity without justification:

Key concepts:
- Complexity privilege: preferring complex explanations because they seem deeper
- Anti-Occam: choosing complex over simple without justification
- Sophistication bias: equating complexity with intelligence
- Epicycle thinking: adding complexity to save a theory
- Rube Goldberg explanation: unnecessarily complex causal chains
- Depth illusion: complexity mistaken for profundity
- Parsimony neglect: ignoring simpler adequate explanations

When complexity privilege IS present:
- Complex explanation chosen over equally adequate simple one
- Complexity treated as evidence of sophistication
- Simpler explanation dismissed as naive without testing
- Additional complexity adds no explanatory power
- Preference for complex driven by aesthetics, not evidence
- Occam's razor violated without justification
- Complexity serves social function (appearing smart)

When complex explanation is appropriate:
- Complexity genuinely needed to explain the data
- Simpler explanations tested and found inadequate
- Additional complexity adds explanatory power
- Complexity reflects genuine complexity of phenomenon
- Parsimony considered but insufficient
- Complexity justified by specific evidence
- Simple explanation would miss important features

Output JSON with: privilege_present (bool), severity (none/mild/moderate/severe), explanation (what is explained), complex_version (the complex explanation), simple_version (the simpler alternative), added_value (what complexity adds), recommendation (appropriate_complexity/mild_complexity_preference/significant_complexity_privilege/major_anti_parsimony/prefer_simpler_explanation)."""

COMPLEXITY_PRIVILEGE_PROMPT = """Detect complexity privilege:

Explanation: {explanation}
Complex version: {complex}
Simple alternative: {simple}
Justification: {justification}
Domain: {domain}
Context: {context}

Is complexity being privileged over simplicity without adequate justification? Return ONLY valid JSON."""


class ComplexityPrivilegeService:
    """Detects complexity privilege — preferring complex explanations without justification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        complex: str = "",
        simple: str = "",
        justification: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect complexity privilege."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COMPLEXITY_PRIVILEGE_PROMPT.format(
                explanation=explanation,
                complex=complex or "Not specified",
                simple=simple or "Not specified",
                justification=justification or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COMPLEXITY_PRIVILEGE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "privilege_present": data.get("privilege_present", False),
            "severity": data.get("severity", ""),
            "complex_version": data.get("complex_version", ""),
            "simple_version": data.get("simple_version", ""),
            "added_value": data.get("added_value", ""),
            "recommendation": data.get("recommendation", ""),
        }
