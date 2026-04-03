from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Report:
    resume_pdf_path: str
    jd_text_source: str
    jd_skills: List[str]
    resume_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float
    salary_values_lpa: List[float]

    trends: Dict[str, dict]
    news_highlights: List[str]

    charts: Dict[str, str]

    # Heuristic ATS-style composite (JD + keywords + optional market + length); see matching/ats_score.py
    ats: Dict[str, Any]

    # From data/aggregates/market_<slug>.json when --market-title is set (CLI) or Streamlit passes it
    market_benchmark: Optional[Dict[str, Any]] = None

