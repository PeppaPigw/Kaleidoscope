"""Translation API route — proxies requests to NVIDIA translate service.

Keeps the API key server-side. The frontend calls /api/v1/translate
instead of hitting NVIDIA directly.

Supports optional persistence to paper.title_zh / paper.abstract_zh.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.translate_client import TranslateClient
from app.dependencies import get_db
from app.models.paper import Paper

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["translate"])

_SYS_EN2ZH = (
    "你是一个论文翻译助手，使用最简洁准确的语言翻译下面的内容。不允许任何其他额外输出"
)
_SYS_ZH2EN = (
    "You are a translation assistant. Translate Chinese text to English using "
    "professional, concise terminology. Output only the translation, no extras."
)


class TranslateRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=10000, description="Text to translate"
    )
    direction: str = Field(
        default="en2zh",
        pattern="^(en2zh|zh2en|auto)$",
        description="Translation direction",
    )
    paper_id: str | None = Field(
        default=None, description="Optional paper ID to persist translation"
    )
    field_type: str | None = Field(
        default=None,
        pattern="^(title|abstract)$",
        description="Field type: title or abstract",
    )


class TranslateResponse(BaseModel):
    translated: str
    original: str


@router.post("/translate", response_model=TranslateResponse, summary="Translate text")
async def translate_text(
    body: TranslateRequest, db: AsyncSession = Depends(get_db)
) -> TranslateResponse:
    """Translate text via the NVIDIA LLM translation API.

    - **en2zh** (default): English → Chinese
    - **zh2en**: Chinese → English
    - **auto**: same as en2zh

    If paper_id and field_type are provided, the translation will be persisted
    to the database (paper.title_zh or paper.abstract_zh).
    """
    stripped = body.text.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="text cannot be blank")

    # Check if translation already exists in database
    if body.paper_id and body.field_type and body.direction == "en2zh":
        stmt = select(Paper).where(Paper.id == body.paper_id)
        result = await db.execute(stmt)
        paper = result.scalar_one_or_none()

        if paper:
            # Return cached translation if exists
            if body.field_type == "title" and paper.title_zh:
                logger.info(
                    "translation.cache_hit",
                    paper_id=body.paper_id,
                    field_type=body.field_type,
                )
                return TranslateResponse(translated=paper.title_zh, original=body.text)
            elif body.field_type == "abstract" and paper.abstract_zh:
                logger.info(
                    "translation.cache_hit",
                    paper_id=body.paper_id,
                    field_type=body.field_type,
                )
                return TranslateResponse(
                    translated=paper.abstract_zh, original=body.text
                )

    system_prompt = _SYS_ZH2EN if body.direction == "zh2en" else _SYS_EN2ZH

    logger.info(
        "translation.start",
        direction=body.direction,
        text_length=len(stripped),
        paper_id=body.paper_id,
        field_type=body.field_type,
    )

    try:
        async with TranslateClient(system_prompt=system_prompt) as client:
            result = await client.translate(stripped, system_prompt=system_prompt)
    except ValueError as e:
        logger.error("translation.config_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Translation service not configured: {e}",
        ) from e
    except Exception as e:
        logger.error("translation.api_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Translation service error: {e}",
        ) from e

    if not result:
        logger.warning("translation.empty_result")
        raise HTTPException(
            status_code=503,
            detail="Translation service returned an empty result",
        )

    # Persist translation to database if paper_id provided
    if body.paper_id and body.field_type and body.direction == "en2zh":
        stmt = select(Paper).where(Paper.id == body.paper_id)
        db_result = await db.execute(stmt)
        paper = db_result.scalar_one_or_none()

        if paper:
            if body.field_type == "title":
                paper.title_zh = result
            elif body.field_type == "abstract":
                paper.abstract_zh = result
            await db.commit()
            logger.info(
                "translation.persisted",
                paper_id=body.paper_id,
                field_type=body.field_type,
            )

    logger.info("translation.complete", direction=body.direction)
    return TranslateResponse(translated=result, original=body.text)
