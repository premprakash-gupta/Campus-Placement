import re
from typing import List


_FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "then",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def _try_load_nltk_stopwords() -> set[str]:
    """
    Best-effort stopword loading.

    If NLTK data is missing (common in hackathon environments), we fall back
    to a tiny built-in list to keep the pipeline working.
    """
    try:
        from nltk.corpus import stopwords  # type: ignore

        return set(stopwords.words("english"))
    except Exception:
        return set(_FALLBACK_STOPWORDS)


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.lower()
    # Keep alphanumerics and key separators.
    text = re.sub(r"[^a-z0-9\.\-\+\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    text = clean_text(text)
    tokens = re.split(r"\s+", text)
    tokens = [t for t in tokens if len(t) >= 2]
    return tokens


def get_stopwords() -> set[str]:
    return _try_load_nltk_stopwords()


def extract_salary_numbers(text: str) -> List[float]:
    """
    Extract approximate salary numbers in LPA / annual figures.

    Examples handled:
    - "₹10 LPA", "10 LPA", "8-12 LPA"
    - "6 LPA - 12 LPA" -> [6, 12]
    """
    if not text:
        return []

    raw = clean_text(text)

    # Capture ranges too (e.g. 6-12 lpa)
    # Note: keep it simple; best effort for demo.
    pattern = re.compile(
        r"(?:₹\s*)?(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(lpa|l.p.a)\b"
    )
    values: List[float] = []
    for m in pattern.finditer(raw):
        a = float(m.group(1))
        b = m.group(2)
        values.append(a)
        if b is not None:
            values.append(float(b))

    # Also handle single plain "₹10" without "lpa" (rare, but safe best-effort)
    if not values:
        plain = re.findall(r"(?:₹\s*)?(\d+(?:\.\d+)?)", raw)
        values.extend(float(x) for x in plain[:20])

    return values

