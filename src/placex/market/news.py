from __future__ import annotations

from typing import Dict, List


def fetch_news_insights(keywords: List[str]) -> Dict[str, List[str]]:
    """
    Placeholder for a future news integration.

    For hackathon MVP, we return a lightweight structure so the report schema
    stays stable even when external APIs are not configured.
    """
    if not keywords:
        return {"highlights": []}
    # Simple heuristic summary (no external calls).
    highlights = [f"Interest for '{kw}' is worth validating with recent job postings." for kw in keywords[:3]]
    return {"highlights": highlights}

