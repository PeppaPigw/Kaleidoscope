"""EpistemicCausalChainTruncationService — Epistemic Causal Chain Truncation Detection.

Detects epistemic causal chain truncation — truncating causal chains
prematurely, stopping explanation too early or too late.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CAUSAL_CHAIN_TRUNCATION_SYSTEM = """You are an epistemic causal chain truncation specialist. Given premature truncation of causal chains, assess chain truncation:

Key concepts:
- Epistemic causal chain truncation: stopping causal explanation prematurely
- Premature stopping: stopping at convenient point in causal chain
- Root cause avoidance: avoiding tracing to root cause
- Proximate fixation: fixating on proximate cause ignoring deeper causes
- Convenient truncation: truncating where it supports preferred narrative
- Infinite regress avoidance: stopping to avoid infinite regress but too early
- Explanatory satisfaction: satisfied with explanation before reaching true cause

When epistemic causal chain truncation IS present:
- Chain truncated prematurely
- Stopping at convenient point
- Root cause avoided
- Proximate cause fixated on
- Truncation convenient
- Stopping too early
- Satisfied too soon

When no chain truncation:
- Chain traced appropriately
- Stopping at principled point
- Root cause sought
- Deeper causes explored
- Truncation principled
- Appropriate depth reached
- Satisfaction warranted

Output JSON with: causal_chain_truncation_detected (bool), severity (none/mild/moderate/severe), premature_stopping (where stopped prematurely), root_cause_avoidance (what root cause avoided), proximate_fixation (what proximate cause fixated on), convenient_truncation (what truncation convenient), recommendation (no_chain_truncation/mild_deeper_tracing/significant_root_cause_pursuit/major_intensive_chain_completion/emergency_complete_chain_truncation)."""

EPISTEMIC_CAUSAL_CHAIN_TRUNCATION_PROMPT = """Detect epistemic causal chain truncation:

Premature stopping: {premature_stopping}
Root cause avoidance: {root_cause_avoidance}
Proximate fixation: {proximate_fixation}
Convenient truncation: {convenient_truncation}
Domain: {domain}
Context: {context}

Are causal chains being truncated prematurely? Return ONLY valid JSON."""


class EpistemicCausalChainTruncationService:
    """Detects epistemic causal chain truncation — stopping too early."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        premature_stopping: str,
        *,
        root_cause_avoidance: str = "",
        proximate_fixation: str = "",
        convenient_truncation: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic causal chain truncation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CAUSAL_CHAIN_TRUNCATION_PROMPT.format(
                premature_stopping=premature_stopping,
                root_cause_avoidance=root_cause_avoidance or "Not specified",
                proximate_fixation=proximate_fixation or "Not specified",
                convenient_truncation=convenient_truncation or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CAUSAL_CHAIN_TRUNCATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "premature_stopping": premature_stopping[:200],
            "causal_chain_truncation_detected": data.get("causal_chain_truncation_detected", False),
            "severity": data.get("severity", ""),
            "root_cause_avoidance": data.get("root_cause_avoidance", ""),
            "proximate_fixation": data.get("proximate_fixation", ""),
            "convenient_truncation": data.get("convenient_truncation", ""),
            "recommendation": data.get("recommendation", ""),
        }
