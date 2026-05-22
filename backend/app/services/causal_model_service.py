"""CausalModelService — Causal Model Compiler.

Compiles a dossier's claims into a typed causal/mechanistic model with
explicit confounders, boundary conditions, and intervention predictions.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import GlobalClaim, ClaimRelation, ClaimMention

logger = structlog.get_logger(__name__)

NODE_SYSTEM = """You classify research claims by causal role. For each claim, assign exactly one role:
- intervention: something that can be manipulated
- outcome: the effect being studied
- mediator: mechanism between cause and effect
- moderator: changes strength/direction of an effect
- confounder: common cause creating spurious associations
- metric: measurement or operationalization
- assumption: background condition taken as given

Output JSON: {"nodes": [{"claim_id": "id", "role": "role", "label": "short label under 40 chars"}]}"""

NODE_PROMPT = """Research question: {question}

Claims:
{claims_text}

Classify each claim's causal role. Return ONLY valid JSON."""

EDGE_SYSTEM = """You identify causal edges between research claims. For each pair with a causal relationship, classify:
- causes: A directly produces or enables B
- inhibits: A prevents or reduces B
- mediates: A is the mechanism through which X affects B
- moderates: A changes the strength/direction of X→B
- confounds: A is a common cause of both X and B
- measured_by: A is operationalized through B
- holds_under: A is true only when condition B holds

Also identify missing confounders and boundary conditions.

Output JSON: {"edges": [{"source_id": "id", "target_id": "id", "relation": "type", "scope_conditions": []}], "missing_confounders": ["text"], "boundary_conditions": ["text"]}"""

EDGE_PROMPT = """Research question: {question}

Nodes (classified claims):
{nodes_text}

Known relationships:
{relations_text}

Identify causal edges between these nodes. Return ONLY valid JSON."""

INTERVENTION_SYSTEM = """You are a causal reasoning engine. Given a causal model (nodes and edges), predict what would happen if a specific intervention were made.

For each intervention, predict:
- Which downstream nodes would be affected
- Direction and approximate magnitude of effect
- Which edges would be activated or blocked
- Confidence in the prediction

Output JSON:
{
  "predictions": [
    {
      "intervention": "description",
      "affected_nodes": ["claim_id"],
      "predicted_effect": "description of what changes",
      "confidence": 0.0-1.0,
      "reasoning": "one sentence"
    }
  ]
}"""

INTERVENTION_PROMPT = """Causal model nodes:
{nodes_text}

Causal model edges:
{edges_text}

Target outcomes: {outcomes}

Generate intervention predictions for the most impactful manipulable nodes. Return ONLY valid JSON."""


