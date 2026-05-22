"""TraitAscriptionService — Trait Ascription Bias Detection.

Detects trait ascription bias — viewing oneself as variable and
context-dependent while viewing others as having fixed traits.
Kammer (1982). "I'm complex and adaptable; they're just like
that." People see themselves as nuanced and situationally
responsive while seeing others as predictable and trait-driven.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TRAIT_ASCRIPTION_SYSTEM = """You are a trait ascription bias specialist. Given judgments about people's characteristics, assess whether there's an asymmetry in how variability is attributed to self vs others:

Key concepts (Kammer, 1982):
- Trait ascription bias: self as variable, others as fixed
- Self-complexity: seeing own behavior as context-dependent
- Other-simplicity: seeing others as trait-driven and predictable
- Behavioral variability: actors know their own range
- Stereotyping mechanism: reducing others to stable traits
- Prediction asymmetry: expecting own behavior to vary but others' to be consistent
- Nuance asymmetry: "I'm complex, they're simple"

When trait ascription bias IS present:
- "I adapt to situations; they're always like that"
- Predicting others' behavior from single observations
- Seeing own contradictions as complexity but others' as hypocrisy
- "That's just who they are" while "I was having a bad day"
- Expecting others to be consistent while excusing own inconsistency
- Reducing others to labels while resisting labels for self
- Surprise when others behave out of character

When trait judgment IS appropriate:
- Extensive observation across many contexts supports the trait judgment
- The person themselves identifies the trait as stable
- Behavioral consistency has been verified over time
- The trait is genuinely stable (e.g., core values, deep preferences)
- Both self and others are evaluated with similar nuance

Output JSON with: trait_ascription_present (bool), severity (none/mild/moderate/severe), situation (what judgment is being made), self_view (how self is characterized), other_view (how others are characterized), variability_asymmetry (difference in attributed variability), evidence_base (what evidence supports the trait judgment), prediction_confidence (how confident are predictions about others), recommendation (trait_judgment_justified/mild_ascription_bias/significant_trait_ascription/major_self_other_asymmetry/attribute_equal_complexity)."""

TRAIT_ASCRIPTION_PROMPT = """Detect trait ascription bias:

Situation: {situation}
Self-characterization: {self_view}
Other-characterization: {other_view}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is there an asymmetry in attributed variability — self as complex/variable, others as fixed/predictable? Return ONLY valid JSON."""


class TraitAscriptionService:
    """Detects trait ascription bias — viewing self as variable but others as fixed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        self_view: str = "",
        other_view: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect trait ascription bias."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=TRAIT_ASCRIPTION_PROMPT.format(
                situation=situation,
                self_view=self_view or "Not specified",
                other_view=other_view or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=TRAIT_ASCRIPTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "trait_ascription_present": data.get("trait_ascription_present", False),
            "severity": data.get("severity", ""),
            "self_view": data.get("self_view", ""),
            "other_view": data.get("other_view", ""),
            "variability_asymmetry": data.get("variability_asymmetry", ""),
            "evidence_base": data.get("evidence_base", ""),
            "prediction_confidence": data.get("prediction_confidence", ""),
            "recommendation": data.get("recommendation", ""),
        }
