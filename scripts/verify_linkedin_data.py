"""
Print a summary of CSVs in data/raw/ (Phase A check). Override: PLACEX_LINKEDIN_RAW_DIR.

Usage:
  python scripts/verify_linkedin_data.py
  python scripts/verify_linkedin_data.py --peek 5000
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))


def main() -> int:
    _ensure_src_on_path()
    from placex.market.linkedin_loader import describe_raw_dataset, get_raw_dir, list_raw_csvs

    parser = argparse.ArgumentParser(description="Verify LinkedIn raw CSVs are present and readable.")
    parser.add_argument("--peek", type=int, default=3, help="Sample rows per file for dtype inference")
    args = parser.parse_args()

    raw = get_raw_dir()
    print(f"Raw directory: {raw}")
    print(f"CSV files: {len(list_raw_csvs())}")
    summary = describe_raw_dataset(nrows_peek=args.peek)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
