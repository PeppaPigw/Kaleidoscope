"""EpistemicComplexitySingleCauseService — Epistemic Complexity Single Cause Detection.

Detects epistemic complexity single cause — seeking single causes for phenomena
that arise from multiple interacting factors and systemic dynamics.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COMPLEXITY_SINGLE_CAUSE_SYSTEM = """You are an epistemic complexity single cause specialist. Given monocausal reasoning, assess causal oversimplification:

Key concepts:
- Epistemic single cause: seeking one cause for multi-causal phenomena
- Monocausal explanation: attributing complex outcomes to single factors
- Root cause fallacy: assuming there's always one root cause
- Blame concentration: concentrating blame on single actor or factor
- Silver bullet thinking: assuming single interventions solve complex problems
- Causal chain truncation: stopping causal analysis at first plausible cause
- Overdetermination blindness: missing that multiple sufficient causes exist

When epistemic single cause IS present:
- Single cause sought
- Monocausal explanation given
- Root cause assumed singular
- Blame concentrated
- Silver bullet expected
- Causal chain truncated
- Overdetermination missed

When no single cause bias:
- Multiple causes considered
- Multi-causal explanation given
- Root causes plural
- Responsibility distributed
- Multiple interventions considered
- Causal chains fully traced
- Overdetermination recognized

Output JSON with: single_cause_detected (bool), severity (none/mild/moderate/severe), monocausal_explanation (what monocausal explanation), blame_concentration (what blame concentrated), silver_bullet_thinking (what silver bullet expected), causal_chain_truncation (what chain truncated), recommendation (no_single_cause/mild_multi_causal_awareness/significant_causal_mapping/major_intensive_systems_analysis/emergency_complete_single_cause)."""

EPISTEMIC_COMPLEXITY_SINGLE_CAUSE_PROMPT = """Detect epistemic complexity single cause:

Monocausal explanation: {monocausal_explanation}
Blame concentration: {blame_concentration}
Silver bullet thinking: {silver_bullet_thinking}
Causal chain truncation: {causal_chain_truncation}
Domain: {domain}
Context: {context}

Is a single cause being sought for multi-causal phenomena? Return ONLY valid JSON."""


class EpistemicComplexitySingleCauseService:
    """Detects epistemic complexity single cause — causal oversimplification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        monocausal_explanation: str,
        *,
        blame_concentration: str = "",
        silver_bullet_thinking: str = "",
        causal_chain_truncation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic complexity single cause."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COMPLEXITY_SINGLE_CAUSE_PROMPT.format(
                monocausal_explanation=monocausal_explanation,
                blame_concentration=blame_concentration or "Not specified",
                silver_bullet_thinking=silver_bullet_thinking or "Not specified",
                causal_chain_truncation=causal_chain_truncation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COMPLEXITY_SINGLE_CAUSE_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "monocausal_explanation": monocausal_explanation[:200],
            "single_cause_detected": data.get("single_cause_detected", False),
            "severity": data.get("severity", ""),
            "blame_concentration": data.get("blame_concentration", ""),
            "silver_bullet_thinking": data.get("silver_bullet_thinking", ""),
            "causal_chain_truncation": data.get("causal_chain_truncation", ""),
            "recommendation": data.get("recommendation", ""),
        }
