"""ResearchThreadService — Research Thread Compiler.

Splits a dossier's claims into stable, persistent research threads.
Each thread is a coherent cluster of claims around a single research question
or hypothesis. Downstream tools (causal model, VOI planner, evidence audit)
consume thread_id for focused analysis.
"""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import GlobalClaim, ClaimRelation, ClaimMention

logger = structlog.get_logger(__name__)

CLUSTER_SYSTEM = """Group claims into research threads. Be extremely concise — short titles, brief scope, no elaboration.

Output JSON only:
{"threads": [{"id": "t1", "title": "under 40 chars", "scope": "one sentence", "thesis": "one sentence", "claim_ids": ["id1"], "open_questions": ["short question"]}], "bridges": [{"claim_id": "id", "from_thread": "t1", "to_thread": "t2", "relation": "short"}]}"""

CLUSTER_PROMPT = """Claims:
{claims_text}

Relations:
{relations_text}

Group into {max_threads} or fewer threads. Use claim IDs exactly as shown. Return ONLY JSON, no explanation."""


class ResearchThreadService:
    """Compiles dossier claims into coherent research threads."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compile_threads(
        self,
        dossier_id: str,
        *,
        seed_claim_ids: list[str] | None = None,
        mode: str = "auto",
        include_bridges: bool = True,
        max_threads: int = 5,
    ) -> dict:
        """Compile claims into research threads."""
        import json
        from app.clients.llm_client import LLMClient

        claims = await self._gather_claims(dossier_id, seed_claim_ids)
        if not claims:
            return {"error": "No claims found in dossier", "dossier_id": dossier_id}

        relations = await self._gather_relations([str(c.id) for c in claims])

        claim_map = {str(c.id): c for c in claims}
        short_map = {str(c.id)[:8]: str(c.id) for c in claims}

        claims_text = "\n".join(
            f"- [{str(c.id)[:8]}] {c.canonical_text[:120]}"
            for c in claims
        )
        relations_text = "\n".join(
            f"- {str(r.source_claim_id)[:8]} --{r.relation}--> {str(r.target_claim_id)[:8]}"
            for r in relations[:50]
        ) or "None"

        llm = LLMClient()
        raw = await llm.complete(
            prompt=CLUSTER_PROMPT.format(
                claims_text=claims_text,
                relations_text=relations_text,
                max_threads=max_threads,
            ),
            system=CLUSTER_SYSTEM,
            max_tokens=4096,
            temperature=0.2,
        )
        cluster_data = self._parse_json(raw)

        threads = []
        all_assigned = set()

        for t in cluster_data.get("threads", []):
            thread_id = str(uuid.uuid4())
            raw_ids = t.get("claim_ids", [])
            resolved_ids = []
            for rid in raw_ids:
                full = self._resolve_id(rid, short_map, claim_map)
                if full and full in claim_map:
                    resolved_ids.append(full)
                    all_assigned.add(full)

            if not resolved_ids:
                continue

            thread_claims = [claim_map[cid] for cid in resolved_ids if cid in claim_map]
            avg_confidence = 0
            if thread_claims:
                confs = [c.effective_confidence or c.direct_confidence or 0 for c in thread_claims]
                avg_confidence = sum(confs) / len(confs) if confs else 0

            evidence_coverage = self._compute_coverage(thread_claims)

            threads.append({
                "thread_id": thread_id,
                "title": t.get("title", "Untitled thread"),
                "scope_statement": t.get("scope", ""),
                "thesis": t.get("thesis", ""),
                "claim_ids": resolved_ids,
                "evidence_coverage": round(evidence_coverage, 2),
                "confidence": round(avg_confidence, 3),
                "open_questions": t.get("open_questions", [])[:5],
            })

        unassigned = [cid for cid in claim_map if cid not in all_assigned]
        if unassigned and threads:
            threads[0]["claim_ids"].extend(unassigned)

        claim_assignments = []
        for thread in threads:
            for cid in thread["claim_ids"]:
                claim_assignments.append({
                    "claim_id": cid,
                    "primary_thread_id": thread["thread_id"],
                })

        bridge_claims = []
        if include_bridges:
            for b in cluster_data.get("bridges", []):
                bid = b.get("claim_id", "")
                full_bid = self._resolve_id(bid, short_map, claim_map)
                if full_bid and full_bid in claim_map:
                    from_thread = self._find_thread_for_id(b.get("from_thread", ""), threads, cluster_data)
                    to_thread = self._find_thread_for_id(b.get("to_thread", ""), threads, cluster_data)
                    bridge_claims.append({
                        "claim_id": full_bid,
                        "from_thread_id": from_thread,
                        "to_thread_id": to_thread,
                        "relation": b.get("relation", "connects"),
                    })

        next_actions = self._compute_next_actions(threads)

        return {
            "dossier_id": dossier_id,
            "threads": threads,
            "claim_assignments": claim_assignments,
            "bridge_claims": bridge_claims,
            "next_actions": next_actions,
            "stats": {
                "total_claims": len(claims),
                "threads_created": len(threads),
                "claims_assigned": len(all_assigned),
                "bridge_claims": len(bridge_claims),
            },
        }

    async def _gather_claims(self, dossier_id: str, seed_claim_ids: list[str] | None) -> list[GlobalClaim]:
        if seed_claim_ids:
            uuids = [uuid.UUID(c) for c in seed_claim_ids]
            result = await self.db.execute(
                select(GlobalClaim).where(GlobalClaim.id.in_(uuids))
            )
            return list(result.scalars().all())

        mention_q = await self.db.execute(
            select(ClaimMention.global_claim_id)
            .where(ClaimMention.dossier_id == uuid.UUID(dossier_id))
            .distinct()
            .limit(100)
        )
        claim_ids = [r[0] for r in mention_q.all()]
        if not claim_ids:
            return []

        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id.in_(claim_ids))
        )
        return list(result.scalars().all())

    async def _gather_relations(self, claim_ids: list[str]) -> list[ClaimRelation]:
        uuids = [uuid.UUID(c) for c in claim_ids]
        result = await self.db.execute(
            select(ClaimRelation)
            .where(
                (ClaimRelation.source_claim_id.in_(uuids))
                | (ClaimRelation.target_claim_id.in_(uuids))
            )
            .limit(200)
        )
        return list(result.scalars().all())

    def _resolve_id(self, short_id: str, short_map: dict, claim_map: dict) -> str | None:
        if short_id in short_map:
            return short_map[short_id]
        if short_id in claim_map:
            return short_id
        for key, full in short_map.items():
            if key.startswith(short_id):
                return full
        return None

    def _compute_coverage(self, claims: list[GlobalClaim]) -> float:
        if not claims:
            return 0.0
        scored = [c for c in claims if c.evidence_strength_score and c.evidence_strength_score > 0]
        if not scored:
            return 0.0
        avg_strength = sum(c.evidence_strength_score for c in scored) / len(scored)
        coverage_ratio = len(scored) / len(claims)
        return (avg_strength / 100.0) * coverage_ratio

    def _find_thread_for_id(self, thread_ref: str, threads: list, cluster_data: dict) -> str:
        raw_threads = cluster_data.get("threads", [])
        for i, rt in enumerate(raw_threads):
            if rt.get("id") == thread_ref and i < len(threads):
                return threads[i]["thread_id"]
        if threads:
            return threads[0]["thread_id"]
        return ""

    def _compute_next_actions(self, threads: list) -> list:
        actions = []
        for t in threads:
            if t["confidence"] < 0.3:
                actions.append({
                    "action": "strengthen_thread",
                    "thread_id": t["thread_id"],
                    "thread_title": t["title"],
                    "reason": f"Low confidence ({t['confidence']:.2f})",
                    "tool": "research_run_start",
                })
            if t["open_questions"]:
                actions.append({
                    "action": "resolve_question",
                    "thread_id": t["thread_id"],
                    "question": t["open_questions"][0],
                    "tool": "question_resolve",
                })
        return actions[:5]

    def _parse_json(self, text: str) -> dict:
        import json
        import re
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*\n?(.*?)(?:\n?```|$)", text, re.DOTALL)
        if fence:
            candidate = fence.group(1).strip()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        match = re.search(r"\{.*", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = self._repair_json(candidate)
                if repaired:
                    return repaired
        return {}

    def _repair_json(self, text: str) -> dict | None:
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
