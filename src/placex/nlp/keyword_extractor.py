import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .preprocess import clean_text, get_stopwords, tokenize


@dataclass(frozen=True)
class SkillPattern:
    name: str
    patterns: Tuple[str, ...]


def _normalize_skill_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).title()


def load_skills_lexicon(raw_lexicon: Sequence[dict]) -> List[SkillPattern]:
    skills: List[SkillPattern] = []
    for entry in raw_lexicon:
        name = _normalize_skill_name(str(entry["name"]))
        patterns = tuple(str(p).lower() for p in entry.get("patterns", []) if str(p).strip())
        skills.append(SkillPattern(name=name, patterns=patterns))
    return skills


def extract_skill_keywords(text: str, skills_lexicon: Sequence[SkillPattern], top_n: int = 20) -> List[str]:
    """
    Demo-friendly skill extraction:
    - Primary: count skill-pattern phrase hits from a predefined lexicon.
    - Secondary: add top frequent tokens (excluding stopwords) to fill gaps.
    """
    if not text or not text.strip():
        return []

    raw = clean_text(text)
    stopwords = get_stopwords()
    tokens = tokenize(raw)

    # 1) Lexicon hits
    scores: Dict[str, int] = {}
    for skill in skills_lexicon:
        hit_count = 0
        for pat in skill.patterns:
            if not pat:
                continue
            # Phrase match: treat pattern as substring
            hit_count += raw.count(pat.lower())
        if hit_count > 0:
            scores[skill.name] = hit_count

    # 2) Token frequency (fallback)
    token_counts: Dict[str, int] = {}
    for t in tokens:
        if t in stopwords:
            continue
        token_counts[t] = token_counts.get(t, 0) + 1

    # Combine: lexicon first, then tokens
    ranked_skills = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    result: List[str] = [name for name, _ in ranked_skills]

    # Add token candidates as "skills" only if we still have room
    if len(result) < top_n:
        ranked_tokens = sorted(token_counts.items(), key=lambda x: (-x[1], x[0]))
        for tok, _ in ranked_tokens:
            # Skip very generic tokens
            if tok in stopwords or len(tok) < 3:
                continue
            candidate = tok.upper() if tok.isalpha() and tok.isupper() else tok
            if candidate not in result:
                result.append(candidate)
            if len(result) >= top_n:
                break

    return result[:top_n]


def extract_jd_keywords(text: str, skills_lexicon: Sequence[SkillPattern], top_n: int = 20) -> List[str]:
    # Same extraction method for JD, but kept as a separate function for clarity.
    return extract_skill_keywords(text, skills_lexicon, top_n=top_n)

