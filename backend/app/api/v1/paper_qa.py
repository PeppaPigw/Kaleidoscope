"""Paper QA API — embedding status, prepare, and Q&A endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services.extraction.paper_qa_service import PaperQAService

router = APIRouter(prefix="/paper-qa", tags=["paper-qa"])


class ConversationTurn(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=12000)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: list[ConversationTurn] = Field(default_factory=list, max_length=6)
    context_snippet: str | None = Field(default=None, max_length=2000)


@router.get("/{paper_id}/status")
async def get_embedding_status(paper_id: str, db: AsyncSession = Depends(get_db)):
    """Get the embedding pipeline status for a paper."""
    svc = PaperQAService(db)
    return await svc.get_status(paper_id)


@router.post("/{paper_id}/prepare")
async def prepare_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger (or reprioritize) the embedding pipeline for a paper."""
    svc = PaperQAService(db)
    return await svc.prepare(paper_id)


@router.post("/{paper_id}/ask")
async def ask_paper(
    paper_id: str,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Answer a question about a paper using RAG (embed → recall → rerank → LLM)."""
    svc = PaperQAService(db)
    status_info = await svc.get_status(paper_id)
    if status_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMBEDDING_NOT_READY",
                "message": "Paper embedding not ready. Call /prepare first.",
                "status": status_info["status"],
            },
        )
    return await svc.ask(
        paper_id,
        body.question,
        history=[turn.model_dump() for turn in body.history],
        context_snippet=body.context_snippet,
    )


@router.post("/{paper_id}/ask/stream")
async def ask_paper_stream(
    paper_id: str,
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream-answer a question about a paper using SSE (embed → recall → rerank → stream LLM)."""
    svc = PaperQAService(db)
    status_info = await svc.get_status(paper_id)
    if status_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMBEDDING_NOT_READY",
                "message": "Paper embedding not ready. Call /prepare first.",
                "status": status_info["status"],
            },
        )
    return StreamingResponse(
        svc.ask_stream(
            paper_id,
            body.question,
            history=[turn.model_dump() for turn in body.history],
            context_snippet=body.context_snippet,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
