"""DefensiveAttributionService — Defensive Attribution Detection.

Detects defensive attribution — attributing accidents or
misfortunes to victims' behavior in order to feel safe.
"It won't happen to me because I wouldn't do what they did."
Shaver (1970). Protects sense of personal invulnerability
but leads to victim-blaming and inadequate risk preparation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

DEFENSIVE_ATTRIBUTION_SYSTEM = """You are a defensive attribution specialist. Given an attribution for someone's misfortune, assess whether the attribution serves to protect the attributor's sense of safety:

Key concepts (Shaver, 1970):
- Defensive attribution: blaming victims to feel personally safe
- Just world overlap: but defensive attribution is specifically about self-protection
- Invulnerability illusion: "it can't happen to me"
- Behavioral attribution: "they must have done something wrong"
- Controllability assumption: assuming outcomes are controllable
- Similarity effect: more defensive when victim is similar to self
- Hindsight bias interaction: "they should have known"

When defensive attribution IS present:
- "They should have been more careful" for random misfortune
- Assuming victims did something to cause their situation
- "That wouldn't happen to me because I would..."
- Finding behavioral explanations for structural/random events
- Blaming victims to maintain sense of personal control
- "They were asking for it" applied to random misfortune

When the attribution IS accurate:
- The victim's behavior genuinely contributed (documented, not assumed)
- The causal link between behavior and outcome is established
- The attribution doesn't serve primarily to protect the attributor
- Similar attributions are applied to own past behavior
- Structural/random factors are also acknowledged

Output JSON with: defensive_attribution_present (bool), severity (none/mild/moderate/severe), event (what happened), victim (who experienced the misfortune), attribution (how is it being explained), self_protection_motive (bool — does the attribution protect the attributor?), behavioral_blame (what behavior is being blamed?), structural_factors (what structural/random factors are ignored?), controllability_assumed (bool — is the outcome assumed controllable?), evidence_for_attribution (what evidence supports the behavioral explanation?), similarity_to_self (how similar is the victim to the attributor?), recommendation (attribution_accurate/mild_defensive/significant_victim_blaming/major_defensive_attribution/acknowledge_randomness)."""

DEFENSIVE_ATTRIBUTION_PROMPT = """Detect defensive attribution:

Event: {event}
Attribution: {attribution}
Victim: {victim}
Structural factors: {structural}
Domain: {domain}
Context: {context}

Is this attribution serving to protect the attributor's sense of safety? Return ONLY valid JSON."""


class DefensiveAttributionService:
    """Detects defensive attribution — blaming victims to feel personally safe."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        event: str,
        *,
        attribution: str = "",
        victim: str = "",
        structural: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect defensive attribution."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=DEFENSIVE_ATTRIBUTION_PROMPT.format(
                event=event,
                attribution=attribution or "Not specified",
                victim=victim or "Not specified",
                structural=structural or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=DEFENSIVE_ATTRIBUTION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "event": event[:200],
            "defensive_attribution_present": data.get("defensive_attribution_present", False),
            "severity": data.get("severity", ""),
            "attribution": data.get("attribution", ""),
            "self_protection_motive": data.get("self_protection_motive", False),
            "behavioral_blame": data.get("behavioral_blame", ""),
            "structural_factors": data.get("structural_factors", ""),
            "controllability_assumed": data.get("controllability_assumed", False),
            "evidence_for_attribution": data.get("evidence_for_attribution", ""),
            "similarity_to_self": data.get("similarity_to_self", ""),
            "recommendation": data.get("recommendation", ""),
        }
