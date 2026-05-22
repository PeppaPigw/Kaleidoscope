"""CognitiveMiserService — Cognitive Miser Detection.

Detects cognitive miser tendency — using the least effortful
cognitive strategy available rather than engaging in deeper
analysis. Fiske & Taylor (1984). People are "cognitive misers"
who conserve mental resources by defaulting to heuristics,
stereotypes, and shortcuts even when the situation warrants
careful thought.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

COGNITIVE_MISER_SYSTEM = """You are a cognitive miser specialist. Given a judgment or decision, assess whether the person is using inappropriately shallow processing for the stakes involved:

Key concepts (Fiske & Taylor, 1984):
- Cognitive miser: defaulting to least-effort processing
- System 1 vs System 2: using fast/automatic when slow/deliberate is needed
- Heuristic processing: shortcuts appropriate for low stakes, not high
- Effort-accuracy tradeoff: when is the shortcut good enough?
- Satisficing: accepting "good enough" when optimal is needed
- Stereotype reliance: using category-level info instead of individual assessment
- Peripheral route: persuaded by surface cues rather than argument quality

When cognitive miser IS present:
- Using stereotypes for high-stakes individual assessments
- Accepting first plausible answer without verification
- Relying on authority/source rather than evaluating arguments
- "Going with gut" on decisions that warrant analysis
- Using rules of thumb for novel, complex situations
- Insufficient effort relative to decision stakes

When the shortcut IS appropriate:
- The stakes are genuinely low
- The heuristic has been validated for this context
- Time pressure genuinely prevents deeper analysis
- The shortcut produces equivalent outcomes to deep analysis
- Expertise makes the "shortcut" actually informed intuition
- The cost of deeper analysis exceeds the benefit

Output JSON with: cognitive_miser_present (bool), severity (none/mild/moderate/severe), decision (what is being decided), processing_depth (how deeply is it being analyzed), stakes (what are the stakes), appropriate_depth (what depth would the stakes warrant), shortcut_used (what heuristic/shortcut is being used), shortcut_accuracy (how accurate is the shortcut likely to be?), effort_justified (bool — would more effort improve the outcome?), time_pressure (is there genuine time pressure?), recommendation (shortcut_appropriate/mild_underprocessing/significant_cognitive_miser/major_shallow_processing/engage_deeper_analysis)."""

COGNITIVE_MISER_PROMPT = """Detect cognitive miser tendency:

Decision: {decision}
Processing: {processing}
Stakes: {stakes}
Time available: {time}
Domain: {domain}
Context: {context}

Is the person using inappropriately shallow processing for the stakes? Return ONLY valid JSON."""


class CognitiveMiserService:
    """Detects cognitive miser tendency — using least-effort processing inappropriately."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        decision: str,
        *,
        processing: str = "",
        stakes: str = "",
        time: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect cognitive miser tendency."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=COGNITIVE_MISER_PROMPT.format(
                decision=decision,
                processing=processing or "Not specified",
                stakes=stakes or "Not specified",
                time=time or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=COGNITIVE_MISER_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "decision": decision[:200],
            "cognitive_miser_present": data.get("cognitive_miser_present", False),
            "severity": data.get("severity", ""),
            "processing_depth": data.get("processing_depth", ""),
            "stakes": data.get("stakes", ""),
            "appropriate_depth": data.get("appropriate_depth", ""),
            "shortcut_used": data.get("shortcut_used", ""),
            "shortcut_accuracy": data.get("shortcut_accuracy", ""),
            "effort_justified": data.get("effort_justified", True),
            "time_pressure": data.get("time_pressure", ""),
            "recommendation": data.get("recommendation", ""),
        }
