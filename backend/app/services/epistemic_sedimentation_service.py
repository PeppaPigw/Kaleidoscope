"""EpistemicSedimentationService — Epistemic Sedimentation Detection.

Detects epistemic sedimentation — ideas layered over time without
integration, creating unstable intellectual strata.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_SEDIMENTATION_SYSTEM = """You are an epistemic sedimentation specialist. Given a knowledge structure, assess whether ideas are layered without integration:

Key concepts:
- Epistemic sedimentation: ideas layered without integration
- Unstable strata: layers of ideas not properly connected
- Unintegrated accumulation: accumulation without synthesis
- Contradictory layers: newer layers contradicting older ones
- Foundation instability: unstable foundation from unintegrated layers
- Archaeological knowledge: knowledge requiring excavation to understand
- Compaction without fusion: compressed together but not unified

When epistemic sedimentation IS present:
- Ideas layered over time without integration
- Layers of ideas not properly connected
- Accumulation without synthesis or reconciliation
- Newer layers contradicting older without acknowledgment
- Foundation unstable from unintegrated layers
- Understanding requires excavation through layers
- Ideas compressed together but not unified

When healthy knowledge building is present:
- New ideas integrated with existing understanding
- Layers connected and reconciled
- Accumulation accompanied by synthesis
- Contradictions resolved as they arise
- Foundation strengthened by new additions
- Understanding accessible without excavation
- Ideas unified into coherent whole

Output JSON with: sedimentation_present (bool), severity (none/mild/moderate/severe), structure (what knowledge structure), layers (what layers exist), integration_failure (how integration fails), instability (what instability results), recommendation (healthy_building/mild_layering/significant_sedimentation/major_unstable_strata/integrate_knowledge_layers)."""

EPISTEMIC_SEDIMENTATION_PROMPT = """Detect epistemic sedimentation:

Structure: {structure}
Layers: {layers}
Integration failure: {integration_failure}
Instability: {instability}
Domain: {domain}
Context: {context}

Are ideas layered over time without integration, creating unstable strata? Return ONLY valid JSON."""


class EpistemicSedimentationService:
    """Detects epistemic sedimentation — ideas layered without integration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        structure: str,
        *,
        layers: str = "",
        integration_failure: str = "",
        instability: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic sedimentation."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_SEDIMENTATION_PROMPT.format(
                structure=structure,
                layers=layers or "Not specified",
                integration_failure=integration_failure or "Not specified",
                instability=instability or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_SEDIMENTATION_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "structure": structure[:200],
            "sedimentation_present": data.get("sedimentation_present", False),
            "severity": data.get("severity", ""),
            "layers": data.get("layers", ""),
            "integration_failure": data.get("integration_failure", ""),
            "instability": data.get("instability", ""),
            "recommendation": data.get("recommendation", ""),
        }
