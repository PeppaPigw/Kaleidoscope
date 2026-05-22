"""EpistemicDevelopmentalDelayService — Epistemic Developmental Delay Detection.

Detects epistemic developmental delay — intellectual systems not reaching
expected milestones at appropriate times.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_DEVELOPMENTAL_DELAY_SYSTEM = """You are an epistemic developmental delay specialist. Given intellectual systems not reaching milestones, assess delay:

Key concepts:
- Epistemic developmental delay: not reaching milestones on time
- Gross motor: large-scale intellectual movement
- Fine motor: precise intellectual manipulation
- Language: intellectual communication development
- Social-emotional: intellectual relationship development
- Cognitive: intellectual thinking development
- Global delay: behind in multiple domains

When epistemic developmental delay IS present:
- Not reaching expected milestones
- Large-scale movement behind
- Precise manipulation behind
- Communication development behind
- Relationship development behind
- Thinking development behind
- Behind in multiple domains

When no developmental delay:
- Meeting milestones on time
- Normal large-scale movement
- Normal precise manipulation
- Normal communication
- Normal relationships
- Normal thinking development
- On track across domains

Output JSON with: developmental_delay (bool), severity (none/mild/moderate/severe), milestone_status (what achievement level), delay_domains (what areas affected), global_vs_specific (what breadth), intervention_need (what support required), recommendation (no_delay/mild_monitoring/significant_early_intervention/major_intensive_therapy/comprehensive_developmental_program)."""

EPISTEMIC_DEVELOPMENTAL_DELAY_PROMPT = """Detect epistemic developmental delay:

Milestone status: {milestone_status}
Delay domains: {delay_domains}
Global vs specific: {global_vs_specific}
Intervention need: {intervention_need}
Domain: {domain}
Context: {context}

Is the intellectual system not reaching expected milestones at appropriate times? Return ONLY valid JSON."""


class EpistemicDevelopmentalDelayService:
    """Detects epistemic developmental delay — not reaching milestones on time."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        milestone_status: str,
        *,
        delay_domains: str = "",
        global_vs_specific: str = "",
        intervention_need: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic developmental delay."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_DEVELOPMENTAL_DELAY_PROMPT.format(
                milestone_status=milestone_status,
                delay_domains=delay_domains or "Not specified",
                global_vs_specific=global_vs_specific or "Not specified",
                intervention_need=intervention_need or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_DEVELOPMENTAL_DELAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "milestone_status": milestone_status[:200],
            "developmental_delay": data.get("developmental_delay", False),
            "severity": data.get("severity", ""),
            "delay_domains": data.get("delay_domains", ""),
            "global_vs_specific": data.get("global_vs_specific", ""),
            "intervention_need": data.get("intervention_need", ""),
            "recommendation": data.get("recommendation", ""),
        }
