"""
Phase B — Explore CSVs in data/raw/ (override: PLACEX_LINKEDIN_RAW_DIR)

Loads up to 5000 rows per file (safe for large postings.csv), prints a short
report, and writes data/interim/linkedin_schema_summary.json for your notes.

Usage:
  python scripts/explore_linkedin_dataset.py
  python scripts/explore_linkedin_dataset.py --nrows 10000
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))


def _guess_role(columns: list[str]) -> str:
    """Lightweight hint for interviews / your notes."""
    cj = [c.lower() for c in columns]
    hints = []
    if any("job" in c or "posting" in c for c in cj):
        hints.append("likely postings/job table")
    if any("skill" in c for c in cj):
        hints.append("likely skills mapping")
    if any("compan" in c for c in cj):
        hints.append("likely company table")
    if any(re.search(r"\bid\b|_id$|_id_", c) for c in cj):
        hints.append("has id-like columns for joins")
    return "; ".join(hints) if hints else "inspect columns manually"


def main() -> int:
    _ensure_src_on_path()
    from placex.market.linkedin_loader import get_raw_dir, list_raw_csvs, load_csv

    parser = argparse.ArgumentParser(description="Explore LinkedIn-style CSVs in raw/")
    parser.add_argument("--nrows", type=int, default=5000, help="Rows to read per CSV (default 5000)")
    args = parser.parse_args()

    raw = get_raw_dir()
    paths = list_raw_csvs()
    if not paths:
        print("No CSV files found under:", raw)
        print("Copy postings.csv and jobs/mappings/companies folders into that path, then run again.")
        return 1

    summary: dict = {"raw_dir": str(raw), "files": {}}

    for p in paths:
        rel = str(p.relative_to(raw)) if p.is_relative_to(raw) else p.name
        try:
            df = load_csv(p, nrows=args.nrows)
            cols = list(df.columns)
            summary["files"][rel] = {
                "path": str(p.resolve()),
                "n_columns": len(cols),
                "columns": cols,
                "dtypes": {c: str(t) for c, t in df.dtypes.items()},
                "rows_read": len(df),
                "note": _guess_role(cols),
                "head_json": df.head(3).to_dict(orient="records"),
            }
        except Exception as e:  # noqa: BLE001
            summary["files"][rel] = {"error": str(e), "path": str(p.resolve())}

    out_dir = Path(__file__).resolve().parents[1] / "data" / "interim"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "linkedin_schema_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # Console: compact view
    print("=" * 60)
    print("Phase B — Dataset exploration")
    print("Raw dir:", raw)
    print("CSV files found:", len(paths))
    print("Full JSON written to:", out_path)
    print("=" * 60)
    for rel, meta in summary["files"].items():
        print(f"\n--- {rel} ---")
        if "error" in meta:
            print("  ERROR:", meta["error"])
            continue
        print("  Rows read:", meta.get("rows_read"), "| Columns:", meta.get("n_columns"))
        print("  Hint:", meta.get("note"))
        print("  Columns:", ", ".join(meta.get("columns", [])[:25]), end="")
        if meta.get("n_columns", 0) > 25:
            print(" ...")
        else:
            print()

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1) Open linkedin_schema_summary.json and note join keys (e.g. job_id, company_id).")
    print("  2) In a notebook, test: df = load_csv('postings.csv', nrows=5000) and explore value counts.")
    print("  3) Run scripts/build_linkedin_aggregates.py when we add it (Phase D).")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
