"""EpistemicCirrhosisService — Epistemic Cirrhosis Detection.

Detects epistemic cirrhosis — progressive scarring replacing functional
intellectual tissue, reducing processing capacity over time.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_CIRRHOSIS_SYSTEM = """You are an epistemic cirrhosis specialist. Given intellectual tissue, assess whether progressive scarring is replacing functional capacity:

Key concepts:
- Epistemic cirrhosis: progressive scarring replacing functional tissue
- Fibrosis: scar tissue forming in response to damage
- Nodular regeneration: distorted regrowth around scars
- Decompensation: system failing despite compensation
- Synthetic failure: inability to produce needed outputs
- Encephalopathy: toxins affecting higher function due to bypass
- Irreversibility: permanent loss of functional tissue

When epistemic cirrhosis IS present:
- Progressive scarring replacing functional intellectual tissue
- Scar tissue forming in response to repeated damage
- Distorted regrowth around intellectual scars
- System failing despite compensatory efforts
- Inability to produce needed intellectual outputs
- Toxins affecting higher function due to bypass routes
- Permanent loss of functional intellectual capacity

When healthy tissue is present:
- No scarring
- No fibrosis
- Normal regeneration
- System functioning well
- Adequate synthetic output
- No encephalopathy
- Full functional capacity

Output JSON with: cirrhosis_present (bool), severity (none/mild/moderate/severe), fibrosis (what scar formation), nodular_regeneration (what distorted regrowth), decompensation (what system failure), synthetic_failure (what output inability), recommendation (healthy_tissue/mild_cirrhosis/significant_cirrhosis/major_scarring/prevent_further_damage)."""

EPISTEMIC_CIRRHOSIS_PROMPT = """Detect epistemic cirrhosis:

Fibrosis: {fibrosis}
Nodular regeneration: {nodular_regeneration}
Decompensation: {decompensation}
Synthetic failure: {synthetic_failure}
Domain: {domain}
Context: {context}

Is progressive scarring replacing functional intellectual tissue, reducing capacity? Return ONLY valid JSON."""


class EpistemicCirrhosisService:
    """Detects epistemic cirrhosis — progressive scarring replacing functional tissue."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fibrosis: str,
        *,
        nodular_regeneration: str = "",
        decompensation: str = "",
        synthetic_failure: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic cirrhosis."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_CIRRHOSIS_PROMPT.format(
                fibrosis=fibrosis,
                nodular_regeneration=nodular_regeneration or "Not specified",
                decompensation=decompensation or "Not specified",
                synthetic_failure=synthetic_failure or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_CIRRHOSIS_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fibrosis": fibrosis[:200],
            "cirrhosis_present": data.get("cirrhosis_present", False),
            "severity": data.get("severity", ""),
            "nodular_regeneration": data.get("nodular_regeneration", ""),
            "decompensation": data.get("decompensation", ""),
            "synthetic_failure": data.get("synthetic_failure", ""),
            "recommendation": data.get("recommendation", ""),
        }
