"""TestimonialSmotheringService — Testimonial Smothering Detection.

Detects testimonial smothering — self-censorship due to anticipated
credibility deficits, where speakers truncate their testimony
because they expect not to be believed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TESTIMONIAL_SMOTHERING_SYSTEM = """You are a testimonial smothering specialist. Given a communication context, assess whether self-censorship is occurring due to anticipated credibility deficits:

Key concepts:
- Testimonial smothering: self-censorship anticipating disbelief
- Anticipated credibility deficit: expecting not to be believed
- Preemptive silence: not speaking because of expected reception
- Truncated testimony: sharing less than known
- Self-censorship: withholding knowledge due to social dynamics
- Unsafe testimony: environments where sharing is risky
- Credibility anticipation: adjusting testimony to expected reception

When testimonial smothering IS present:
- Self-censorship due to anticipated disbelief
- Knowledge withheld because of expected reception
- Testimony truncated to avoid credibility challenges
- Speakers sharing less than they know
- Environments making full testimony risky
- Anticipated credibility deficit causing silence
- Knowledge lost to preemptive self-censorship

When appropriate discretion is present:
- Silence based on relevance not fear
- Discretion serving communication not avoidance
- Withholding based on appropriateness not anticipated disbelief
- Testimony calibrated to context not credibility fear
- Environments supporting full testimony
- Silence chosen not forced by anticipated reception
- Discretion serving rather than suppressing knowledge

Output JSON with: smothering_present (bool), severity (none/mild/moderate/severe), context (what communication context), withheld (what is withheld), anticipated_deficit (what credibility deficit is anticipated), environment (what environment causes smothering), recommendation (safe_environment/mild_self_censorship/significant_testimonial_smothering/major_knowledge_suppression/create_safe_testimony_environments)."""

TESTIMONIAL_SMOTHERING_PROMPT = """Detect testimonial smothering:

Communication context: {comm_context}
What is shared: {shared}
What is withheld: {withheld}
Environment: {environment}
Domain: {domain}
Context: {context}

Is self-censorship occurring due to anticipated credibility deficits? Return ONLY valid JSON."""


class TestimonialSmotheringService:
    """Detects testimonial smothering — self-censorship anticipating disbelief."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        comm_context: str,
        *,
        shared: str = "",
        withheld: str = "",
        environment: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect testimonial smothering."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TESTIMONIAL_SMOTHERING_PROMPT.format(
                comm_context=comm_context,
                shared=shared or "Not specified",
                withheld=withheld or "Not specified",
                environment=environment or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TESTIMONIAL_SMOTHERING_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "comm_context": comm_context[:200],
            "smothering_present": data.get("smothering_present", False),
            "severity": data.get("severity", ""),
            "withheld": data.get("withheld", ""),
            "anticipated_deficit": data.get("anticipated_deficit", ""),
            "environment": data.get("environment", ""),
            "recommendation": data.get("recommendation", ""),
        }
