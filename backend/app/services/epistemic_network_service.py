"""EpistemicNetworkService — Knowledge Flow & Power Structure Analysis.

Maps how knowledge flows between researchers, institutions, and fields.
Identifies gatekeepers, echo chambers, information bottlenecks, and
power structures that shape what gets published and believed.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

NETWORK_SYSTEM = """You are an epistemic network analyst. Given a research domain, map the social and institutional structures that shape knowledge production: who are the gatekeepers, where are the echo chambers, what bottlenecks exist, and how does power flow through the network.

Output JSON with: network.domain, network.key_actors (list of actor/role gatekeeper|hub|bridge|peripheral/influence 0-1/mechanism), network.echo_chambers (list of chamber/members_description/shared_assumptions/blind_spots), network.bottlenecks (list of bottleneck/type institutional|methodological|funding|publication/severity 0-1/consequence), network.power_structures (list of structure/who_benefits/who_is_excluded/how_it_perpetuates), network.information_flows (list of from/to/what/speed fast|slow|blocked/quality 0-1), network.vulnerability_points (list of point/if_disrupted_then), network.reform_opportunities (list of opportunity/feasibility 0-1/impact 0-1)."""

NETWORK_PROMPT = """Analyze the epistemic network:

Domain: {domain}
Focus: {focus}

Known context:
{context_text}

Map knowledge flow structures. Return ONLY valid JSON."""

BIAS_LANDSCAPE_SYSTEM = """You are a research bias cartographer. Given a field, map the systematic biases that shape what gets studied, published, and believed. Include publication bias, funding bias, methodology bias, geographic bias, and paradigm bias.

Output JSON with: bias_landscape.domain, bias_landscape.biases (list of bias_type/description/severity 0-1/direction what_it_favors/what_it_suppresses/evidence_of_bias/correction_mechanism), bias_landscape.overall_distortion (0-1 how distorted the field's knowledge is), bias_landscape.most_affected_questions (list of question/how_biased/true_answer_likelihood), bias_landscape.correction_priorities (ordered list of what to fix first), bias_landscape.unbiased_estimate (what we'd believe with perfect information)."""

BIAS_LANDSCAPE_PROMPT = """Map the bias landscape:

Domain: {domain}
Topic: {topic}

Known findings:
{findings_text}

Map systematic biases. Return ONLY valid JSON."""


class EpistemicNetworkService:
    """Analyzes epistemic networks and bias landscapes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_network(
        self,
        domain: str,
        *,
        focus: str = "",
        dossier_id: str | None = None,
    ) -> dict:
        """Map the epistemic network of a research domain."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        context = await self._gather_context(domain, dossier_id)
        context_text = "\n".join(f"- {c}" for c in context[:8]) or "General domain knowledge"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=NETWORK_PROMPT.format(
                domain=domain,
                focus=focus or "overall structure",
                context_text=context_text,
            ),
            system=NETWORK_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        net = data.get("network", data)

        return {
            "domain": domain,
            "key_actors": net.get("key_actors", []),
            "echo_chambers": net.get("echo_chambers", []),
            "bottlenecks": net.get("bottlenecks", []),
            "power_structures": net.get("power_structures", []),
            "information_flows": net.get("information_flows", []),
            "vulnerability_points": net.get("vulnerability_points", []),
            "reform_opportunities": net.get("reform_opportunities", []),
        }

    async def map_bias_landscape(
        self,
        domain: str,
        *,
        topic: str = "",
        findings: list[str] | None = None,
        dossier_id: str | None = None,
    ) -> dict:
        """Map systematic biases in a research field."""
        from app.clients.llm_client import LLMClient
        from app.services.llm_utils import parse_llm_json

        extra = await self._gather_context(topic or domain, dossier_id)
        all_findings = (findings or []) + extra
        findings_text = "\n".join(f"- {f}" for f in all_findings[:8]) or "General field findings"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=BIAS_LANDSCAPE_PROMPT.format(
                domain=domain,
                topic=topic or domain,
                findings_text=findings_text,
            ),
            system=BIAS_LANDSCAPE_SYSTEM,
            max_tokens=4096,
            temperature=0.4,
        )
        data = parse_llm_json(raw)
        bias = data.get("bias_landscape", data)

        return {
            "domain": domain,
            "biases": bias.get("biases", []),
            "overall_distortion": bias.get("overall_distortion", 0),
            "most_affected_questions": bias.get("most_affected_questions", []),
            "correction_priorities": bias.get("correction_priorities", []),
            "unbiased_estimate": bias.get("unbiased_estimate", ""),
        }

    async def _gather_context(self, query: str, dossier_id: str | None) -> list[str]:
        try:
            from app.services.search.vector_search import VectorSearchService
            svc = VectorSearchService()
            results = svc.search(query=query[:100], top_k=5)
            return [r.get("payload", {}).get("text", "")[:120] for r in results]
        except Exception:
            return []
