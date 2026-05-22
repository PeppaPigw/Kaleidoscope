"""ConclusionShoppingService — Conclusion Shopping Detection.

Detects conclusion shopping — searching for evidence or arguments
to support a predetermined conclusion, where inquiry serves
justification rather than discovery.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

CONCLUSION_SHOPPING_SYSTEM = """You are a conclusion shopping specialist. Given a reasoning process, assess whether evidence is being sought to support a predetermined conclusion:

Key concepts:
- Conclusion shopping: seeking evidence for predetermined conclusion
- Reverse reasoning: conclusion first, evidence second
- Justification seeking: inquiry serving justification not discovery
- Evidence shopping: selecting evidence to fit conclusion
- Argument construction: building case for decided conclusion
- Motivated search: search directed by desired outcome
- Post-hoc rationalization: finding reasons after deciding

When conclusion shopping IS present:
- Conclusion determined before evidence gathered
- Evidence sought to support not test conclusion
- Disconfirming evidence not sought or ignored
- Search directed by desired outcome
- Arguments constructed to justify not discover
- Inquiry serving justification not understanding
- Reasoning working backward from conclusion

When directed inquiry is appropriate:
- Hypothesis tested not just confirmed
- Both confirming and disconfirming evidence sought
- Conclusion open to revision by evidence
- Search balanced across possibilities
- Arguments evaluated not just constructed
- Inquiry genuinely open to surprise
- Reasoning following evidence to conclusion

Output JSON with: shopping_present (bool), severity (none/mild/moderate/severe), reasoning (what reasoning occurs), predetermined (what conclusion is predetermined), evidence_sought (what evidence is sought), evidence_ignored (what evidence is ignored), recommendation (genuine_inquiry/mild_confirmation_seeking/significant_conclusion_shopping/major_reverse_reasoning/open_inquiry_to_genuine_discovery)."""

CONCLUSION_SHOPPING_PROMPT = """Detect conclusion shopping:

Reasoning process: {reasoning}
Conclusion reached: {conclusion}
Evidence sought: {sought}
Evidence ignored: {ignored}
Domain: {domain}
Context: {context}

Is evidence being sought to support a predetermined conclusion rather than genuine inquiry? Return ONLY valid JSON."""


class ConclusionShoppingService:
    """Detects conclusion shopping — seeking evidence for predetermined conclusions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        reasoning: str,
        *,
        conclusion: str = "",
        sought: str = "",
        ignored: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect conclusion shopping."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CONCLUSION_SHOPPING_PROMPT.format(
                reasoning=reasoning,
                conclusion=conclusion or "Not specified",
                sought=sought or "Not specified",
                ignored=ignored or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=CONCLUSION_SHOPPING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "reasoning": reasoning[:200],
            "shopping_present": data.get("shopping_present", False),
            "severity": data.get("severity", ""),
            "predetermined": data.get("predetermined", ""),
            "evidence_sought": data.get("evidence_sought", ""),
            "evidence_ignored": data.get("evidence_ignored", ""),
            "recommendation": data.get("recommendation", ""),
        }
