"""EvidenceSufficiencyService — prescribes exactly what evidence is needed to strengthen a claim."""

import uuid

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_ledger import ClaimMention, ClaimRelation, GlobalClaim

logger = structlog.get_logger(__name__)

STRENGTH_TARGETS = {
    "critical_premise": {"strength": 80, "effective_confidence": 0.85},
    "important_premise": {"strength": 65, "effective_confidence": 0.70},
    "leaf_claim": {"strength": 50, "effective_confidence": 0.55},
}

METHODOLOGY_HIERARCHY = [
    "meta_analysis", "rct", "longitudinal", "experimental",
    "benchmark", "observational", "theoretical", "anecdotal", "unknown",
]


class EvidenceSufficiencyService:
    """Prescribes the minimum evidence needed to reach a target confidence."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def audit_claim(self, claim_id: str) -> dict:
        """Full sufficiency audit for a single claim."""
        result = await self.db.execute(
            select(GlobalClaim).where(GlobalClaim.id == uuid.UUID(claim_id))
        )
        claim = result.scalar_one_or_none()
        if not claim:
            return {"error": "Claim not found"}

        from app.services.claim_dependency_service import ClaimDependencyService
        dep_svc = ClaimDependencyService(self.db)
        fragility = await dep_svc.get_fragility_report(claim_id)

        downstream = await dep_svc.get_downstream_impacts(claim_id, depth=2)
        downstream_count = downstream["total"]

        criticality_class = self._classify_criticality(downstream_count, claim)
        target = STRENGTH_TARGETS[criticality_class]

        current = {
            "strength": claim.evidence_strength_score or 0,
            "effective_confidence": claim.effective_confidence or 0,
            "direct_confidence": claim.direct_confidence or 0,
            "support_count": claim.support_count or 0,
            "contradict_count": claim.contradict_count or 0,
            "status": claim.status,
            "fragility": fragility.get("fragility_score", 0),
            "criticality": fragility.get("criticality_score", 0),
        }

        strength_breakdown = claim.strength_breakdown or {}
        blockers = self._compute_blockers(claim, current, target, strength_breakdown, fragility)
        evidence_needed = self._prescribe_evidence(blockers, current, target)
        queries = self._generate_queries(claim, blockers)
        tool_calls = self._recommend_tools(blockers)

        meets_target = (
            current["strength"] >= target["strength"]
            and current["effective_confidence"] >= target["effective_confidence"]
        )

        return {
            "claim_id": claim_id,
            "claim_text": claim.canonical_text[:150],
            "meets_target": meets_target,
            "criticality_class": criticality_class,
            "current": current,
            "target": target,
            "strength_gap": max(0, target["strength"] - current["strength"]),
            "confidence_gap": round(max(0, target["effective_confidence"] - current["effective_confidence"]), 3),
            "blockers": blockers,
            "minimum_evidence_needed": evidence_needed,
            "recommended_queries": queries,
            "next_best_tool_calls": tool_calls,
        }

    def _classify_criticality(self, downstream_count: int, claim: GlobalClaim) -> str:
        if downstream_count >= 3:
            return "critical_premise"
        elif downstream_count >= 1:
            return "important_premise"
        return "leaf_claim"

    def _compute_blockers(
        self, claim: GlobalClaim, current: dict, target: dict,
        breakdown: dict, fragility: dict,
    ) -> list[dict]:
        blockers = []
        strength = current["strength"]
        target_strength = target["strength"]

        methodology = breakdown.get("methodology", {})
        method_type = methodology.get("type", "unknown")
        method_score = methodology.get("score", 0)
        if method_score < 15 and strength < target_strength:
            better_methods = METHODOLOGY_HIERARCHY[:METHODOLOGY_HIERARCHY.index(method_type)] if method_type in METHODOLOGY_HIERARCHY else METHODOLOGY_HIERARCHY[:4]
            lift = min(15, target_strength - strength)
            blockers.append({
                "type": "weak_methodology",
                "current_method": method_type,
                "estimated_lift": lift,
                "suggestion": f"Need evidence from: {', '.join(better_methods[:3])}",
            })

        sample = breakdown.get("sample_adequacy", {})
        sample_score = sample.get("score", 0)
        detected_n = sample.get("detected_n")
        if sample_score < 14 and strength < target_strength:
            lift = min(10, target_strength - strength)
            blockers.append({
                "type": "sample_too_small",
                "current_n": detected_n,
                "estimated_lift": lift,
                "suggestion": "Need study with n > 100 (ideally n > 1000)",
            })

        stats = breakdown.get("statistical_rigor", {})
        stats_score = stats.get("score", 0)
        if stats_score < 15 and strength < target_strength:
            lift = min(12, target_strength - strength)
            blockers.append({
                "type": "statistical_rigor_gap",
                "signals_found": stats.get("signals_found", 0),
                "estimated_lift": lift,
                "suggestion": "Need study reporting p-values, confidence intervals, or effect sizes",
            })

        replication = breakdown.get("replication", {})
        rep_score = replication.get("score", 0)
        if rep_score < 8 and (current["support_count"] or 0) <= 1:
            lift = min(10, target_strength - strength)
            blockers.append({
                "type": "missing_replication",
                "current_sources": current["support_count"],
                "estimated_lift": lift,
                "suggestion": "Need 2+ independent studies confirming this claim",
            })

        if current["contradict_count"] > 0 and claim.status == "disputed":
            lift = 8
            blockers.append({
                "type": "contradiction_unresolved",
                "contradict_count": current["contradict_count"],
                "estimated_lift": lift,
                "suggestion": "Need direct comparison study or meta-analysis resolving the contradiction",
            })

        weak_premises = fragility.get("weak_premises", [])
        if weak_premises:
            for wp in weak_premises[:2]:
                blockers.append({
                    "type": "weak_upstream_premise",
                    "claim_id": wp["claim_id"],
                    "claim_text": wp["text"][:80],
                    "upstream_strength": wp.get("evidence_strength"),
                    "estimated_cascade_lift": 0.15,
                    "suggestion": f"Strengthen upstream premise: '{wp['text'][:50]}...'",
                })

        recency = breakdown.get("recency", {})
        latest_year = recency.get("latest_year")
        if latest_year and latest_year < 2023:
            blockers.append({
                "type": "stale_evidence",
                "latest_year": latest_year,
                "estimated_lift": 5,
                "suggestion": "Need recent (2023+) study confirming this still holds",
            })

        blockers.sort(key=lambda b: b.get("estimated_lift", b.get("estimated_cascade_lift", 0)), reverse=True)
        return blockers

    def _prescribe_evidence(self, blockers: list, current: dict, target: dict) -> list[str]:
        prescriptions = []
        for b in blockers:
            bt = b["type"]
            if bt == "missing_replication":
                prescriptions.append("2 independent supporting studies from different research groups")
            elif bt == "weak_methodology":
                prescriptions.append(f"1 study using stronger methodology ({b.get('suggestion', '')})")
            elif bt == "sample_too_small":
                prescriptions.append("1 study with sample size > 1000 participants/instances")
            elif bt == "statistical_rigor_gap":
                prescriptions.append("1 study with full statistical reporting (p-values, CIs, effect sizes)")
            elif bt == "contradiction_unresolved":
                prescriptions.append("1 meta-analysis or direct comparison study resolving the contradiction")
            elif bt == "weak_upstream_premise":
                prescriptions.append(f"Strengthen premise: '{b.get('claim_text', '')[:50]}...'")
            elif bt == "stale_evidence":
                prescriptions.append(f"1 recent (2023+) study confirming the claim still holds")

        if not prescriptions:
            if current["strength"] < target["strength"]:
                prescriptions.append("Additional supporting evidence from any rigorous source")

        return prescriptions[:6]

    def _generate_queries(self, claim: GlobalClaim, blockers: list) -> list[str]:
        base_text = claim.canonical_text[:80]
        queries = []

        for b in blockers[:3]:
            bt = b["type"]
            if bt == "missing_replication":
                queries.append(f"replication {base_text}")
            elif bt == "weak_methodology":
                queries.append(f"randomized controlled {base_text}")
                queries.append(f"meta-analysis {base_text}")
            elif bt == "sample_too_small":
                queries.append(f"large-scale study {base_text}")
            elif bt == "statistical_rigor_gap":
                queries.append(f"statistical analysis {base_text}")
            elif bt == "contradiction_unresolved":
                queries.append(f"comparison {base_text} conflicting evidence")
            elif bt == "stale_evidence":
                queries.append(f"{base_text} 2024 2025")

        if not queries:
            queries.append(f"systematic review {base_text}")

        return queries[:5]

    def _recommend_tools(self, blockers: list) -> list[str]:
        tools = set()
        for b in blockers:
            bt = b["type"]
            if bt in ("missing_replication", "weak_methodology", "sample_too_small", "stale_evidence"):
                tools.add("smart_search")
                tools.add("topic_monitor_create")
            elif bt == "contradiction_unresolved":
                tools.add("claim_conflict_scan")
                tools.add("smart_search")
            elif bt == "weak_upstream_premise":
                tools.add("evidence_sufficiency_audit")
            elif bt == "statistical_rigor_gap":
                tools.add("smart_search")
                tools.add("claim_ledger_search")

        tools.add("claim_ledger_search")
        return sorted(tools)[:5]

    async def audit_dossier(self, dossier_id: str) -> dict:
        """Audit all claims in a dossier, returning those that don't meet their target."""
        mentions_q = await self.db.execute(
            select(ClaimMention.global_claim_id).where(
                ClaimMention.dossier_id == uuid.UUID(dossier_id)
            ).distinct()
        )
        claim_ids = [str(row[0]) for row in mentions_q.all()]

        if not claim_ids:
            return {"dossier_id": dossier_id, "audits": [], "total": 0, "insufficient_count": 0}

        audits = []
        insufficient = 0
        for cid in claim_ids:
            result = await self.audit_claim(cid)
            if "error" in result:
                continue
            if not result.get("meets_target", True):
                insufficient += 1
            audits.append({
                "claim_id": cid,
                "claim_text": result.get("claim_text", "")[:80],
                "meets_target": result.get("meets_target"),
                "criticality_class": result.get("criticality_class"),
                "strength_gap": result.get("strength_gap"),
                "confidence_gap": result.get("confidence_gap"),
                "top_blocker": result["blockers"][0]["type"] if result.get("blockers") else None,
            })

        audits.sort(key=lambda a: a.get("strength_gap", 0), reverse=True)

        return {
            "dossier_id": dossier_id,
            "total": len(audits),
            "insufficient_count": insufficient,
            "sufficient_count": len(audits) - insufficient,
            "audits": audits,
        }
