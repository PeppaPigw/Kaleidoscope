"""EpistemicExpertiseDepthIllusionService — Epistemic Expertise Depth Illusion Detection.

Detects epistemic expertise depth illusion — confusing surface familiarity with
deep understanding, overestimating one's own or others' comprehension.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_EXPERTISE_DEPTH_ILLUSION_SYSTEM = """You are an epistemic expertise depth illusion specialist. Given depth illusion, assess understanding overestimation:

Key concepts:
- Epistemic expertise depth illusion: confusing familiarity with understanding
- Illusion of explanatory depth: thinking you understand more than you do
- Recognition vs. recall: recognizing terms without understanding mechanisms
- Surface fluency: fluent discussion masking shallow understanding
- Jargon competence: using terminology without grasping concepts
- Teaching test failure: inability to explain simply revealing shallow knowledge
- Dunning-Kruger expertise: insufficient knowledge to recognize own gaps

When epistemic expertise depth illusion IS present:
- Familiarity confused with understanding
- Explanatory depth overestimated
- Recognition mistaken for knowledge
- Surface fluency masking shallowness
- Jargon used without comprehension
- Cannot explain simply
- Gaps unrecognized

When no depth illusion:
- Familiarity distinguished from understanding
- Explanatory limits acknowledged
- Recognition vs. knowledge distinguished
- Depth accurately assessed
- Jargon backed by comprehension
- Can explain at multiple levels
- Gaps recognized

Output JSON with: depth_illusion_detected (bool), severity (none/mild/moderate/severe), explanatory_depth_overestimate (what depth overestimated), surface_fluency (what fluency masking), jargon_competence (what jargon without comprehension), teaching_test_failure (what cannot be explained simply), recommendation (no_depth_illusion/mild_depth_probing/significant_explanation_testing/major_intensive_knowledge_audit/emergency_complete_depth_illusion)."""

EPISTEMIC_EXPERTISE_DEPTH_ILLUSION_PROMPT = """Detect epistemic expertise depth illusion:

Explanatory depth overestimate: {explanatory_depth_overestimate}
Surface fluency: {surface_fluency}
Jargon competence: {jargon_competence}
Teaching test failure: {teaching_test_failure}
Domain: {domain}
Context: {context}

Is familiarity being confused with deep understanding? Return ONLY valid JSON."""


class EpistemicExpertiseDepthIllusionService:
    """Detects epistemic expertise depth illusion — familiarity vs. understanding."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanatory_depth_overestimate: str,
        *,
        surface_fluency: str = "",
        jargon_competence: str = "",
        teaching_test_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic expertise depth illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_EXPERTISE_DEPTH_ILLUSION_PROMPT.format(
                explanatory_depth_overestimate=explanatory_depth_overestimate,
                surface_fluency=surface_fluency or "Not specified",
                jargon_competence=jargon_competence or "Not specified",
                teaching_test_failure=teaching_test_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_EXPERTISE_DEPTH_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanatory_depth_overestimate": explanatory_depth_overestimate[:200],
            "depth_illusion_detected": data.get("depth_illusion_detected", False),
            "severity": data.get("severity", ""),
            "surface_fluency": data.get("surface_fluency", ""),
            "jargon_competence": data.get("jargon_competence", ""),
            "teaching_test_failure": data.get("teaching_test_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
