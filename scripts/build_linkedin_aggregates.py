"""
Phase D — Build market aggregates from data/raw (LinkedIn-style CSVs).

Streams postings.csv in chunks (large file), filters by title substring,
joins job_skills + skills, and writes JSON to data/aggregates/.

Usage:
  python scripts/build_linkedin_aggregates.py --title "Data Analyst"
  python scripts/build_linkedin_aggregates.py --title "Software Engineer" --top-n 25
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))


def slugify_title(title: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", title, flags=re.UNICODE)
    s = re.sub(r"[\s\-]+", "_", s.strip()).lower()
    return (s[:100] if s else "unknown")


def main() -> int:
    _ensure_src_on_path()
    from placex.market.linkedin_loader import get_aggregates_dir, get_raw_dir

    parser = argparse.ArgumentParser(description="Build market skill/salary aggregates for a job title")
    parser.add_argument("--title", type=str, default="Data Analyst", help="Substring to match on postings.title")
    parser.add_argument("--top-n", type=int, default=20, dest="top_n", help="Top N skills to keep")
    parser.add_argument(
        "--chunksize",
        type=int,
        default=50_000,
        help="Rows per chunk when reading postings.csv",
    )
    args = parser.parse_args()

    raw = get_raw_dir()
    agg_dir = get_aggregates_dir()
    agg_dir.mkdir(parents=True, exist_ok=True)

    postings_path = raw / "postings.csv"
    job_skills_path = raw / "jobs" / "job_skills.csv"
    skills_map_path = raw / "mappings" / "skills.csv"

    for p in (postings_path, job_skills_path, skills_map_path):
        if not p.is_file():
            print(f"Missing required file: {p}")
            return 1

    import numpy as np
    import pandas as pd

    print("Loading skill name map...")
    df_skills = pd.read_csv(skills_map_path, encoding="utf-8", on_bad_lines="warn")
    if "skill_abr" not in df_skills.columns or "skill_name" not in df_skills.columns:
        print("skills.csv must have columns skill_abr, skill_name")
        return 1
    abr_to_name = df_skills.set_index("skill_abr")["skill_name"].to_dict()

    print("Loading job_skills (full table)...")
    job_skills = pd.read_csv(job_skills_path, encoding="utf-8", on_bad_lines="warn", dtype={"job_id": "int64"})

    title_pat = args.title
    print(f"Scanning postings.csv for title containing: {title_pat!r} ...")

    want_cols = [
        "job_id",
        "title",
        "med_salary",
        "normalized_salary",
        "min_salary",
        "max_salary",
    ]
    peek = pd.read_csv(postings_path, nrows=0, encoding="utf-8", on_bad_lines="warn")
    usecols = [c for c in want_cols if c in peek.columns]
    if "job_id" not in usecols or "title" not in usecols:
        print("postings.csv must contain at least job_id and title columns.")
        return 1

    job_ids: set[int] = set()
    salary_vals: list[float] = []

    chunk_n = 0
    for chunk in pd.read_csv(
        postings_path,
        chunksize=args.chunksize,
        usecols=usecols,
        encoding="utf-8",
        on_bad_lines="warn",
        low_memory=False,
    ):
        chunk_n += 1
        if chunk_n % 5 == 0:
            print(f"  ... chunks processed: {chunk_n}, matched job_ids so far: {len(job_ids)}")

        m = chunk["title"].astype(str).str.contains(title_pat, case=False, na=False, regex=False)
        sub = chunk.loc[m]
        if sub.empty:
            continue

        for jid in sub["job_id"].dropna().astype(int):
            job_ids.add(int(jid))

        # Prefer normalized_salary, then med_salary
        for col in ("normalized_salary", "med_salary"):
            if col not in sub.columns:
                continue
            s = pd.to_numeric(sub[col], errors="coerce").dropna()
            salary_vals.extend(float(x) for x in s.tolist())
            break

    print(f"Matched postings: {len(job_ids)}")
    if not job_ids:
        print("No postings matched. Try a broader --title string.")
        return 1

    print("Filtering job_skills to matched job_ids...")
    js = job_skills[job_skills["job_id"].isin(job_ids)]
    if js.empty:
        print("No job_skills rows for matched job_ids (unexpected).")
        return 1

    counts = js["skill_abr"].value_counts().head(args.top_n)

    top_skills = []
    for abr, cnt in counts.items():
        name = abr_to_name.get(abr, str(abr))
        top_skills.append(
            {
                "skill_abr": str(abr),
                "skill_name": str(name),
                "count": int(cnt),
            }
        )

    sal_obj: dict = {"n_salary_samples": len(salary_vals)}
    if salary_vals:
        arr = np.array(salary_vals, dtype=float)
        sal_obj.update(
            {
                "median": float(np.median(arr)),
                "p25": float(np.percentile(arr, 25)),
                "p75": float(np.percentile(arr, 75)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
            }
        )
    else:
        sal_obj["note"] = "No salary values in matched postings (columns empty or non-numeric)."

    out = {
        "title_filter": title_pat,
        "job_postings_matched": len(job_ids),
        "top_skills": top_skills,
        "salary": sal_obj,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    slug = slugify_title(title_pat)
    out_path = agg_dir / f"market_{slug}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
