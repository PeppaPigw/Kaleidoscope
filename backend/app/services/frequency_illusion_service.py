"""FrequencyIllusionService — Frequency Illusion (Baader-Meinhof) Detection.

Detects the frequency illusion — the perception that something
encountered recently is suddenly appearing everywhere. Also
called the Baader-Meinhof phenomenon. Zwicky (2006). After
learning a new word, concept, or noticing something for the
first time, it seems to appear with impossible frequency.
This is selective attention, not actual increased frequency.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

FREQUENCY_ILLUSION_SYSTEM = """You are a frequency illusion specialist. Given a perception of increased frequency, assess whether it's genuine or an attention artifact:

Key concepts (Zwicky, 2006):
- Frequency illusion: newly noticed things seem suddenly everywhere
- Baader-Meinhof phenomenon: learning something then seeing it constantly
- Selective attention: noticing what you're primed to notice
- Confirmation bias interaction: counting hits, ignoring misses
- Recency illusion: believing something recent is actually new
- Availability heuristic interaction: easily recalled = frequent
- Attentional priming: awareness creates detection sensitivity

When the frequency illusion IS present:
- "I keep seeing X everywhere since I learned about it"
- Believing a trend is new when only awareness is new
- Overestimating frequency of recently learned concepts
- "Everyone is talking about X" when attention is selective
- Perceiving a pattern where only detection has changed
- "This is happening more and more" without baseline data
- Confusing increased awareness with increased occurrence

When frequency increase IS real:
- Baseline data confirms actual increase in occurrence
- Multiple independent observers note the same increase
- The increase is measurable, not just perceived
- There's a causal mechanism for actual increase
- The observation predates the awareness (not post-hoc)

Output JSON with: frequency_illusion_present (bool), severity (none/mild/moderate/severe), perception (what seems to be increasing), trigger (what caused the initial awareness), baseline (what was the actual prior frequency), attention_change (how has attention changed), actual_frequency (has actual frequency changed), evidence_for_increase (what evidence supports real increase), recommendation (frequency_increase_real/mild_attention_artifact/significant_frequency_illusion/major_pattern_projection/establish_baseline_before_claiming_trend)."""

FREQUENCY_ILLUSION_PROMPT = """Detect frequency illusion:

Perception: {perception}
Trigger: {trigger}
Baseline: {baseline}
Evidence: {evidence}
Domain: {domain}
Context: {context}

Is the perceived increase in frequency an attention artifact rather than a real change? Return ONLY valid JSON."""


class FrequencyIllusionService:
    """Detects frequency illusion — perceived increase due to attention, not actual change."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        perception: str,
        *,
        trigger: str = "",
        baseline: str = "",
        evidence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect frequency illusion."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=FREQUENCY_ILLUSION_PROMPT.format(
                perception=perception,
                trigger=trigger or "Not specified",
                baseline=baseline or "Not specified",
                evidence=evidence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=FREQUENCY_ILLUSION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "perception": perception[:200],
            "frequency_illusion_present": data.get("frequency_illusion_present", False),
            "severity": data.get("severity", ""),
            "trigger": data.get("trigger", ""),
            "baseline": data.get("baseline", ""),
            "attention_change": data.get("attention_change", ""),
            "actual_frequency": data.get("actual_frequency", ""),
            "evidence_for_increase": data.get("evidence_for_increase", ""),
            "recommendation": data.get("recommendation", ""),
        }
