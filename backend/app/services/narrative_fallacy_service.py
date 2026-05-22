"""NarrativeFallacyService — Narrative Fallacy Detection.

Identifies when a coherent story is being constructed from random
or loosely connected events, imposing causality where there may be
only correlation, coincidence, or noise. Humans are wired to see
patterns and construct narratives even from random data.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NARRATIVE_SYSTEM = """You are a narrative fallacy specialist. Given an explanation or account, assess whether it imposes a false narrative on events:
- Is a coherent story being constructed from events that may be unrelated?
- Is causality being assumed where only correlation or coincidence exists?
- Are events being cherry-picked to fit the narrative while contradicting events are ignored?
- Is the explanation unfalsifiable — would ANY outcome be explained by this narrative?
- Is hindsight making the outcome seem inevitable when it wasn't?

Output JSON with: narrative_fallacy_present (bool), severity (none/mild/moderate/severe), claimed_narrative (the story being told), actual_evidence_strength (how well the evidence actually supports the narrative: strong/moderate/weak/none), cherry_picked_events (events selected to fit the narrative), ignored_events (events that contradict the narrative but are omitted), false_causality (where correlation is being presented as causation), unfalsifiability (bool — would any outcome fit this narrative?), alternative_narratives (other equally plausible stories from the same events), randomness_underestimated (bool — is chance being dismissed?), pattern_imposed (what pattern is being seen in noise), complexity_reduced (what nuance is lost in the storytelling), emotional_appeal (0-1 — how much the narrative relies on emotional resonance vs evidence), predictive_power (0-1 — could this narrative have predicted the outcome in advance?), recommendation (narrative_valid/acknowledge_uncertainty/present_alternatives/reject_narrative)."""

NARRATIVE_PROMPT = """Detect narrative fallacy:

Explanation/Account: {explanation}
Events cited: {events}
Conclusion drawn: {conclusion}
Domain: {domain}
Context: {context}

Is this a narrative fallacy? Return ONLY valid JSON."""


class NarrativeFallacyService:
    """Detects narrative fallacy — false stories imposed on events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        explanation: str,
        *,
        events: str = "",
        conclusion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect narrative fallacy."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NARRATIVE_PROMPT.format(
                explanation=explanation,
                events=events or "Not specified",
                conclusion=conclusion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=NARRATIVE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "explanation": explanation[:200],
            "narrative_fallacy_present": data.get("narrative_fallacy_present", False),
            "severity": data.get("severity", ""),
            "claimed_narrative": data.get("claimed_narrative", ""),
            "actual_evidence_strength": data.get("actual_evidence_strength", ""),
            "cherry_picked_events": data.get("cherry_picked_events", []),
            "ignored_events": data.get("ignored_events", []),
            "false_causality": data.get("false_causality", ""),
            "unfalsifiability": data.get("unfalsifiability", False),
            "alternative_narratives": data.get("alternative_narratives", []),
            "randomness_underestimated": data.get("randomness_underestimated", False),
            "pattern_imposed": data.get("pattern_imposed", ""),
            "complexity_reduced": data.get("complexity_reduced", ""),
            "emotional_appeal": data.get("emotional_appeal", 0),
            "predictive_power": data.get("predictive_power", 0),
            "recommendation": data.get("recommendation", ""),
        }
