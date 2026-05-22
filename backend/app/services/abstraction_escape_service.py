"""AbstractionEscapeService — Abstraction Escape Detection.

Detects abstraction escape — using abstraction to escape accountability
for concrete harms, where moving to a higher level of abstraction
makes specific damage invisible or unaddressable.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ABSTRACTION_ESCAPE_SYSTEM = """You are an abstraction escape specialist. Given a discourse, assess whether abstraction is being used to escape accountability:

Key concepts:
- Abstraction escape: using abstraction to avoid accountability
- Concrete harm invisibility: abstraction hiding specific damage
- Level shifting: moving to abstract level to avoid concrete
- Accountability dissolution: responsibility lost in abstraction
- Statistical hiding: individual harms hidden in aggregates
- Systemic language escape: system talk avoiding personal responsibility
- Theoretical retreat: retreating to theory when practice challenged

When abstraction escape IS present:
- Abstraction used to make concrete harms invisible
- Level of discourse shifted to avoid accountability
- Specific damage hidden behind general language
- Responsibility dissolved through abstraction
- Individual harms hidden in statistical aggregates
- Systemic language used to avoid personal accountability
- Theory invoked to escape practical challenges

When abstraction is appropriate:
- Abstraction serves understanding not evasion
- Concrete specifics available alongside abstract
- Accountability preserved at appropriate level
- Abstraction illuminates rather than hides
- General patterns identified without erasing specifics
- System-level analysis complements individual accountability
- Theory connected to practice

Output JSON with: escape_present (bool), severity (none/mild/moderate/severe), discourse (what is discussed), abstraction_used (what abstraction is employed), concrete_hidden (what concrete reality is hidden), accountability_lost (what accountability is avoided), recommendation (appropriate_abstraction/mild_level_shifting/significant_abstraction_escape/major_accountability_dissolution/connect_abstract_to_concrete)."""

ABSTRACTION_ESCAPE_PROMPT = """Detect abstraction escape:

Discourse: {discourse}
Abstraction used: {abstraction}
Concrete reality: {concrete}
Accountability: {accountability}
Domain: {domain}
Context: {context}

Is abstraction being used to escape accountability for concrete harms? Return ONLY valid JSON."""


class AbstractionEscapeService:
    """Detects abstraction escape — using abstraction to avoid accountability."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        discourse: str,
        *,
        abstraction: str = "",
        concrete: str = "",
        accountability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect abstraction escape."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ABSTRACTION_ESCAPE_PROMPT.format(
                discourse=discourse,
                abstraction=abstraction or "Not specified",
                concrete=concrete or "Not specified",
                accountability=accountability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ABSTRACTION_ESCAPE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "discourse": discourse[:200],
            "escape_present": data.get("escape_present", False),
            "severity": data.get("severity", ""),
            "abstraction_used": data.get("abstraction_used", ""),
            "concrete_hidden": data.get("concrete_hidden", ""),
            "accountability_lost": data.get("accountability_lost", ""),
            "recommendation": data.get("recommendation", ""),
        }
