"""EpistemicCausalPostHocErgoPropterHocService - Post Hoc Ergo Propter Hoc Detection.

Detects post hoc reasoning where temporal sequence is mistaken for causation.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_POST_HOC_SYSTEM = """You are an epistemic causal post hoc ergo propter hoc specialist. Given temporal sequences, assess whether sequence is mistaken for causation:

Key concepts:
- Post hoc ergo propter hoc: assuming because B followed A, A caused B
- Temporal coincidence: events co-occurring without causal link
- Confound blindness: ignoring third variables that explain both
- Mechanism absence: no plausible causal pathway identified

When post hoc reasoning IS present:
- Temporal sequence treated as causation
- Coincidence mistaken for connection
- Confounds ignored
- No mechanism identified
- Alternative explanations unexplored

When no post hoc reasoning:
- Temporal sequence distinguished from causation
- Coincidence considered
- Confounds investigated
- Mechanisms proposed and tested
- Alternative explanations explored

Output JSON with: post_hoc_detected (bool), severity (none/mild/moderate/severe), temporal_coincidence (what coincidence), confound_blindness (what confounds ignored), mechanism_absence (what mechanism missing), recommendation (no_post_hoc/mild_mechanism_check/significant_confound_analysis/major_causal_reconstruction/emergency_complete_post_hoc)."""

EPISTEMIC_CAUSAL_POST_HOC_PROMPT = """Detect epistemic causal post hoc ergo propter hoc:

Temporal sequence: {temporal_sequence}
Temporal coincidence: {temporal_coincidence}
Confound blindness: {confound_blindness}
Mechanism absence: {mechanism_absence}
Domain: {domain}
Context: {context}

Is temporal sequence being mistaken for causation? Return ONLY valid JSON."""


class EpistemicCausalPostHocErgoPropterHocService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        temporal_sequence: str,
        *,
        temporal_coincidence: str = "",
        confound_blindness: str = "",
        mechanism_absence: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_POST_HOC_PROMPT.format(
                temporal_sequence=temporal_sequence,
                temporal_coincidence=temporal_coincidence or "Not specified",
                confound_blindness=confound_blindness or "Not specified",
                mechanism_absence=mechanism_absence or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_POST_HOC_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "temporal_sequence": temporal_sequence[:200],
            "post_hoc_detected": data.get("post_hoc_detected", False),
            "severity": data.get("severity", ""),
            "temporal_coincidence": data.get("temporal_coincidence", ""),
            "confound_blindness": data.get("confound_blindness", ""),
            "mechanism_absence": data.get("mechanism_absence", ""),
            "recommendation": data.get("recommendation", ""),
        }
