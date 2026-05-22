"""CruxEngineService — Adversarial Thesis Resolver.

Generates rival theses for a research question, identifies crux claims
(the smallest set that would flip the answer), and resolves them.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import GlobalClaim, ClaimRelation

logger = structlog.get_logger(__name__)

RIVAL_SYSTEM = """You are a research hypothesis generator. Given a research question, generate 2-4 competing theses that represent genuinely different answers. Each thesis should be defensible and represent a real position in the literature.

Rules:
- Generate exactly the number of theses requested (2-4)
- Each thesis must be a clear, falsifiable claim (25-200 chars)
- Theses should be mutually exclusive or represent meaningfully different positions
- Include the mainstream view AND at least one contrarian/minority position
- Order from most to least likely based on current evidence

Output JSON:
{
  "theses": [
    {
      "text": "the thesis statement",
      "prior_confidence": 0.0-1.0,
      "position": "mainstream|contrarian|emerging|minority",
      "key_assumption": "the critical assumption this thesis depends on"
    }
  ]
}"""

RIVAL_PROMPT = """Research question: {question}

Generate {n_theses} competing theses. Return ONLY valid JSON."""

CRUX_SYSTEM = """You are a crux identifier. Given two competing theses, identify the single most important empirically testable claim that would flip which thesis wins. Be extremely concise.

Output ONLY this JSON (no explanation):
{"crux_claim": "short claim text under 120 chars", "why_decisive": "one short sentence", "thesis_if_true": 0, "thesis_if_false": 1, "estimated_resolution_cost": 5}"""

CRUX_PROMPT = """Thesis A: {thesis_a}
(Assumption: {supports_a})

Thesis B: {thesis_b}
(Assumption: {supports_b})

