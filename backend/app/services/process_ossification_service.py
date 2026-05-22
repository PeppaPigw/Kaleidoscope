"""ProcessOssificationService — Process Ossification Detection.

Detects process ossification — processes becoming rigid and preventing
adaptation, where procedures designed for past conditions persist
unchanged despite changed circumstances.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

PROCESS_OSSIFICATION_SYSTEM = """You are a process ossification specialist. Given an organizational process, assess whether it has become rigid and maladaptive:

Key concepts:
- Process ossification: processes becoming rigid and unadaptable
- Procedural rigidity: inability to modify procedures
- Context blindness: processes unchanged despite changed context
- Ritual compliance: following process without understanding purpose
- Adaptation failure: inability to evolve with circumstances
- Bureaucratic inertia: processes persisting through inertia alone
- Purpose loss: original purpose forgotten, process continues

When process ossification IS present:
- Processes rigid despite changed circumstances
- Procedures followed without understanding purpose
- Adaptation to new conditions prevented by process
- Original context for process no longer applies
- Process continues through inertia not value
- Modification of process treated as violation
- Purpose of process forgotten or irrelevant

When process stability is appropriate:
- Process serves current needs effectively
- Stability provides valuable predictability
- Process regularly reviewed for relevance
- Modifications possible when justified
- Purpose of process understood and current
- Process adapted when context changes
- Stability chosen deliberately not by default

Output JSON with: ossification_present (bool), severity (none/mild/moderate/severe), process (what process is analyzed), original_purpose (what purpose it served), current_context (what context has changed), rigidity (how process resists change), recommendation (appropriate_process_stability/mild_procedural_inertia/significant_process_ossification/major_adaptation_failure/review_and_adapt_processes)."""

PROCESS_OSSIFICATION_PROMPT = """Detect process ossification:

Process: {process}
Original purpose: {purpose}
Current context: {current}
Adaptation attempts: {adaptation}
Domain: {domain}
Context: {context}

Has this process become rigid and maladaptive? Return ONLY valid JSON."""


class ProcessOssificationService:
    """Detects process ossification — processes becoming rigid and preventing adaptation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        process: str,
        *,
        purpose: str = "",
        current: str = "",
        adaptation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect process ossification."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=PROCESS_OSSIFICATION_PROMPT.format(
                process=process,
                purpose=purpose or "Not specified",
                current=current or "Not specified",
                adaptation=adaptation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=PROCESS_OSSIFICATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "process": process[:200],
            "ossification_present": data.get("ossification_present", False),
            "severity": data.get("severity", ""),
            "original_purpose": data.get("original_purpose", ""),
            "current_context": data.get("current_context", ""),
            "rigidity": data.get("rigidity", ""),
            "recommendation": data.get("recommendation", ""),
        }
