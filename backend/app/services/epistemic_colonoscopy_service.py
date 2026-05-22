"""EpistemicColonoscopyService — Epistemic Colonoscopy Detection.

Detects need for epistemic colonoscopy — examining the full length of
intellectual processing pathway for hidden pathology.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EPISTEMIC_COLONOSCOPY_SYSTEM = """You are an epistemic colonoscopy specialist. Given intellectual processing pathways, assess whether hidden pathology exists along the full length:

Key concepts:
- Epistemic colonoscopy: examining full intellectual processing pathway
- Polyp: benign growth that could become malignant
- Stricture: narrowing of the processing pathway
- Diverticulum: outpouching weakness in pathway wall
- Occult bleeding: hidden loss not visible externally
- Mucosal inflammation: surface irritation of pathway
- Transit time: speed of processing through pathway

When epistemic colonoscopy findings ARE present:
- Hidden pathology along processing pathway
- Benign growths with malignant potential
- Narrowing restricting intellectual throughput
- Weakness outpouchings in pathway walls
- Hidden intellectual loss not externally visible
- Surface irritation of processing pathway
- Abnormal processing transit time

When healthy pathway is present:
- Clean processing pathway
- No growths or polyps
- Full-width pathway
- Strong intact walls
- No hidden losses
- Healthy mucosal surface
- Normal transit time

Output JSON with: colonoscopy_findings_present (bool), severity (none/mild/moderate/severe), polyps (what benign growths), stricture (what narrowing), diverticulum (what wall weakness), occult_bleeding (what hidden loss), recommendation (healthy_pathway/mild_findings/significant_pathology/major_processing_disease/intervene_intellectual_pathway)."""

EPISTEMIC_COLONOSCOPY_PROMPT = """Detect epistemic colonoscopy findings:

Polyps: {polyps}
Stricture: {stricture}
Diverticulum: {diverticulum}
Occult bleeding: {occult_bleeding}
Domain: {domain}
Context: {context}

Is there hidden pathology along the full intellectual processing pathway? Return ONLY valid JSON."""


class EpistemicColonoscopyService:
    """Detects epistemic colonoscopy findings — hidden processing pathway pathology."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect(
        self,
        polyps: str,
        *,
        stricture: str = "",
        diverticulum: str = "",
        occult_bleeding: str = "",
        domain: str = "",
        context: str = "",
    ) -> dict:
        """Detect epistemic colonoscopy findings."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        llm = LLMClient()
        raw = await llm.complete(
            prompt=EPISTEMIC_COLONOSCOPY_PROMPT.format(
                polyps=polyps,
                stricture=stricture or "Not specified",
                diverticulum=diverticulum or "Not specified",
                occult_bleeding=occult_bleeding or "Not specified",
                domain=domain or "general",
                context=context or "No additional context",
            ),
            system=EPISTEMIC_COLONOSCOPY_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        data = parse_llm_json(raw)

        return {
            "polyps": polyps[:200],
            "colonoscopy_findings_present": data.get("colonoscopy_findings_present", False),
            "severity": data.get("severity", ""),
            "stricture": data.get("stricture", ""),
            "diverticulum": data.get("diverticulum", ""),
            "occult_bleeding": data.get("occult_bleeding", ""),
            "recommendation": data.get("recommendation", ""),
        }
