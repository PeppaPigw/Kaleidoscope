"""Cross-paper reasoning API — synthesis, timelines, essential papers.

P3 WS-2: §20 (#165-176)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter(prefix="/cross-paper", tags=["cross-paper"])


def _raise_cross_paper_error(result: dict) -> None:
    error = result.get("error")
    if not error:
        return
    detail = str(error)
    if "not found" in detail.lower() or detail.lower() == "no papers found":
        raise HTTPException(status_code=404, detail=detail)
    raise HTTPException(
        status_code=502,
        detail=f"Cross-paper service error: {detail[:200]}",
    )


class SynthesisRequest(BaseModel):
    paper_ids: list[str]
    topic: str = "this research area"


class EssentialPapersRequest(BaseModel):
    paper_ids: list[str]
    top_k: int = 10


class BridgePapersRequest(BaseModel):
    paper_ids: list[str]


class TimelineRequest(BaseModel):
    paper_ids: list[str]


@router.post("/synthesize")
async def synthesize(
    req: SynthesisRequest,
    db: AsyncSession = Depends(get_db),
):
    """Synthesize knowledge across multiple papers."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    try:
        result = await svc.synthesize(req.paper_ids, req.topic)
        _raise_cross_paper_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cross-paper service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/timeline")
async def build_timeline(
    req: TimelineRequest,
    db: AsyncSession = Depends(get_db),
):
    """Build a research evolution timeline from papers."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    try:
        result = await svc.build_timeline(req.paper_ids)
        _raise_cross_paper_error(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Cross-paper service error: {str(e)[:200]}",
        ) from e
    finally:
        await svc.close()


@router.post("/essential-papers")
async def essential_papers(
    req: EssentialPapersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Find the minimal essential reading set using citation importance."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    return {"papers": await svc.find_essential_papers(req.paper_ids, req.top_k)}


@router.post("/bridge-papers")
async def bridge_papers(
    req: BridgePapersRequest,
    db: AsyncSession = Depends(get_db),
):
    """Detect bridge papers connecting research communities."""
    from app.services.analysis.cross_paper_service import CrossPaperService

    svc = CrossPaperService(db)
    return {"papers": await svc.find_bridge_papers(req.paper_ids)}


@router.get("/contradictions")
async def find_contradictions(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Find potentially contradicting claim pairs across papers."""
    from sqlalchemy import select

    from app.models.claim import Claim

    stmt = select(Claim).limit(limit * 4)
    result = await db.execute(stmt)
    claims = result.scalars().all()

    negation_terms = {
        "not",
        "no",
        "never",
        "fails",
        "worse",
        "lower",
        "decreases",
        "reduces",
    }
    positive_terms = {
        "improves",
        "better",
        "higher",
        "increases",
        "achieves",
        "outperforms",
    }

    contradictions: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for index, claim_a in enumerate(claims):
        for claim_b in claims[index + 1 :]:
            if claim_a.paper_id == claim_b.paper_id:
                continue
            text_a = (claim_a.text or "").lower()
            text_b = (claim_b.text or "").lower()
            has_neg_a = any(term in text_a for term in negation_terms)
            has_pos_a = any(term in text_a for term in positive_terms)
            has_neg_b = any(term in text_b for term in negation_terms)
            has_pos_b = any(term in text_b for term in positive_terms)
            pair_key = tuple(sorted((str(claim_a.id), str(claim_b.id))))
            if not ((has_pos_a and has_neg_b) or (has_neg_a and has_pos_b)):
                continue
            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)
            contradictions.append(
                {
                    "id": f"contra-{len(contradictions) + 1}",
                    "claimA": {
                        "id": str(claim_a.id),
                        "text": claim_a.text or "",
                        "paper_id": str(claim_a.paper_id),
                    },
                    "claimB": {
                        "id": str(claim_b.id),
                        "text": claim_b.text or "",
                        "paper_id": str(claim_b.paper_id),
                    },
                    "severity": "high" if (has_neg_a or has_neg_b) else "medium",
                    "resolved": False,
                }
            )
            if len(contradictions) >= limit:
                break
        if len(contradictions) >= limit:
            break

    return {"contradictions": contradictions, "total": len(contradictions)}
