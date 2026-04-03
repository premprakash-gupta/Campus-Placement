from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .schemas import Report


def write_report(report: Report, output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "report.json"
    payload: Dict[str, Any] = asdict(report)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Convenience copy for demo "latest"
    latest_path = out_dir / "report_latest.json"
    try:
        with latest_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return report_path

