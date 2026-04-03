from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..extraction.resume_pdf import extract_text_from_pdf
from ..market.dataset_benchmark import compare_resume_to_market, load_market_aggregate
from ..market.news import fetch_news_insights
from ..market.trends import fetch_google_trends
from ..matching.ats_score import compute_ats_score, simple_jd_keyword_hits
from ..matching.skill_matcher import compute_skill_match
from ..nlp.keyword_extractor import extract_skill_keywords, load_skills_lexicon
from ..nlp.preprocess import extract_salary_numbers
from ..reporting.schemas import Report
from ..reporting.write_report import write_report
from ..visualization.charts import (
    plot_missing_skills,
    plot_resume_vs_jd_match,
    plot_skill_demand,
    plot_skill_trends,
    plot_salary_distribution,
)


def _default_repo_root() -> Path:
    # PlaceX/src/placex/pipeline/runner.py -> PlaceX
    return Path(__file__).resolve().parents[3]


def load_config(config_path: str | Path) -> dict:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run_analysis(
    resume_pdf_path: str,
    jd_text: str,
    config_path: Optional[str] = None,
    output_dir: str | Path = "outputs",
    market_benchmark_title: Optional[str] = None,
) -> Path:
    repo_root = _default_repo_root()
    if config_path is None:
        config_path = repo_root / "config" / "config.yaml"

    cfg = load_config(config_path)

    pipeline_cfg = cfg.get("pipeline", {})
    top_skills_for_trends = int(pipeline_cfg.get("top_skills_for_trends", 5))
    keyword_top_n = int(pipeline_cfg.get("keyword_top_n", 20))
    timeframe = str(pipeline_cfg.get("timeframe", "today 12-m"))
    geo = str(pipeline_cfg.get("geo", "IN"))

    lexicon_raw = cfg.get("skills_lexicon", [])
    skills_lexicon = load_skills_lexicon(lexicon_raw)

    resume_text = extract_text_from_pdf(resume_pdf_path)

    resume_skills: List[str] = extract_skill_keywords(resume_text, skills_lexicon, top_n=keyword_top_n)
    jd_skills: List[str] = extract_skill_keywords(jd_text, skills_lexicon, top_n=keyword_top_n)

    match_result = compute_skill_match(resume_skills, jd_skills)

    salary_values = extract_salary_numbers(resume_text) + extract_salary_numbers(jd_text)

    # Trends: use a short, unique set biased towards gaps.
    trend_keywords: List[str] = []
    for s in match_result.missing_skills:
        if s not in trend_keywords:
            trend_keywords.append(s)
        if len(trend_keywords) >= top_skills_for_trends:
            break
    for s in match_result.matched_skills:
        if s not in trend_keywords:
            trend_keywords.append(s)
        if len(trend_keywords) >= top_skills_for_trends:
            break

    trends = fetch_google_trends(trend_keywords, timeframe=timeframe, geo=geo)
    news = fetch_news_insights(trend_keywords)
    news_highlights = news.get("highlights", []) if isinstance(news, dict) else []

    output_dir = Path(output_dir)
    charts_dir = output_dir / "charts"
    reports_dir = output_dir / "reports"

    chart_paths: Dict[str, str] = {
        "skill_demand": str(charts_dir / "skill_demand.png"),
        "resume_vs_jd": str(charts_dir / "resume_vs_jd.png"),
        "missing_skills": str(charts_dir / "missing_skills.png"),
        "skill_trendline": str(charts_dir / "skill_trendline.png"),
        "salary_distribution": str(charts_dir / "salary_distribution.png"),
    }

    # Generate charts (best-effort; each function creates an empty placeholder if needed)
    plot_skill_demand(jd_skills, match_result.missing_skills, chart_paths["skill_demand"])
    plot_resume_vs_jd_match(match_result.match_score, chart_paths["resume_vs_jd"])
    plot_missing_skills(match_result.missing_skills, chart_paths["missing_skills"])
    plot_skill_trends(trends, chart_paths["skill_trendline"])
    plot_salary_distribution(salary_values, chart_paths["salary_distribution"])

    market_payload: Optional[Dict[str, Any]] = None
    if market_benchmark_title and str(market_benchmark_title).strip():
        title_key = str(market_benchmark_title).strip()
        agg = load_market_aggregate(title_key)
        if agg:
            comparison = compare_resume_to_market(resume_skills, agg)
            market_payload = {
                "aggregate_found": True,
                "title_requested": title_key,
                "title_filter": agg.get("title_filter"),
                "job_postings_matched": agg.get("job_postings_matched"),
                "comparison": comparison,
                "top_skills": agg.get("top_skills", []),
                "salary": agg.get("salary"),
            }
        else:
            market_payload = {
                "aggregate_found": False,
                "title_requested": title_key,
                "hint": f'Run: python scripts/build_linkedin_aggregates.py --title "{title_key}"',
            }

    market_align_pct: Optional[float] = None
    if market_payload and market_payload.get("aggregate_found"):
        comp = market_payload.get("comparison") or {}
        if isinstance(comp, dict) and comp.get("market_alignment_pct") is not None:
            market_align_pct = float(comp["market_alignment_pct"])

    jd_keyword_hits = simple_jd_keyword_hits(resume_text, jd_text)
    ats_payload = compute_ats_score(
        jd_match_pct=match_result.match_score,
        market_alignment_pct=market_align_pct,
        resume_text_len=len(resume_text or ""),
        jd_keyword_hit_pct=jd_keyword_hits,
    )

    report = Report(
        resume_pdf_path=str(resume_pdf_path),
        jd_text_source="provided_text_or_file",
        jd_skills=jd_skills,
        resume_skills=resume_skills,
        matched_skills=match_result.matched_skills,
        missing_skills=match_result.missing_skills,
        match_score=match_result.match_score,
        salary_values_lpa=[float(x) for x in salary_values],
        trends=trends,
        news_highlights=news_highlights,
        charts=chart_paths,
        ats=ats_payload,
        market_benchmark=market_payload,
    )

    return write_report(report, reports_dir)

