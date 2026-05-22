"""Kaleidoscope SDK — async Python client for the Kaleidoscope agent API.

Usage::

    from kaleidoscope_sdk import KaleidoscopeClient

    async with KaleidoscopeClient() as ks:
        results = await ks.search("transformer attention mechanisms")
        paper = await ks.get_paper(results.results[0]["id"])
        answer = await ks.ask_paper(paper.id, "What is the main contribution?")
        print(answer.answer)
"""

from .client import (
    KaleidoscopeAuthError,
    KaleidoscopeClient,
    KaleidoscopeError,
    KaleidoscopeNotFoundError,
)
from .types import (
    AnswerResult,
    ClaimResult,
    EvidenceResult,
    ImportResult,
    Paper,
    PaperList,
    ResolveResult,
    SearchResult,
)

__all__ = [
    "KaleidoscopeClient",
    "KaleidoscopeError",
    "KaleidoscopeAuthError",
    "KaleidoscopeNotFoundError",
    "Paper",
    "SearchResult",
    "ImportResult",
    "PaperList",
    "AnswerResult",
    "EvidenceResult",
    "ClaimResult",
    "ResolveResult",
]

__version__ = "0.1.0"
