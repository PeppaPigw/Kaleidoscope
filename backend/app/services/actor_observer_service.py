"""ActorObserverService — Actor-Observer Asymmetry Detection.

Detects actor-observer asymmetry — attributing own behavior to
situational factors while attributing others' identical behavior
to their character/disposition. Jones & Nisbett (1971). "I was
late because of traffic; they were late because they're
irresponsible." Same behavior, different causal attribution
depending on whether you're the actor or observer.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

ACTOR_OBSERVER_SYSTEM = """You are an actor-observer asymmetry specialist. Given causal attributions for behavior, assess whether there's an asymmetry between how own vs others' behavior is explained:

Key concepts (Jones & Nisbett, 1971):
- Actor-observer asymmetry: situational for self, dispositional for others
- Fundamental attribution error interaction: overweighting character for others
- Visual perspective: actors see situations, observers see actors
- Information asymmetry: actors know their own variability
- Self-serving bias interaction: protecting self-image through attribution
- Correspondence bias: inferring traits from single behaviors (for others)
- Situational awareness: actors attend to context, observers to person

When actor-observer asymmetry IS present:
- "I failed because the test was unfair; they failed because they're lazy"
- Explaining own mistakes situationally but others' as character flaws
- "I had good reasons; they just don't care"
- Seeing own behavior as context-dependent but others' as revealing
- Different standards for excusing own vs others' identical behavior
- "Anyone would have done what I did" but "they should have known better"
- Attributing own success to effort but others' to luck

When attribution IS balanced:
- Same causal framework applied to self and others
- Acknowledging situational factors for others' behavior
- Recognizing dispositional factors in own behavior
- Seeking to understand others' context before judging
- Consistent standards for evaluating identical behaviors

Output JSON with: actor_observer_present (bool), severity (none/mild/moderate/severe), behavior (what behavior is being explained), self_attribution (how own behavior is explained), other_attribution (how others' behavior is explained), asymmetry (what is the attribution difference), situational_factors (what situational factors exist), dispositional_factors (what character factors are invoked), recommendation (attribution_balanced/mild_asymmetry/significant_actor_observer_bias/major_double_standard/apply_consistent_attribution)."""

ACTOR_OBSERVER_PROMPT = """Detect actor-observer asymmetry:

Situation: {situation}
Self-explanation: {self_explain}
Other-explanation: {other_explain}
Behavior: {behavior}
Domain: {domain}
Context: {context}

Is there an asymmetry between situational self-attribution and dispositional other-attribution? Return ONLY valid JSON."""


class ActorObserverService:
    """Detects actor-observer asymmetry — different causal attributions for self vs others."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        situation: str,
        *,
        self_explain: str = "",
        other_explain: str = "",
        behavior: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect actor-observer asymmetry."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=ACTOR_OBSERVER_PROMPT.format(
                situation=situation,
                self_explain=self_explain or "Not specified",
                other_explain=other_explain or "Not specified",
                behavior=behavior or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=ACTOR_OBSERVER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "situation": situation[:200],
            "actor_observer_present": data.get("actor_observer_present", False),
            "severity": data.get("severity", ""),
            "self_attribution": data.get("self_attribution", ""),
            "other_attribution": data.get("other_attribution", ""),
            "asymmetry": data.get("asymmetry", ""),
            "situational_factors": data.get("situational_factors", ""),
            "dispositional_factors": data.get("dispositional_factors", ""),
            "recommendation": data.get("recommendation", ""),
        }
