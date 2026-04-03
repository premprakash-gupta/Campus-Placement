from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple


@dataclass(frozen=True)
class SkillMatchResult:
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float


def compute_skill_match(resume_skills: Iterable[str], jd_skills: Iterable[str]) -> SkillMatchResult:
    resume_set: Set[str] = {str(s).strip() for s in resume_skills if str(s).strip()}
    jd_set: Set[str] = {str(s).strip() for s in jd_skills if str(s).strip()}

    matched = sorted(resume_set.intersection(jd_set))
    missing = sorted(jd_set.difference(resume_set))
    denom = max(1, len(jd_set))
    score = (len(matched) / denom) * 100.0

    return SkillMatchResult(
        matched_skills=matched,
        missing_skills=missing,
        match_score=score,
    )