class CausalModelService:
    """Compiles claims into a typed causal/mechanistic model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_model(
        self,
        *,
        dossier_id: str | None = None,
        question: str | None = None,
        focus_claim_ids: list[str] | None = None,
        mode: str = "build",
        max_claims: int = 50,
        max_edges: int = 100,
        target_outcomes: list[str] | None = None,
    ) -> dict:
        """Compile a causal model from dossier claims."""
        import json
        from app.clients.llm_client import LLMClient

        claims = await self._gather_claims(dossier_id, focus_claim_ids, max_claims)
        if not claims:
            return {"error": "No claims found", "status": "empty"}

        relations = await self._gather_relations(
            [str(c.id) for c in claims], max_edges
        )

        llm = LLMClient()

        claims_text = "\n".join(
            f"- [{str(c.id)[:8]}] {c.canonical_text[:150]} "
            f"(strength={c.evidence_strength_score or 0:.0f}, "
            f"confidence={c.effective_confidence or c.direct_confidence or 0:.2f})"
            for c in claims[:max_claims]
        )

        relations_text = "\n".join(
            f"- {str(r.source_claim_id)[:8]} --{r.relation}--> {str(r.target_claim_id)[:8]} "
            f"(confidence={r.confidence:.2f})"
            for r in relations[:max_edges]
        )

        claim_map = {str(c.id): c for c in claims}
        claim_short_map = {str(c.id)[:8]: str(c.id) for c in claims}

        def resolve_id(short_id: str) -> str:
            """Resolve a potentially truncated ID prefix to the full UUID."""
            if short_id in claim_short_map:
                return claim_short_map[short_id]
            if short_id in claim_map:
                return short_id
            for key, full in claim_short_map.items():
                if key.startswith(short_id):
                    return full
            return short_id

        # Step 1: Classify nodes
        node_raw = await llm.complete(
            prompt=NODE_PROMPT.format(
                claims_text=claims_text,
                question=question or "General causal structure",
            ),
            system=NODE_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        node_data = self._parse_json(node_raw)

        nodes = []
        for n in node_data.get("nodes", []):
            cid = n.get("claim_id", "")
            full_id = resolve_id(cid)
            claim = claim_map.get(full_id)
            nodes.append({
                "id": full_id,
                "label": n.get("label", claim.canonical_text[:60] if claim else cid),
                "type": n.get("role", "assumption"),
                "linked_claim_ids": [full_id] if full_id in claim_map else [],
                "confidence": float(claim.effective_confidence or claim.direct_confidence or 0) if claim else 0,
                "evidence_strength": float(claim.evidence_strength_score or 0) if claim else 0,
            })

        # Step 2: Identify edges
        nodes_text_for_edges = "\n".join(
            f"- [{n['id'][:8]}] {n['label']} (role={n['type']})"
            for n in nodes
        )
        edge_raw = await llm.complete(
            prompt=EDGE_PROMPT.format(
                nodes_text=nodes_text_for_edges or claims_text,
                relations_text=relations_text or "None identified yet",
                question=question or "General causal structure",
            ),
            system=EDGE_SYSTEM,
            max_tokens=2048,
            temperature=0.2,
        )
        edge_data = self._parse_json(edge_raw)

        missing_confounders = edge_data.get("missing_confounders", [])
        boundary_conditions = edge_data.get("boundary_conditions", [])

        edges = []
        for e in edge_data.get("edges", []):
            src = resolve_id(e.get("source_id", ""))
            tgt = resolve_id(e.get("target_id", ""))
            src_claim = claim_map.get(src)
            tgt_claim = claim_map.get(tgt)

            supporting = []
            contradicting = []
            for r in relations:
                if str(r.source_claim_id) == src and str(r.target_claim_id) == tgt:
                    if r.relation == "supports":
                        supporting.append(str(r.source_claim_id))
                    elif r.relation == "contradicts":
                        contradicting.append(str(r.source_claim_id))

            edge_confidence = 0.5
            if src_claim and tgt_claim:
                s1 = src_claim.effective_confidence or src_claim.direct_confidence or 0
                s2 = tgt_claim.effective_confidence or tgt_claim.direct_confidence or 0
                edge_confidence = (s1 + s2) / 2

            edges.append({
                "source": src,
                "target": tgt,
                "relation": e.get("relation", "causes"),
                "confidence": round(edge_confidence, 3),
                "support_score": float(src_claim.evidence_strength_score or 0) if src_claim else 0,
                "supporting_claim_ids": supporting,
                "contradicting_claim_ids": contradicting,
                "scope_conditions": e.get("scope_conditions", []),
            })

        missing_confounders = edge_data.get("missing_confounders", [])
        boundary_conditions = edge_data.get("boundary_conditions", [])

        high_value_unknowns = self._identify_unknowns(nodes, edges, missing_confounders)

        intervention_predictions = []
        if mode in ("build", "intervene") and nodes and edges:
            intervention_predictions = await self._predict_interventions(
                llm, nodes, edges, target_outcomes or []
            )

        cruxes = self._identify_model_cruxes(nodes, edges)

        next_actions = self._compute_next_actions(high_value_unknowns, edges)

        model_id = str(uuid.uuid4())

        return {
            "model_id": model_id,
            "status": "built" if nodes else "partial",
            "question": question,
            "dossier_id": dossier_id,
            "nodes": nodes,
            "edges": edges,
            "high_value_unknowns": high_value_unknowns,
            "intervention_predictions": intervention_predictions,
            "cruxes": cruxes,
            "boundary_conditions": boundary_conditions,
            "missing_confounders": missing_confounders,
            "next_actions": next_actions,
            "stats": {
                "claims_analyzed": len(claims),
                "relations_found": len(relations),
                "nodes_in_model": len(nodes),
                "edges_in_model": len(edges),
                "weak_edges": sum(1 for e in edges if e["confidence"] < 0.4),
                "strong_edges": sum(1 for e in edges if e["confidence"] > 0.7),
            },
        }

    async def _gather_claims(
        self, dossier_id: str | None, focus_claim_ids: list[str] | None, max_claims: int
    ) -> list[GlobalClaim]:
        if focus_claim_ids:
            uuids = [uuid.UUID(c) for c in focus_claim_ids]
            result = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
            return list(result.scalars().all())

        if dossier_id:
            mention_q = await self.db.execute(
                select(ClaimMention.global_claim_id)
                .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
                .distinct()
                .limit(max_claims)
            )
            claim_ids = [r[0] for r in mention_q.all()]
            if claim_ids:
                result = await self.db.execute(
                    select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
                )
                return list(result.scalars().all())

        result = await self.db.execute(
            select(GlobalClaim)
            .where(GlobalClaim.status == "active")
            .order_by(GlobalClaim.evidence_strength_score.desc().nullslast())
            .limit(max_claims)
        )
        return list(result.scalars().all())

    async def _gather_relations(
        self, claim_ids: list[str], max_edges: int
    ) -> list[ClaimRelation]:
        uuids = [uuid.UUID(c) for c in claim_ids]
        result = await self.db.execute(
            select(ClaimRelation)
            .where(
                (ClaimRelation.source_claim_id.in_(uuids))
                | (ClaimRelation.target_claim_id.in_(uuids))
            )
            .limit(max_edges)
        )
        return list(result.scalars().all())

    async def _predict_interventions(
        self, llm, nodes: list, edges: list, target_outcomes: list
    ) -> list:
        interventions = [n for n in nodes if n["type"] == "intervention"]
        outcomes = [n for n in nodes if n["type"] == "outcome"]

        if not interventions or not outcomes:
            return []

        nodes_text = "\n".join(
            f"- [{n['id'][:8]}] {n['label']} (type={n['type']}, confidence={n['confidence']:.2f})"
            for n in nodes[:30]
        )
        edges_text = "\n".join(
            f"- {e['source'][:8]} --{e['relation']}--> {e['target'][:8]} (confidence={e['confidence']:.2f})"
            for e in edges[:40]
        )
        outcomes_text = ", ".join(target_outcomes) if target_outcomes else ", ".join(
            o["label"][:40] for o in outcomes[:3]
        )

        try:
            raw = await llm.complete(
                prompt=INTERVENTION_PROMPT.format(
                    nodes_text=nodes_text,
                    edges_text=edges_text,
                    outcomes=outcomes_text,
                ),
                system=INTERVENTION_SYSTEM,
                max_tokens=2048,
                temperature=0.2,
            )
            data = self._parse_json(raw)
            return data.get("predictions", [])[:5]
        except Exception as e:
            logger.warning("intervention_prediction_error", error=str(e))
            return []

    def _identify_unknowns(
        self, nodes: list, edges: list, missing_confounders: list
    ) -> list:
        unknowns = []

        for e in edges:
            if e["confidence"] < 0.4:
                unknowns.append({
                    "type": "weak_edge",
                    "description": f"Weak causal link: {e['source'][:8]}→{e['target'][:8]} ({e['relation']}, conf={e['confidence']:.2f})",
                    "expected_information_gain": round(0.4 - e["confidence"], 2),
                    "recommended_calls": [
                        {"tool": "claim_resolve", "args": {"claim_id": e["source"], "objective": "strengthen"}}
                    ],
                })

        for conf in missing_confounders[:3]:
            unknowns.append({
                "type": "missing_confounder",
                "description": conf,
                "expected_information_gain": 0.25,
                "recommended_calls": [
                    {"tool": "search_papers", "args": {"query": conf[:60], "mode": "semantic"}}
                ],
            })

        for n in nodes:
            if n["type"] == "assumption" and n["confidence"] < 0.3:
                unknowns.append({
                    "type": "boundary_condition",
                    "description": f"Weak assumption: {n['label']} (conf={n['confidence']:.2f})",
                    "expected_information_gain": 0.3,
                    "recommended_calls": [
                        {"tool": "claim_resolve", "args": {"claim_id": n["id"], "objective": "strengthen"}}
                    ],
                })

        unknowns.sort(key=lambda u: u["expected_information_gain"], reverse=True)
        return unknowns[:10]

    def _identify_model_cruxes(self, nodes: list, edges: list) -> list:
        cruxes = []

        outcome_nodes = {n["id"] for n in nodes if n["type"] == "outcome"}
        for e in edges:
            if e["target"] in outcome_nodes and e["confidence"] < 0.5:
                cruxes.append({
                    "node_or_edge_id": f"{e['source'][:8]}→{e['target'][:8]}",
                    "why_decisive": f"Direct {e['relation']} link to outcome with low confidence ({e['confidence']:.2f})",
                })

        for n in nodes:
            if n["type"] == "mediator" and n["confidence"] < 0.4:
                cruxes.append({
                    "node_or_edge_id": n["id"],
                    "why_decisive": f"Mediator node with low confidence ({n['confidence']:.2f}) — if wrong, causal path breaks",
                })

        return cruxes[:5]

    def _compute_next_actions(self, unknowns: list, edges: list) -> list:
        actions = []
        for u in unknowns[:3]:
            if u["recommended_calls"]:
                call = u["recommended_calls"][0]
                actions.append({
                    "tool": call["tool"],
                    "args": call["args"],
                    "reason": u["description"][:80],
                })

        if not actions:
            weak = [e for e in edges if e["confidence"] < 0.5]
            if weak:
                actions.append({
                    "tool": "research_next_best_action",
                    "args": {"objective": "maximize_certainty"},
                    "reason": f"{len(weak)} weak edges need strengthening",
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
        # Handle fenced JSON (complete or truncated)
        fence = re.search(r"```(?:json)?\s*\n?(.*?)(?:\n?```|$)", text, re.DOTALL)
        if fence:
            candidate = fence.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_truncated_json(candidate)
                if repaired:
                    return repaired
        # Try raw JSON extraction
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_truncated_json(candidate)
                if repaired:
                    return repaired
        return {}

    def _repair_truncated_json(self, text: str) -> dict | None:
        """Attempt to repair truncated JSON by closing open brackets/braces in correct order."""
        import json
        text = text.rstrip().rstrip(",")
        stack = []
        in_string = False
        escape = False
        for ch in text:
            if escape:
                escape = False
                continue
            if ch == '\\' and in_string:
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in ('}', ']'):
                if stack and stack[-1] == ch:
                    stack.pop()
        if in_string:
            text += '"'
        text = text.rstrip().rstrip(",")
        text += ''.join(reversed(stack))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
