"""Text similarity and normalization utilities."""

import re
import unicodedata

from rapidfuzz import fuzz


def normalize_title(title: str) -> str:
    """
    Normalize a paper title for comparison.

    Steps:
    1. Unicode normalize (NFKD)
    2. Lowercase
    3. Remove punctuation except hyphens
    4. Collapse whitespace
    """
    if not title:
        return ""

    # Unicode normalize
    title = unicodedata.normalize("NFKD", title)
    # Lowercase
    title = title.lower()
    # Remove non-alphanumeric except hyphens and spaces
    title = re.sub(r"[^\w\s-]", "", title)
    # Collapse whitespace
    title = re.sub(r"\s+", " ", title).strip()

    return title


def titles_are_similar(title_a: str, title_b: str, threshold: float = 0.90) -> bool:
    """
    Check if two paper titles are similar enough to be duplicates.

    Uses token-sort ratio from rapidfuzz for order-insensitive comparison.
    Default threshold is 0.90 (90% similarity).
    """
    norm_a = normalize_title(title_a)
    norm_b = normalize_title(title_b)

    if not norm_a or not norm_b:
        return False

    # Exact match after normalization
    if norm_a == norm_b:
        return True

    # Fuzzy match using token sort ratio (handles word reordering)
    score = fuzz.token_sort_ratio(norm_a, norm_b) / 100.0
    return score >= threshold


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, adding ellipsis if truncated."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[: max_length - 3] + "..."
