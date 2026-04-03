from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    sys.path.insert(0, str(src_path))


def _read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    _ensure_src_on_path()

    from placex.pipeline.runner import run_analysis  # noqa: WPS433

    parser = argparse.ArgumentParser(description="PlaceX - Market-Aware Resume Analyzer (CLI MVP)")
    parser.add_argument("--resume-pdf", required=True, help="Path to resume PDF")
    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument("--job-description-text", help="Job description text (paste here)")
    jd_group.add_argument("--job-description-file", help="Path to a .txt file containing job description")
    parser.add_argument("--config", default=None, help="Path to config YAML (optional)")
    parser.add_argument("--output", default="outputs", help="Output directory (reports + charts)")
    parser.add_argument(
        "--market-title",
        default=None,
        help='Optional: add market benchmark to report.json. Example: "Data Analyst" (run build_linkedin_aggregates.py first)',
    )

    args = parser.parse_args()

    if args.job_description_file:
        jd_text = _read_text_file(args.job_description_file)
    else:
        jd_text = args.job_description_text or ""

    report_path = run_analysis(
        resume_pdf_path=args.resume_pdf,
        jd_text=jd_text,
        config_path=args.config,
        output_dir=args.output,
        market_benchmark_title=args.market_title,
    )

    print(f"Report generated at: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

