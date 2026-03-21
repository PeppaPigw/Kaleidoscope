"""Intelligence API — LLM-powered summaries, extraction, and QA."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.paper import Paper

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ─── Request/Response Schemas ─────────────────────────────────────

class SummarizeRequest(BaseModel):
    level: Literal["tweet", "abstract", "executive", "detailed"] = "abstract"


class QARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class CollectionQARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    paper_ids: list[str] = Field(..., min_length=1, max_length=10)


# ─── Endpoints ───────────────────────────────────────────────────

@router.post("/papers/{paper_id}/summarize")
async def summarize_paper(
    paper_id: str,
    body: SummarizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a multi-level summary of a paper.

    Levels:
    - **tweet**: 1-2 sentences (~50 words)
    - **abstract**: Structured 4-part summary (~300 words)
    - **executive**: For research leads (~800 words)
    - **detailed**: Comprehensive (~2000 words)
    """
    from app.services.extraction.summarizer import SummarizationService

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    svc = SummarizationService(db)
    try:
        summary = await svc.summarize(paper, level=body.level)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
    finally:
        await svc.close()


@router.post("/papers/{paper_id}/extract")
async def extract_structured(
    paper_id: str,
    extract_type: str = Query("highlights", description="highlights or methods"),
    db: AsyncSession = Depends(get_db),
):
    """
    Extract structured information from a paper.

    Types:
    - **highlights**: Key highlights, contributions, limitations, future work
    - **methods**: Methods, datasets, metrics, baselines, implementation details
    """
    from app.services.extraction.extractor import ExtractionService

    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.deleted_at.is_(None))
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    svc = ExtractionService(db)
    try:
        if extract_type == "highlights":
            extracted = await svc.extract_highlights(paper)
        elif extract_type == "methods":
            extracted = await svc.extract_methods(paper)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown type: {extract_type}")

        # Persist extracted data
        await db.commit()
        return {"paper_id": paper_id, "type": extract_type, "data": extracted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        await svc.close()


@router.post("/papers/{paper_id}/ask")
async def ask_paper(
    paper_id: str,
    body: QARequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question about a specific paper.

    Uses RAG: retrieves relevant passages from the paper,
    then generates an answer with source citations.
    """
    from app.services.extraction.qa_engine import PaperQAEngine

    svc = PaperQAEngine(db)
    try:
        result = await svc.ask(paper_id, body.question)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA failed: {str(e)}")
    finally:
        await svc.close()


@router.post("/ask")
async def ask_collection(
    body: CollectionQARequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question across multiple papers.

    Synthesizes information from up to 10 papers, comparing
    and contrasting findings with citations to each paper.
    """
    from app.services.extraction.qa_engine import PaperQAEngine

    svc = PaperQAEngine(db)
    try:
        result = await svc.ask_collection(body.paper_ids, body.question)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-doc QA failed: {str(e)}")
    finally:
        await svc.close()
