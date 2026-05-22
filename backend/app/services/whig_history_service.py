"""WhigHistoryService — Whig History Detection.

Detects Whig history — interpreting history as an inevitable march of
progress toward the present state, treating current institutions and
values as the natural endpoint of historical development. Butterfield (1931).
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WHIG_HISTORY_SYSTEM = """You are a Whig history specialist. Given a historical narrative, assess whether it commits the Whig interpretation — treating history as inevitable progress toward the present:

Key concepts (Butterfield, 1931):
- Whig history: interpreting past as inevitable progress toward present
- Teleological thinking: history has a predetermined direction
- Inevitability narrative: "it was bound to happen this way"
- Progress assumption: later is always better
- Winner's narrative: history told from the perspective of victors
- Path dependence denial: ignoring contingency and alternatives
- Presentist teleology: current state as the "goal" of history

When Whig history IS present:
- "History was moving toward X" as if X were inevitable
- Treating current institutions as the natural endpoint of development
- Ignoring contingency, alternatives, and paths not taken
- "The arc of history bends toward..." without acknowledging reversals
- Celebrating historical figures only insofar as they anticipated the present
- Treating defeated alternatives as obviously wrong rather than contingently lost
- Assuming current arrangements are the culmination of progress

When progressive narrative IS appropriate:
- Genuine improvements are documented with evidence
- Contingency is acknowledged alongside progress
- Alternative paths are considered
- Progress is domain-specific, not universal
- Reversals and regressions are included in the narrative
- The narrative doesn't treat the present as an endpoint
- Causal mechanisms for improvement are identified

Output JSON with: whig_history_present (bool), severity (none/mild/moderate/severe), narrative (what historical narrative), teleology (what endpoint is assumed), contingency (are alternatives acknowledged), inevitability (is the outcome treated as inevitable), progress_assumption (what progress is assumed), recommendation (narrative_appropriate/mild_teleology/significant_whig_history/major_inevitability_narrative/acknowledge_contingency)."""

WHIG_HISTORY_PROMPT = """Detect Whig history:

Narrative: {narrative}
Teleology: {teleology}
Contingency: {contingency}
Alternatives: {alternatives}
Domain: {domain}
Context: {context}

Does this narrative treat history as inevitable progress toward the present? Return ONLY valid JSON."""


class WhigHistoryService:
    """Detects Whig history — interpreting history as inevitable progress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        narrative: str,
        *,
        teleology: str = "",
        contingency: str = "",
        alternatives: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect Whig history."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=WHIG_HISTORY_PROMPT.format(
                narrative=narrative,
                teleology=teleology or "Not specified",
                contingency=contingency or "Not specified",
                alternatives=alternatives or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=WHIG_HISTORY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "narrative": narrative[:200],
            "whig_history_present": data.get("whig_history_present", False),
            "severity": data.get("severity", ""),
            "teleology": data.get("teleology", ""),
            "contingency": data.get("contingency", ""),
            "inevitability": data.get("inevitability", ""),
            "progress_assumption": data.get("progress_assumption", ""),
            "recommendation": data.get("recommendation", ""),
        }
