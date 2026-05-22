"""ResearchStrategyService — Value-of-Information Planner for autonomous research agents."""

import uuid
from dataclasses import dataclass, field

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimRelation, GlobalClaim, ClaimMention

logger = structlog.get_logger(__name__)

OBJECTIVES = {
    "maximize_certainty": "Maximize overall dossier confidence by targeting weakest high-impact claims",
    "resolve_contradiction": "Prioritize resolving disputed claims with contradicting evidence",
    "stress_test": "Find evidence that could falsify or weaken the thesis",
    "fill_gaps": "Close literature gaps and dead-end dependency chains",
    "broaden_coverage": "Expand evidence base with independent replications and new sources",
}

ACTION_TYPES = {
    "smart_search": {"base_cost": 1.0, "base_yield": 0.6, "description": "Search for papers matching a targeted query"},
    "paper_qa": {"base_cost": 2.0, "base_yield": 0.7, "description": "Deep-read a specific paper to extract claims"},
    "contradiction_resolve": {"base_cost": 3.0, "base_yield": 0.8, "description": "Find meta-analysis or comparison study"},
    "replication_hunt": {"base_cost": 1.5, "base_yield": 0.5, "description": "Search for independent replications"},
    "upstream_strengthen": {"base_cost": 2.5, "base_yield": 0.75, "description": "Strengthen a weak upstream premise"},
    "topic_monitor": {"base_cost": 0.5, "base_yield": 0.3, "description": "Set up ongoing monitoring for new evidence"},
    "recency_update": {"base_cost": 1.0, "base_yield": 0.4, "description": "Find recent studies confirming stale claims"},
}

OBJECTIVE_BONUSES = {
    "maximize_certainty": {
        "upstream_strengthen": 0.3,
        "smart_search": 0.1,
        "paper_qa": 0.2,
    },
    "resolve_contradiction": {
        "contradiction_resolve": 0.5,
        "smart_search": 0.1,
    },
    "stress_test": {
        "smart_search": 0.2,
        "contradiction_resolve": 0.3,
        "replication_hunt": 0.1,
    },
    "fill_gaps": {
        "upstream_strengthen": 0.3,
        "smart_search": 0.2,
        "replication_hunt": 0.2,
    },
    "broaden_coverage": {
        "replication_hunt": 0.4,
        "smart_search": 0.2,
        "topic_monitor": 0.2,
    },
}


@dataclass
class CandidateAction:
    action_type: str
    target_claim_id: str
    target_claim_text: str
    utility: float = 0.0
    expected_confidence_lift: float = 0.0
    downstream_impact: int = 0
    reason: str = ""
    search_queries: list = field(default_factory=list)
    mcp_calls: list = field(default_factory=list)
    stopping_condition: str = ""


