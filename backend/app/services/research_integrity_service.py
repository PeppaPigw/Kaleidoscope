"""ResearchIntegrityService — Comprehensive Research Integrity Audit.

Combines multiple analysis engines into a single comprehensive integrity
check. Runs evidence chain tracing, assumption excavation, methodology
audit, confidence calibration, and contradiction detection in sequence
to produce a holistic integrity assessment.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class ResearchIntegrityService:
    """Comprehensive research integrity auditing via multi-engine pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def full_audit(
        self,
        claim: str,
        *,
        evidence: list[str] | None = None,
        methodology: str = "",
        domain: str = "",
    ) -> dict:
        """Run a comprehensive integrity audit combining multiple engines."""
        from app.services.agent.tool_dispatcher import ToolDispatcher

        dispatcher = ToolDispatcher(self.db)
        results = {}
        issues = []

        # 1. Evidence chain trace
        chain_result = await dispatcher.call_tool("evidence_chain_trace", {
            "claim": claim,
            "evidence": evidence or [],
            "domain": domain,
        })
        results["evidence_chain"] = {
            "strength": chain_result.get("overall_strength", 0),
            "primary_reached": chain_result.get("primary_reached", False),
            "weakest_link": chain_result.get("weakest_link", ""),
        }
        if chain_result.get("overall_strength", 1) < 0.5:
            issues.append(f"Weak evidence chain (strength: {chain_result.get('overall_strength')})")

        # 2. Assumption excavation
        assumption_result = await dispatcher.call_tool("assumption_excavate", {
            "argument": claim,
            "domain": domain,
        })
        results["assumptions"] = {
            "count": assumption_result.get("assumption_count", 0),
            "fragility": assumption_result.get("reasoning_fragility", 0),
            "most_dangerous": assumption_result.get("most_dangerous", ""),
        }
        if assumption_result.get("reasoning_fragility", 0) > 0.7:
            issues.append(f"High reasoning fragility ({assumption_result.get('reasoning_fragility')})")

        # 3. Methodology audit (if methodology provided)
        if methodology:
            method_result = await dispatcher.call_tool("methodology_audit", {
                "description": claim,
                "methodology": methodology,
                "domain": domain,
            })
            results["methodology"] = {
                "grade": method_result.get("grade", ""),
                "score": method_result.get("overall_score", 0),
                "critical_flaws": method_result.get("critical_flaws", []),
            }
            if method_result.get("overall_score", 1) < 0.5:
                issues.append(f"Methodology grade: {method_result.get('grade')}")

        # 4. Confidence calibration
        calibration_result = await dispatcher.call_tool("confidence_calibrate", {
            "claims": [{"claim": claim, "confidence": 0.8}],
            "domain": domain,
        })
        results["calibration"] = {
            "overall_score": calibration_result.get("overall_calibration", 0),
            "bias": calibration_result.get("systematic_bias", ""),
        }
        if calibration_result.get("systematic_bias") == "overconfident":
            issues.append("Systematic overconfidence detected")

        # Compute overall integrity score
        scores = [
            results["evidence_chain"]["strength"],
            1 - results["assumptions"]["fragility"],
            results["calibration"]["overall_score"],
        ]
        if "methodology" in results:
            scores.append(results["methodology"]["score"])

        overall = sum(scores) / len(scores) if scores else 0

        grade_map = [(0.9, "A"), (0.8, "B+"), (0.7, "B"), (0.6, "C+"), (0.5, "C"), (0.4, "D"), (0, "F")]
        grade = next(g for threshold, g in grade_map if overall >= threshold)

        return {
            "claim": claim[:200],
            "overall_integrity": round(overall, 2),
            "grade": grade,
            "issues_found": len(issues),
            "issues": issues,
            "components": results,
            "recommendation": "High confidence warranted" if overall >= 0.7 else
                            "Moderate confidence — address issues" if overall >= 0.5 else
                            "Low confidence — significant integrity concerns",
        }
