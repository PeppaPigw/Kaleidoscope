"""Translation API route — proxies requests to NVIDIA translate service.

Keeps the API key server-side. The frontend calls /api/v1/translate
instead of hitting NVIDIA directly.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.clients.translate_client import TranslateClient

router = APIRouter(tags=["translate"])

_SYS_EN2ZH = (
    "你是一个论文翻译助手，使用最简洁准确的语言翻译下面的内容。不允许任何其他额外输出"
)
_SYS_ZH2EN = (
    "You are a translation assistant. Translate Chinese text to English using "
    "professional, concise terminology. Output only the translation, no extras."
)


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    direction: str = Field(
        default="en2zh",
        pattern="^(en2zh|zh2en|auto)$",
        description="Translation direction",
    )


class TranslateResponse(BaseModel):
    translated: str
    original: str


@router.post("/translate", response_model=TranslateResponse, summary="Translate text")
async def translate_text(body: TranslateRequest) -> TranslateResponse:
    """Translate text via the NVIDIA LLM translation API.

    - **en2zh** (default): English → Chinese  
    - **zh2en**: Chinese → English  
    - **auto**: same as en2zh
    """
    stripped = body.text.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail="text cannot be blank")

    system_prompt = _SYS_ZH2EN if body.direction == "zh2en" else _SYS_EN2ZH

    try:
        async with TranslateClient(system_prompt=system_prompt) as client:
            result = await client.translate(stripped, system_prompt=system_prompt)
    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Translation service not configured: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Translation service error: {e}",
        ) from e

    if not result:
        raise HTTPException(
            status_code=503,
            detail="Translation service returned an empty result",
        )

    return TranslateResponse(translated=result, original=body.text)