class ResearchStrategyService:
    """Goal-conditioned next-best-action engine for research agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def plan_next_actions(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        max_actions: int = 5,
        budget_papers: int = 10,
        target_claims: list[str] | None = None,
    ) -> dict:
        """Compute the top-N highest-utility research actions for a dossier."""
        if objective not in OBJECTIVES:
            return {"error": f"Unknown objective. Choose from: {list(OBJECTIVES.keys())}"}

        mentions_q = await self.db.execute(
            select(ClaimMention.global_claim_id).where(
                ClaimMention.dossier_id == uuid.UUID(dossier_id)
            ).distinct()
        )
        claim_ids = [row[0] for row in mentions_q.all()]

        if not claim_ids:
            return {"dossier_id": dossier_id, "actions": [], "objective": objective,
                    "message": "No claims in dossier"}

        claims_q = await self.db.execute(
            select(GlobalClaim).where(
                GlobalClaim.id.in_(claim_ids),
                GlobalClaim.status != "rejected",
            )
        )
        claims = claims_q.scalars().all()
        claim_map = {c.id: c for c in claims}

        if target_claims:
            target_uuids = [uuid.UUID(t) for t in target_claims]
            claims = [c for c in claims if c.id in target_uuids]

        rels_q = await self.db.execute(
            select(ClaimRelation).where(
                ClaimRelation.relation == "depends_on",
                (ClaimRelation.source_claim_id.in_(claim_ids)) |
                (ClaimRelation.target_claim_id.in_(claim_ids)),
            )
        )
        relations = rels_q.scalars().all()

        downstream_map = {}
        for r in relations:
            downstream_map.setdefault(r.target_claim_id, []).append(r.source_claim_id)

        from app.services.evidence_sufficiency_service import EvidenceSufficiencyService
        sufficiency_svc = EvidenceSufficiencyService(self.db)

        candidates = []
        for claim in claims:
            claim_candidates = await self._generate_candidates(
                claim, claim_map, downstream_map, sufficiency_svc, objective
            )
            candidates.extend(claim_candidates)

        for c in candidates:
            c.utility = self._score_utility(c, objective, budget_papers)

        candidates.sort(key=lambda c: c.utility, reverse=True)
        top = candidates[:max_actions]

        actions = []
        for i, c in enumerate(top):
            actions.append({
                "rank": i + 1,
                "action_type": c.action_type,
                "action_description": ACTION_TYPES[c.action_type]["description"],
                "target_claim_id": c.target_claim_id,
                "target_claim_text": c.target_claim_text,
                "utility_score": round(c.utility, 3),
                "expected_confidence_lift": round(c.expected_confidence_lift, 3),
                "downstream_claims_affected": c.downstream_impact,
                "reason": c.reason,
                "search_queries": c.search_queries,
                "mcp_calls": c.mcp_calls,
                "stopping_condition": c.stopping_condition,
            })

        total_expected_lift = sum(a["expected_confidence_lift"] for a in actions)

        return {
            "dossier_id": dossier_id,
            "objective": objective,
            "objective_description": OBJECTIVES[objective],
            "actions": actions,
            "total_actions_considered": len(candidates),
            "total_expected_confidence_lift": round(total_expected_lift, 3),
            "budget_papers": budget_papers,
            "estimated_papers_needed": sum(
                2 if a["action_type"] in ("contradiction_resolve", "upstream_strengthen", "paper_qa") else 1
                for a in actions
            ),
        }

    async def _generate_candidates(
        self,
        claim: GlobalClaim,
        claim_map: dict,
        downstream_map: dict,
        sufficiency_svc,
        objective: str,
    ) -> list[CandidateAction]:
        candidates = []
        cid = claim.id
        strength = claim.evidence_strength_score or 0
        effective = claim.effective_confidence or 0
        support = claim.support_count or 0
        contradict = claim.contradict_count or 0
        downstream_count = len(downstream_map.get(cid, []))
        breakdown = claim.strength_breakdown or {}
        text = claim.canonical_text[:80]

        if strength < 50 and support <= 1:
            lift = min(0.25, (50 - strength) / 100 * 0.5)
            candidates.append(CandidateAction(
                action_type="replication_hunt",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=downstream_count,
                reason=f"Single source (support={support}), needs independent confirmation",
                search_queries=[
                    f"replication {text}",
                    f"independent study {text}",
                ],
                mcp_calls=[
                    {"tool": "smart_search", "args": {"query": f"replication {text}", "dossier_id": "..."}},
                ],
                stopping_condition="Found 2+ independent sources confirming the claim",
            ))

        if claim.status == "disputed" and contradict > 0:
            lift = 0.3 + min(0.2, contradict * 0.1)
            candidates.append(CandidateAction(
                action_type="contradiction_resolve",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=downstream_count,
                reason=f"{contradict} contradiction(s) unresolved — high epistemic value in resolution",
                search_queries=[
                    f"meta-analysis {text}",
                    f"systematic review {text} conflicting",
                ],
                mcp_calls=[
                    {"tool": "smart_search", "args": {"query": f"meta-analysis {text}"}},
                    {"tool": "claim_conflict_scan", "args": {"claim_id": str(cid)}},
                ],
                stopping_condition="Found meta-analysis or direct comparison resolving the contradiction",
            ))

        methodology = breakdown.get("methodology", {})
        method_type = methodology.get("type", "unknown")
        if method_type in ("unknown", "anecdotal", "theoretical") and strength < 60:
            lift = min(0.2, (60 - strength) / 100 * 0.4)
            candidates.append(CandidateAction(
                action_type="smart_search",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=downstream_count,
                reason=f"Weak methodology ({method_type}) — need empirical evidence",
                search_queries=[
                    f"randomized controlled trial {text}",
                    f"experimental study {text}",
                    f"empirical evidence {text}",
                ],
                mcp_calls=[
                    {"tool": "smart_search", "args": {"query": f"RCT OR experimental {text}"}},
                ],
                stopping_condition="Found study with methodology score >= experimental",
            ))

        if downstream_count >= 2 and effective < 0.5:
            lift = 0.15 * downstream_count
            candidates.append(CandidateAction(
                action_type="upstream_strengthen",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=min(0.4, lift),
                downstream_impact=downstream_count,
                reason=f"Weak foundation (eff_conf={effective:.2f}) with {downstream_count} downstream claims at risk",
                search_queries=[
                    f"evidence {text}",
                    f"systematic review {text}",
                ],
                mcp_calls=[
                    {"tool": "evidence_sufficiency_audit", "args": {"claim_id": str(cid)}},
                    {"tool": "smart_search", "args": {"query": f"systematic review {text}"}},
                ],
                stopping_condition=f"Effective confidence >= 0.7 for this claim",
            ))

        recency = breakdown.get("recency", {})
        latest_year = recency.get("latest_year")
        if latest_year and latest_year < 2023 and downstream_count > 0:
            lift = 0.1
            candidates.append(CandidateAction(
                action_type="recency_update",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=downstream_count,
                reason=f"Latest evidence from {latest_year} — may be outdated",
                search_queries=[
                    f"{text} 2024 2025",
                    f"recent study {text}",
                ],
                mcp_calls=[
                    {"tool": "smart_search", "args": {"query": f"{text} 2024 2025"}},
                ],
                stopping_condition="Found 2023+ study confirming or updating the claim",
            ))

        if objective == "stress_test" and strength > 30:
            lift = 0.15
            candidates.append(CandidateAction(
                action_type="smart_search",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=downstream_count,
                reason="Stress-test: actively seeking disconfirming evidence",
                search_queries=[
                    f"critique {text}",
                    f"limitations {text}",
                    f"fails to replicate {text}",
                ],
                mcp_calls=[
                    {"tool": "smart_search", "args": {"query": f"critique OR limitation {text}"}},
                ],
                stopping_condition="Found credible challenge or confirmed robustness",
            ))

        if objective == "broaden_coverage" and support <= 2 and downstream_count == 0:
            lift = 0.08
            candidates.append(CandidateAction(
                action_type="topic_monitor",
                target_claim_id=str(cid),
                target_claim_text=text,
                expected_confidence_lift=lift,
                downstream_impact=0,
                reason="Low coverage leaf — set up passive monitoring for new evidence",
                search_queries=[],
                mcp_calls=[
                    {"tool": "topic_monitor_create", "args": {"dossier_id": "...", "topic": text}},
                ],
                stopping_condition="Monitor active; will alert on new relevant papers",
            ))

        return candidates

    def _score_utility(self, candidate: CandidateAction, objective: str, budget: int) -> float:
        action_meta = ACTION_TYPES[candidate.action_type]
        base_yield = action_meta["base_yield"]
        cost = action_meta["base_cost"]

        confidence_lift = candidate.expected_confidence_lift
        downstream_multiplier = 1.0 + min(1.0, candidate.downstream_impact * 0.15)

        objective_bonus = OBJECTIVE_BONUSES.get(objective, {}).get(candidate.action_type, 0.0)

        utility = (
            base_yield
            * confidence_lift
            * downstream_multiplier
            * (1.0 + objective_bonus)
            / cost
        )

        if candidate.downstream_impact >= 3:
            utility *= 1.3

        if "disputed" in candidate.reason.lower() or "contradiction" in candidate.reason.lower():
            utility *= 1.2

        return utility

    async def replan(
        self,
        dossier_id: str,
        *,
        objective: str = "maximize_certainty",
        completed_actions: list[dict] | None = None,
        max_actions: int = 5,
    ) -> dict:
        """Replan after actions have been taken. Accounts for what was already done."""
        result = await self.plan_next_actions(
            dossier_id, objective=objective, max_actions=max_actions + 3
        )

        if completed_actions and result.get("actions"):
            completed_claims = {a.get("target_claim_id") for a in completed_actions}
            completed_types = {
                (a.get("target_claim_id"), a.get("action_type"))
                for a in completed_actions
            }

            filtered = []
            for action in result["actions"]:
                key = (action["target_claim_id"], action["action_type"])
                if key not in completed_types:
                    filtered.append(action)

            result["actions"] = filtered[:max_actions]
            for i, a in enumerate(result["actions"]):
                a["rank"] = i + 1

            result["completed_actions_count"] = len(completed_actions)
            result["message"] = (
                f"Replanned after {len(completed_actions)} completed actions. "
                f"Showing next {len(result['actions'])} highest-utility actions."
            )

        return result