Return ONLY the JSON object, nothing else."""


class CruxEngineService:
    """Adversarial thesis resolver with crux identification."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_question(
        self,
        question: str,
        *,
        dossier_id: str | None = None,
        n_theses: int = 3,
        resolve_cruxes: bool = True,
        budget_papers: int = 8,
    ) -> dict:
        """Full crux analysis: generate rivals → identify cruxes → resolve → recompute."""
        import json
        import re
        from app.clients.llm_client import LLMClient

        llm = LLMClient()

        raw = await llm.complete(
            prompt=RIVAL_PROMPT.format(question=question, n_theses=n_theses),
            system=RIVAL_SYSTEM,
            max_tokens=2048,
            temperature=0.3,
        )
        rival_data = self._parse_json(raw)
        theses_raw = rival_data.get("theses", [])

        if not theses_raw:
            return {"error": "Failed to generate rival theses", "question": question}

        from app.services.claim_ledger_service import ClaimLedgerService
        ledger = ClaimLedgerService(self.db)

        theses = []
        for t in theses_raw[:4]:
            text = t.get("text", "")
            if not text:
                continue

            result = await ledger.upsert_claim(
                text=text,
                dossier_id=dossier_id,
                source_tool="crux_engine",
            )
            claim_id = None
            if result and not result.get("error"):
                claim_id = result.get("claim_id") or result.get("global_claim_id")
                if not claim_id:
                    claims = result.get("claims", [])
                    if claims:
                        claim_id = claims[0].get("claim_id") or claims[0].get("global_claim_id")

            theses.append({
                "text": text,
                "claim_id": str(claim_id) if claim_id else None,
                "prior_confidence": t.get("prior_confidence", 0.5),
                "position": t.get("position", "unknown"),
                "key_assumption": t.get("key_assumption", ""),
                "current_confidence": t.get("prior_confidence", 0.5),
                "supporting_claims": [],
                "contradicting_claims": [],
            })

        cruxes = await self._identify_cruxes(theses, llm, dossier_id, ledger)

        resolution_results = []
        if resolve_cruxes and cruxes:
            per_crux_budget = max(2, budget_papers // len(cruxes[:3]))
            for crux in cruxes[:3]:
                if crux.get("claim_id"):
                    res = await self._resolve_crux(crux, dossier_id, per_crux_budget)
                    resolution_results.append(res)

        for i, thesis in enumerate(theses):
            thesis["current_confidence"] = self._recompute_thesis_confidence(
                thesis, cruxes, resolution_results
            )

        theses.sort(key=lambda t: t["current_confidence"], reverse=True)

        winner = theses[0] if theses else None
        runner_up = theses[1] if len(theses) > 1 else None
        margin = (winner["current_confidence"] - runner_up["current_confidence"]) if winner and runner_up else 0

        stabilized = margin > 0.2 or (not cruxes)

        return {
            "question": question,
            "status": "stabilized" if stabilized else "contested",
            "winning_thesis": winner["text"] if winner else None,
            "winning_confidence": round(winner["current_confidence"], 3) if winner else 0,
            "margin": round(margin, 3),
            "theses": [
                {
                    "rank": i + 1,
                    "text": t["text"],
                    "claim_id": t["claim_id"],
                    "position": t["position"],
                    "prior_confidence": t["prior_confidence"],
                    "current_confidence": round(t["current_confidence"], 3),
                    "key_assumption": t["key_assumption"],
                }
                for i, t in enumerate(theses)
            ],
            "crux_claims": [
                {
                    "text": c["text"],
                    "claim_id": c.get("claim_id"),
                    "why_decisive": c.get("why_decisive", ""),
                    "thesis_if_true": c.get("thesis_if_true"),
                    "thesis_if_false": c.get("thesis_if_false"),
                    "resolution_cost": c.get("estimated_resolution_cost", 5),
                    "resolved": c.get("resolved", False),
                    "resolution_stance": c.get("resolution_stance"),
                }
                for c in cruxes
            ],
            "resolution_results": resolution_results,
            "next_actions": self._compute_next_actions(theses, cruxes, stabilized),
        }

    async def _identify_cruxes(self, theses, llm, dossier_id, ledger) -> list:
        cruxes = []
        if len(theses) < 2:
            return cruxes

        for i in range(len(theses)):
            for j in range(i + 1, min(len(theses), i + 3)):
                try:
                    raw = await llm.complete(
                        prompt=CRUX_PROMPT.format(
                            thesis_a=theses[i]["text"],
                            supports_a=theses[i].get("key_assumption", ""),
                            thesis_b=theses[j]["text"],
                            supports_b=theses[j].get("key_assumption", ""),
                        ),
                        system=CRUX_SYSTEM,
                        max_tokens=1024,
                        temperature=0.1,
                    )
                    crux_data = self._parse_json(raw)
                    crux_text = crux_data.get("crux_claim", "")
                    if not crux_text:
                        continue

                    result = await ledger.upsert_claim(
                        text=crux_text,
                        dossier_id=dossier_id,
                        source_tool="crux_engine",
                    )
                    claim_id = None
                    if result and not result.get("error"):
                        claim_id = result.get("claim_id") or result.get("global_claim_id")
                        if not claim_id:
                            claims = result.get("claims", [])
                            if claims:
                                claim_id = claims[0].get("claim_id") or claims[0].get("global_claim_id")

                    cruxes.append({
                        "text": crux_text,
                        "claim_id": str(claim_id) if claim_id else None,
                        "why_decisive": crux_data.get("why_decisive", ""),
                        "thesis_if_true": i,
                        "thesis_if_false": j,
                        "estimated_resolution_cost": crux_data.get("estimated_resolution_cost", 5),
                        "resolved": False,
                        "resolution_stance": None,
                    })
                except Exception as e:
                    logger.warning("crux_identification_error", error=str(e))

        cruxes.sort(key=lambda c: c.get("estimated_resolution_cost", 10))
        return cruxes

    async def _resolve_crux(self, crux: dict, dossier_id: str | None, budget: int) -> dict:
        from app.services.claim_resolution_service import ClaimResolutionService
        resolver = ClaimResolutionService(self.db)

        try:
            result = await resolver.resolve_claim(
                crux["claim_id"],
                objective="strengthen",
                budget_papers=budget,
                dossier_id=dossier_id,
            )

            if result.get("status") == "resolved":
                supports = result.get("adjudications", {}).get("supports", 0)
                contradicts = result.get("adjudications", {}).get("contradicts", 0)
                if supports > contradicts:
                    crux["resolved"] = True
                    crux["resolution_stance"] = "supported"
                elif contradicts > supports:
                    crux["resolved"] = True
                    crux["resolution_stance"] = "contradicted"

            return {
                "crux_text": crux["text"][:80],
                "claim_id": crux["claim_id"],
                "resolved": crux["resolved"],
                "stance": crux.get("resolution_stance"),
                "confidence_delta": result.get("confidence_delta", 0),
                "papers_searched": result.get("papers_searched", 0),
            }
        except Exception as e:
            logger.warning("crux_resolution_error", error=str(e))
            return {"crux_text": crux["text"][:80], "error": str(e)}

    def _recompute_thesis_confidence(self, thesis, cruxes, resolutions) -> float:
        conf = thesis["prior_confidence"]

        for crux in cruxes:
            if not crux.get("resolved"):
                continue
            stance = crux.get("resolution_stance")
            thesis_idx_if_true = crux.get("thesis_if_true")
            thesis_idx_if_false = crux.get("thesis_if_false")

            if stance == "supported":
                if thesis.get("text") and thesis_idx_if_true is not None:
                    conf += 0.1
            elif stance == "contradicted":
                if thesis.get("text") and thesis_idx_if_false is not None:
                    conf -= 0.05

        return max(0.05, min(0.95, conf))

    def _compute_next_actions(self, theses, cruxes, stabilized) -> list:
        if stabilized:
            return [{"action": "report", "reason": "Thesis stabilized with sufficient margin"}]

        actions = []
        unresolved = [c for c in cruxes if not c.get("resolved")]
        for crux in unresolved[:3]:
            actions.append({
                "action": "resolve_crux",
                "claim_id": crux.get("claim_id"),
                "crux_text": crux["text"][:60],
                "expected_impact": "Could flip winning thesis",
                "tool": "claim_resolve",
            })

        if not actions:
            actions.append({
                "action": "broaden_search",
                "reason": "All identified cruxes resolved but margin still narrow",
                "tool": "research_run_start",
            })

        return actions

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if fence:
            try:
                return json.loads(fence.group(1).strip())
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}
