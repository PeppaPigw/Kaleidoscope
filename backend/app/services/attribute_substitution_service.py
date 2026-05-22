"""AttributeSubstitutionService — Attribute Substitution Detection.

Detects attribute substitution — answering an easier question
instead of the hard one that was actually asked. Kahneman (2003).
"How happy are you with your life?" becomes "What is my mood
right now?" Leads to judgments based on accessible but
irrelevant attributes rather than the actual target attribute.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ATTRIBUTE_SUBSTITUTION_SYSTEM = """You are an attribute substitution specialist. Given a judgment, assess whether the person is answering an easier question instead of the one actually asked:

Key concepts (Kahneman, 2003):
- Attribute substitution: replacing a hard question with an easier one
- Target attribute: what should be evaluated (complex, requires effort)
- Heuristic attribute: what is actually evaluated (accessible, easy)
- Affect heuristic overlap: using emotional response as proxy for risk
- Representativeness overlap: using similarity as proxy for probability
- Availability overlap: using ease of recall as proxy for frequency
- Cross-dimensional mapping: using one dimension to judge another

When attribute substitution IS present:
- Judging competence by confidence (confidence is easier to assess)
- Judging future happiness by current mood
- Judging investment quality by brand familiarity
- Judging argument strength by speaker attractiveness
- Judging probability by how easily examples come to mind
- Answering "how do I feel about it?" instead of "what do I think about it?"

When the proxy IS appropriate:
- The heuristic attribute genuinely correlates with the target
- The person is aware they're using a proxy and it's deliberate
- The proxy has been validated for this context
- The target attribute is genuinely unmeasurable
- The proxy is the best available evidence for the target

Output JSON with: attribute_substitution_present (bool), severity (none/mild/moderate/severe), question_asked (what should be evaluated — the target attribute), question_answered (what is actually being evaluated — the heuristic attribute), target_attribute (the complex attribute that should be assessed), heuristic_attribute (the easy attribute being used instead), correlation (how well does the heuristic predict the target?), accessibility_gap (how much easier is the heuristic to assess?), awareness (bool — is the person aware of the substitution?), consequence (what is lost by using the proxy?), recommendation (proxy_appropriate/mild_substitution/significant_mismatch/major_wrong_question/assess_target_directly)."""

ATTRIBUTE_SUBSTITUTION_PROMPT = """Detect attribute substitution:

Judgment: {judgment}
Question asked: {question}
Basis of judgment: {basis}
Target attribute: {target}
Domain: {domain}
Context: {context}

Is the person answering an easier question instead of the one asked? Return ONLY valid JSON."""


class AttributeSubstitutionService:
    """Detects attribute substitution — answering an easier question than the one asked."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        judgment: str,
        *,
        question: str = "",
        basis: str = "",
        target: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect attribute substitution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ATTRIBUTE_SUBSTITUTION_PROMPT.format(
                judgment=judgment,
                question=question or "Not specified",
                basis=basis or "Not specified",
                target=target or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ATTRIBUTE_SUBSTITUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "judgment": judgment[:200],
            "attribute_substitution_present": data.get("attribute_substitution_present", False),
            "severity": data.get("severity", ""),
            "question_asked": data.get("question_asked", ""),
            "question_answered": data.get("question_answered", ""),
            "target_attribute": data.get("target_attribute", ""),
            "heuristic_attribute": data.get("heuristic_attribute", ""),
            "correlation": data.get("correlation", ""),
            "accessibility_gap": data.get("accessibility_gap", ""),
            "awareness": data.get("awareness", False),
            "consequence": data.get("consequence", ""),
            "recommendation": data.get("recommendation", ""),
        }
