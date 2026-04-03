"""
Heuristic ATS-style score (0–100) for demos. Not a commercial ATS product.

Combines JD skill match, optional market alignment, JD keyword overlap, and resume length.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def compute_ats_score(
    *,
    jd_match_pct: float,
    market_alignment_pct: Optional[float] = None,
    resume_text_len: int = 0,
    jd_keyword_hit_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Composite ATS-style score plus explainable components.

    jd_match_pct
        Lexicon skill match vs JD (0-100).
    market_alignment_pct
        Optional overlap with top market skills from aggregates (0-100).
    resume_text_len
        Characters of extracted resume text.
    jd_keyword_hit_pct
        Optional 0-100 from ``simple_jd_keyword_hits`` (JD words found in resume).
    """
    jd = max(0.0, min(100.0, float(jd_match_pct)))

    if market_alignment_pct is not None:
        m = max(0.0, min(100.0, float(market_alignment_pct)))
        core = 0.62 * jd + 0.38 * m
        formula = "Core = 62% JD skills + 38% market skills"
    else:
        core = jd
        formula = "Core = JD skill match only (no market aggregate)"

    keyword_points = 0.0
    if jd_keyword_hit_pct is not None:
        k = max(0.0, min(100.0, float(jd_keyword_hit_pct)))
        # Up to +10 pts for literal JD vocabulary appearing in resume (ATS keyword scan proxy)
        keyword_points = 0.10 * k
        formula += f"; + up to 10 pts JD keyword overlap ({k:.0f}% hits)"

    length_bonus = 0.0
    length_note = ""
    if resume_text_len <= 0:
        length_note = "No text length recorded."
    elif resume_text_len < 300:
        length_note = "Resume text is short; add measurable outcomes and role keywords."
    elif resume_text_len <= 12000:
        length_bonus = 2.0
        length_note = "+2 when length is in a typical readable range."
    else:
        length_note = "Long resume; lead with strongest role keywords."

    score = min(100.0, core + keyword_points + length_bonus)

    return {
        "ats_score": round(score, 2),
        "grade": _grade(score),
        "components": {
            "core_score": round(min(100.0, core), 2),
            "jd_match_pct": round(jd, 2),
            "market_alignment_pct": round(market_alignment_pct, 2) if market_alignment_pct is not None else None,
            "keyword_overlap_points": round(keyword_points, 2),
            "jd_keyword_hit_pct": round(jd_keyword_hit_pct, 2) if jd_keyword_hit_pct is not None else None,
            "resume_text_chars": int(resume_text_len),
            "length_bonus": length_bonus,
        },
        "formula": formula,
        "length_note": length_note,
        "disclaimer": "Educational heuristic only — not a vendor ATS score.",
    }


def _grade(score: float) -> str:
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Competitive"
    if score >= 55:
        return "Moderate"
    return "Needs work"


def simple_jd_keyword_hits(resume_text: str, jd_text: str, *, max_terms: int = 40) -> float:
    """
    Crude proxy: % of JD content tokens (len>=3) that appear in resume (0-100).
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0

    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    stop = {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "was",
        "our",
        "out",
        "day",
        "get",
        "has",
        "how",
        "its",
        "may",
        "new",
        "now",
        "old",
        "see",
        "two",
        "who",
        "way",
        "use",
        "any",
        "with",
        "from",
        "that",
        "this",
        "will",
        "your",
        "have",
        "been",
        "work",
        "job",
        "role",
    }
    words = re.findall(r"[a-z0-9#+.]{3,}", jd_lower)
    terms: list[str] = []
    for w in words:
        if w in stop or w.isdigit():
            continue
        terms.append(w)
        if len(terms) >= max_terms:
            break
    if not terms:
        return 0.0
    hits = sum(1 for t in terms if t in resume_lower)
    return 100.0 * hits / len(terms)
