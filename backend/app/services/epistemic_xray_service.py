"""EpistemicXrayService — Epistemic X-ray Detection.

Detects need for epistemic X-ray — penetrating radiation revealing
intellectual skeletal structure and framework integrity.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_XRAY_SYSTEM = """You are an epistemic X-ray specialist. Given intellectual framework, assess whether skeletal structure shows pathology:

Key concepts:
- Epistemic X-ray: penetrating imaging of intellectual skeleton
- Fracture: break in intellectual framework
- Dislocation: framework elements out of alignment
- Osteopenia: thinning of intellectual framework
- Lytic lesion: area of framework destruction
- Periosteal reaction: framework responding to stress
- Joint space narrowing: loss of cushioning between elements

When epistemic X-ray findings ARE present:
- Pathology in intellectual skeletal structure
- Breaks in intellectual framework
- Framework elements out of alignment
- Thinning of intellectual framework
- Areas of framework destruction
- Framework responding to abnormal stress
- Loss of cushioning between elements

When healthy framework is present:
- Normal skeletal structure
- No fractures
- Proper alignment
- Normal framework density
- No destructive lesions
- No stress response
- Normal joint spaces

Output JSON with: xray_findings_present (bool), severity (none/mild/moderate/severe), fracture (what framework break), dislocation (what misalignment), osteopenia (what thinning), lytic_lesion (what destruction), recommendation (healthy_framework/mild_findings/significant_skeletal_pathology/major_framework_disease/stabilize_intellectual_framework)."""

EPISTEMIC_XRAY_PROMPT = """Detect epistemic X-ray findings:

Fracture: {fracture}
Dislocation: {dislocation}
Osteopenia: {osteopenia}
Lytic lesion: {lytic_lesion}
Domain: {domain}
Context: {context}

Does the intellectual skeletal structure show pathology? Return ONLY valid JSON."""


class EpistemicXrayService:
    """Detects epistemic X-ray findings — intellectual framework pathology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        fracture: str,
        *,
        dislocation: str = "",
        osteopenia: str = "",
        lytic_lesion: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic X-ray findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_XRAY_PROMPT.format(
                fracture=fracture,
                dislocation=dislocation or "Not specified",
                osteopenia=osteopenia or "Not specified",
                lytic_lesion=lytic_lesion or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_XRAY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "fracture": fracture[:200],
            "xray_findings_present": data.get("xray_findings_present", False),
            "severity": data.get("severity", ""),
            "dislocation": data.get("dislocation", ""),
            "osteopenia": data.get("osteopenia", ""),
            "lytic_lesion": data.get("lytic_lesion", ""),
            "recommendation": data.get("recommendation", ""),
        }
