from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt


def _ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def plot_skill_demand(
    jd_skills: List[str],
    missing_skills: List[str],
    output_path: str | Path,
    title: str = "Skill Demand (from Job Description)",
) -> None:
    _ensure_dir(Path(output_path).parent)
    skills = jd_skills[:15]

    if not skills:
        # Still create an empty chart for hackathon demo consistency.
        plt.figure(figsize=(10, 4))
        plt.title(title)
        plt.text(0.5, 0.5, "No JD skills extracted", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(str(output_path))
        plt.close()
        return

    # Hackathon-friendly: demand as "1 per extracted skill".
    counts = [1 for _ in skills]
    colors = ["#d62728" if s in set(missing_skills) else "#1f77b4" for s in skills]

    plt.figure(figsize=(12, 5))
    plt.bar(skills, counts, color=colors)
    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.ylabel("Extracted Frequency")
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()


def plot_resume_vs_jd_match(
    match_score: float,
    output_path: str | Path,
    title: str = "Resume vs Job Description Match",
) -> None:
    _ensure_dir(Path(output_path).parent)
    plt.figure(figsize=(6, 4))
    pct = max(0.0, min(100.0, float(match_score)))
    plt.bar(["Match"], [pct], color="#2ca02c")
    plt.ylim(0, 100)
    plt.title(title)
    plt.ylabel("Match Score (%)")
    plt.text(0, pct + 2, f"{pct:.1f}%", ha="center")
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()


def plot_missing_skills(
    missing_skills: List[str],
    output_path: str | Path,
    title: str = "Missing Skills (JD - Resume)",
) -> None:
    _ensure_dir(Path(output_path).parent)
    top = missing_skills[:15]
    if not top:
        plt.figure(figsize=(10, 4))
        plt.title(title)
        plt.text(0.5, 0.5, "No missing skills", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(str(output_path))
        plt.close()
        return

    plt.figure(figsize=(12, 5))
    plt.bar(top, [1] * len(top), color="#ff7f0e")
    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()


def plot_skill_trends(
    trends: Dict[str, dict],
    output_path: str | Path,
    title: str = "Google Trends (Interest Over Time)",
    max_skills: int = 4,
) -> None:
    _ensure_dir(Path(output_path).parent)
    if not trends:
        plt.figure(figsize=(10, 4))
        plt.title(title)
        plt.text(0.5, 0.5, "Trends unavailable (check internet/pytrends).", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(str(output_path))
        plt.close()
        return

    keys = list(trends.keys())[:max_skills]

    plt.figure(figsize=(12, 5))
    for kw in keys:
        series = trends.get(kw, {})
        dates = series.get("dates", [])
        values = series.get("values", [])
        if not dates or not values:
            continue
        # Normalize for comparability
        max_v = max(values) if values else 1.0
        norm = [v / max_v * 100.0 if max_v else 0.0 for v in values]
        plt.plot(dates, norm, label=kw)

    plt.title(title)
    plt.ylabel("Normalized Interest (%)")
    plt.xlabel("Date")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()


def plot_salary_distribution(
    salary_values: List[float],
    output_path: str | Path,
    title: str = "Salary Distribution (Extracted)",
) -> None:
    _ensure_dir(Path(output_path).parent)
    plt.figure(figsize=(8, 5))
    if not salary_values:
        plt.title(title)
        plt.text(0.5, 0.5, "No salary numbers extracted", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(str(output_path))
        plt.close()
        return

    cleaned = [float(x) for x in salary_values if math.isfinite(float(x))]
    plt.hist(cleaned, bins=min(10, max(3, len(cleaned))), color="#9467bd", edgecolor="black")
    plt.title(title)
    plt.xlabel("Salary (approx. LPA)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(str(output_path))
    plt.close()

