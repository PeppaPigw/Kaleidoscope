"""EpistemicPostOpRecoveryService — Epistemic Post-Operative Recovery Detection.

Detects epistemic post-operative recovery issues — complications and
challenges arising after intellectual surgical intervention.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_POST_OP_SYSTEM = """You are an epistemic post-operative recovery specialist. Given intellectual systems after surgery, assess recovery:

Key concepts:
- Epistemic post-op: recovery after intellectual surgery
- Surgical site infection: contamination at intervention point
- Ileus: intellectual gut not resuming function
- DVT: clot formation from immobility
- Atelectasis: intellectual lung collapse from shallow breathing
- Wound dehiscence: surgical closure reopening
- Return to function: resuming normal intellectual activity

When epistemic post-op issues ARE present:
- Contamination at intervention point
- Function not resuming after surgery
- Clot formation from immobility
- Collapse from shallow activity
- Closure reopening
- Delayed return to function
- Complications developing

When no post-op issues:
- Clean intervention site
- Normal function resuming
- No clot formation
- Full activity maintained
- Closure intact
- Normal recovery timeline
- No complications

Output JSON with: post_op_issues (bool), severity (none/mild/moderate/severe), complication_type (what problem), wound_status (what site condition), function_return (what resumption), mobility_status (what activity level), recommendation (no_post_op_issues/mild_monitoring/significant_intervention/major_reoperation/emergency_post_op_crisis)."""

EPISTEMIC_POST_OP_PROMPT = """Detect epistemic post-operative recovery issues:

Complication type: {complication_type}
Wound status: {wound_status}
Function return: {function_return}
Mobility status: {mobility_status}
Domain: {domain}
Context: {context}

Are there complications after intellectual surgical intervention? Return ONLY valid JSON."""


class EpistemicPostOpRecoveryService:
    """Detects epistemic post-operative recovery issues — complications after surgery."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        complication_type: str,
        *,
        wound_status: str = "",
        function_return: str = "",
        mobility_status: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic post-operative recovery issues."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_POST_OP_PROMPT.format(
                complication_type=complication_type,
                wound_status=wound_status or "Not specified",
                function_return=function_return or "Not specified",
                mobility_status=mobility_status or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_POST_OP_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "complication_type": complication_type[:200],
            "post_op_issues": data.get("post_op_issues", False),
            "severity": data.get("severity", ""),
            "wound_status": data.get("wound_status", ""),
            "function_return": data.get("function_return", ""),
            "mobility_status": data.get("mobility_status", ""),
            "recommendation": data.get("recommendation", ""),
        }
