"""
Load LinkedIn-style job posting CSVs from data/raw/ (default).

Place CSVs and subfolders (jobs, mappings, companies) there, or set
PLACEX_LINKEDIN_RAW_DIR to another folder. Use list_raw_csvs(), load_csv(),
or load_by_name_hint().
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Optional

# Lazy import so importing this module does not require pandas until used.
import importlib


def _pandas():
    return importlib.import_module("pandas")


def _repo_root() -> Path:
    # src/placex/market/linkedin_loader.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def get_raw_dir() -> Path:
    """
    Directory where raw CSVs live (default: ``<repo>/data/raw``).

    Override with env ``PLACEX_LINKEDIN_RAW_DIR`` (absolute path recommended).
    """
    override = os.environ.get("PLACEX_LINKEDIN_RAW_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _repo_root() / "data" / "raw"


def get_aggregates_dir() -> Path:
    """Where precomputed Parquet/JSON aggregates should be written (Phase D)."""
    return _repo_root() / "data" / "aggregates"


def ensure_raw_dir_exists() -> Path:
    d = get_raw_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_raw_csvs(*, recursive: bool = True) -> list[Path]:
    """
    All .csv files under the raw directory.

    Default ``recursive=True`` so you can keep a Kaggle-style layout, e.g.::

        raw/postings.csv
        raw/jobs/...
        raw/mappings/...
        raw/companies/...
    """
    d = get_raw_dir()
    if not d.is_dir():
        return []
    if not recursive:
        return sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() == ".csv")
    return sorted(d.rglob("*.csv"))


def find_csv_in_raw(name: str) -> Path | None:
    """
    Find a CSV under ``raw/`` by exact filename (e.g. ``postings.csv``).

    Searches recursively. If several files share the same name, returns the
    first path in sorted order (use a full path in ``load_csv`` to avoid ambiguity).
    """
    d = get_raw_dir()
    if not d.is_dir():
        return None
    name_l = name.lower()
    matches = [p for p in d.rglob("*.csv") if p.name.lower() == name_l]
    if not matches:
        return None
    return sorted(matches)[0]


def read_csv_header(path: str | Path, encoding: str = "utf-8") -> list[str]:
    """First row of a CSV as column names (fast, no full parse)."""
    p = Path(path)
    pd = _pandas()
    return list(pd.read_csv(p, nrows=0, encoding=encoding, on_bad_lines="warn").columns)


def load_csv(
    path_or_filename: str | Path,
    *,
    nrows: Optional[int] = None,
    encoding: str = "utf-8",
    low_memory: bool = False,
    **read_csv_kwargs: Any,
) -> "Any":
    """
    Load one CSV from raw dir by full path or by filename (must exist in raw/).

    Pass nrows=5000 while exploring schema to keep things fast.
    """
    pd = _pandas()
    p = Path(path_or_filename)
    if not p.is_file():
        candidate = get_raw_dir() / path_or_filename
        if candidate.is_file():
            p = candidate
        else:
            found = find_csv_in_raw(Path(path_or_filename).name)
            if found is not None:
                p = found
            if not p.is_file():
                raise FileNotFoundError(
                    f"CSV not found: {path_or_filename} (looked under {get_raw_dir()})"
                )

    kwargs = dict(
        encoding=encoding,
        low_memory=low_memory,
        on_bad_lines="warn",
    )
    kwargs.update(read_csv_kwargs)
    if nrows is not None:
        kwargs["nrows"] = nrows

    return pd.read_csv(p, **kwargs)


def load_by_name_hint(
    hint: str,
    *,
    nrows: Optional[int] = None,
    **read_csv_kwargs: Any,
) -> tuple[Path, Any]:
    """
    Load the first CSV whose filename contains `hint` (case-insensitive).

    Example: load_by_name_hint("skill") for job_skills.csv
    Returns (path_used, DataFrame).
    """
    hint_l = hint.lower()
    matches = [p for p in list_raw_csvs() if hint_l in p.name.lower()]
    if not matches:
        raise FileNotFoundError(
            f"No CSV in {get_raw_dir()} matches hint {hint!r}. "
            f"Available: {[p.name for p in list_raw_csvs()]}"
        )
    if len(matches) > 1:
        # Prefer shortest name (often the main file) or first sorted
        matches.sort(key=lambda x: (len(x.name), x.name))
    path = matches[0]
    return path, load_csv(path, nrows=nrows, **read_csv_kwargs)


def describe_raw_dataset(
    *,
    nrows_peek: int = 3,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """
    Summary of every CSV in raw/: columns, dtypes, row count (full scan per file).

    For large files, row count can be slow; use nrows_peek only for sample rows.
    """
    pd = _pandas()
    raw = get_raw_dir()
    out: dict[str, Any] = {"raw_dir": str(raw), "files": {}}
    paths = list_raw_csvs()
    if not paths:
        out["error"] = "No CSV files found. Copy your dataset CSVs into the raw folder."
        return out

    # Skip full line-count for huge files (e.g. 500MB postings.csv) — too slow.
    _LARGE_BYTES = 50 * 1024 * 1024

    for p in paths:
        rel = str(p.relative_to(raw)) if p.is_relative_to(raw) else p.name
        try:
            df_head = pd.read_csv(p, nrows=nrows_peek, encoding=encoding, on_bad_lines="warn")
            row_count: Optional[int] | str = None
            try:
                sz = p.stat().st_size
                if sz > _LARGE_BYTES:
                    row_count = "skipped (large file; use pandas or DuckDB to count)"
                else:
                    with p.open("r", encoding=encoding, errors="replace") as f:
                        row_count = sum(1 for _ in f) - 1
                        if isinstance(row_count, int) and row_count < 0:
                            row_count = 0
            except OSError:
                row_count = None

            out["files"][rel] = {
                "path": str(p.resolve()),
                "columns": list(df_head.columns),
                "dtypes": {c: str(t) for c, t in df_head.dtypes.items()},
                "sample_rows": nrows_peek,
                "approx_row_count": row_count,
            }
        except Exception as e:  # noqa: BLE001
            out["files"][rel] = {"error": str(e)}
    return out


def load_standard_bundle(
    *,
    nrows: Optional[int] = None,
    postings_hint: str = "posting",
    skills_hint: str = "skill",
    companies_hint: str = "compan",
) -> dict[str, Any]:
    """
    Try to load main postings, skills, and company files using filename hints.

    Adjust hints to match your actual filenames after you copy CSVs into raw/.
    Returns dict with keys: postings, skills, companies, paths (meta).
    Missing keys are None if no file matched.
    """
    result: dict[str, Any] = {"postings": None, "skills": None, "companies": None, "paths": {}}

    def try_hint(key: str, hint: str) -> None:
        try:
            path, df = load_by_name_hint(hint, nrows=nrows)
            result[key] = df
            result["paths"][key] = str(path)
        except FileNotFoundError:
            result["paths"][key] = None

    try_hint("postings", postings_hint)
    try_hint("skills", skills_hint)
    try_hint("companies", companies_hint)

    return result
