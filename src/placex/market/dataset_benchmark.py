"""
Load precomputed market aggregates (JSON under data/aggregates) and compare
resume skills to top market skills for a job title slice.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_aggregates_dir() -> Path:
    return _repo_root() / "data" / "aggregates"


def slugify_title(title: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", title, flags=re.UNICODE)
    s = re.sub(r"[\s\-]+", "_", s.strip()).lower()
    return (s[:100] if s else "unknown")


def market_aggregate_path_for_title(title: str) -> Path:
    return get_aggregates_dir() / f"market_{slugify_title(title)}.json"


def load_market_aggregate(title: str) -> Optional[Dict[str, Any]]:
    """Load JSON built by scripts/build_linkedin_aggregates.py for this title."""
    p = market_aggregate_path_for_title(title)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _norm_skill(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _resume_covers_market_skill(resume_set: set[str], market_name_norm: str) -> bool:
    if not market_name_norm:
        return False
    if market_name_norm in resume_set:
        return True
    for r in resume_set:
        if len(r) < 2:
            continue
        if r in market_name_norm or market_name_norm in r:
            return True
    return False


def compare_resume_to_market(
    resume_skills: List[str],
    market_aggregate: Dict[str, Any],
    *,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compare extracted resume skills to the aggregate's top_skills list.

    Matching is case-insensitive; allows light substring overlap between resume
    tokens and dataset skill names.
    """
    top = market_aggregate.get("top_skills") or []
    if top_k is not None:
        top = top[:top_k]

    resume_set = {_norm_skill(s) for s in resume_skills if str(s).strip()}

    matched: List[str] = []
    for row in top:
        display = row.get("skill_name") or row.get("skill_abr") or ""
        nm = _norm_skill(display)
        if _resume_covers_market_skill(resume_set, nm):
            matched.append(str(display))

    denom = max(1, len(top))
    alignment_pct = (len(matched) / denom) * 100.0

    return {
        "market_title_filter": market_aggregate.get("title_filter"),
        "job_postings_matched": market_aggregate.get("job_postings_matched"),
        "matched_market_skills": matched,
        "market_alignment_pct": round(alignment_pct, 2),
        "top_market_skill_names": [row.get("skill_name") for row in top],
        "salary_summary": market_aggregate.get("salary"),
    }


def market_top_skill_gaps(
    resume_skills: List[str],
    market_aggregate: Dict[str, Any],
    *,
    top_n: int = 15,
) -> List[str]:
    """
    Among the top-N demand skills in the aggregate, names the resume does not
    cover (same matching rules as compare_resume_to_market).
    """
    top = (market_aggregate.get("top_skills") or [])[:top_n]
    resume_set = {_norm_skill(s) for s in resume_skills if str(s).strip()}
    gaps: List[str] = []
    for row in top:
        display = row.get("skill_name") or row.get("skill_abr") or ""
        nm = _norm_skill(display)
        if not nm:
            continue
        if not _resume_covers_market_skill(resume_set, nm):
            gaps.append(str(display))
    return gaps
