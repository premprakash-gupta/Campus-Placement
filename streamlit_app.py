from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root / "src"))


_ensure_src_on_path()

from placex.pipeline.runner import run_analysis  # noqa: E402  # isort: skip


_LIGHT_THEME_CSS = """
<style>
    /* Light pastel palette: sky / mint / lavender */
    .stApp {
        background: linear-gradient(165deg, #f0f9ff 0%, #ecfdf5 35%, #faf5ff 70%, #f8fafc 100%);
        color: #000000 !important;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        color: #000000 !important;
    }
    /* Default body / markdown text: black */
    .block-container p,
    .block-container li,
    .block-container span:not([style*="color"]),
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {
        color: #000000 !important;
    }
    h1 {
        color: #000000 !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    h2, h3 {
        color: #000000 !important;
        font-weight: 600;
    }
    [data-testid="stCaptionContainer"] p {
        color: #000000 !important;
    }
    /* Widget labels */
    [data-testid="stWidgetLabel"] p,
    label {
        color: #000000 !important;
    }
    /* Inputs: soft borders */
    [data-baseweb="textarea"] textarea,
    [data-baseweb="input"] input {
        border-radius: 10px !important;
        border-color: #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    /* Primary button: light teal */
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #5eead4 0%, #2dd4bf 100%) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(45, 212, 191, 0.25);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #99f6e4 0%, #5eead4 100%) !important;
        color: #000000 !important;
    }
    /* Secondary / default buttons */
    .stButton > button[kind="secondary"] {
        border-radius: 10px !important;
    }
    /* File uploader area */
    [data-testid="stFileUploader"] section {
        border-radius: 12px !important;
        border: 1px dashed #94a3b8 !important;
        background: rgba(255, 255, 255, 0.7) !important;
    }
    /* Dividers softer */
    hr {
        border-color: #e2e8f0 !important;
        opacity: 0.9;
    }
    /* Metrics: black text */
    [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    [data-testid="stMetricValue"] {
        color: #000000 !important;
    }
    /* Full Report JSON (st.json): light visible panel */
    [data-testid="stJson"] {
        background: #e0f2fe !important;
        border: 1px solid #7dd3fc !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
    }
    /* Inner react-json-view uses inline bg — override for light panel */
    [data-testid="stJson"] .react-json-view,
    [data-testid="stJson"] .stJson > div {
        background-color: #f0f9ff !important;
        border-radius: 8px !important;
    }
    [data-testid="stJson"] pre,
    [data-testid="stJson"] code {
        background-color: rgba(255, 255, 255, 0.85) !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }
</style>
"""


st.set_page_config(page_title="PlaceX - Resume Analyzer", layout="wide")
st.markdown(_LIGHT_THEME_CSS, unsafe_allow_html=True)
st.title("PlaceX: Market-Aware Resume Analyzer")
st.caption(
    "Hackathon scope: **A)** Resume vs JD · **B)** Market view (top skills + salary from dataset) · "
    "**C)** JD skill gaps vs market skill gaps side-by-side."
)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Inputs")
    resume_file = st.file_uploader("Resume PDF", type=["pdf"])
    jd_file = st.file_uploader("Job Description PDF (optional)", type=["pdf"])
    jd_text_input = st.text_area("Or Job Description (paste text)", height=150, placeholder="Paste JD text here if not uploading a PDF...")

    config_choice = st.text_input(
        "Config YAML path (optional)",
        value="",
        placeholder="e.g., config/config.yaml (leave blank for default)",
    )

    output_dir = st.text_input("Output directory", value="outputs")

    market_benchmark_title = st.text_input(
        "Market benchmark (job title)",
        value="Data Analyst",
        help='Run once: python scripts/build_linkedin_aggregates.py --title "Data Analyst"',
    )

    analyze = st.button("Analyze", type="primary")

with col2:
    st.subheader("Hackathon triangle (don't overbuild)")
    st.markdown(
        """
        **A)** Resume vs **this job description** (match %, overlap, missing skills).

        **B)** **One market view** — postings whose `title` contains your *Market benchmark* string:
        top skills from `job_skills` + median salary from the same slice (pre-built JSON).

        **C)** **One differentiator** — **JD gaps** vs **market gaps** in two columns
        (what this posting asks for vs what similar postings demand).

        Prep: `python scripts/build_linkedin_aggregates.py --title \"Data Analyst\"`
        """
    )


def _save_upload(uploaded_file) -> str:
    repo_root = Path(__file__).resolve().parent
    upload_dir = repo_root / "data" / "interim" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / uploaded_file.name
    # Overwrite each run (hackathon-friendly).
    dest.write_bytes(uploaded_file.getbuffer())
    return str(dest)


if analyze:
    if resume_file is None:
        st.error("Please upload a resume PDF.")
        st.stop()
        
    jd_text = jd_text_input
    if jd_file is not None:
        try:
            jd_pdf_path = _save_upload(jd_file)
            from placex.extraction.resume_pdf import extract_text_from_pdf
            extracted_jd = extract_text_from_pdf(jd_pdf_path)
            jd_text = extracted_jd + "\\n" + jd_text
        except Exception as e:
            st.error(f"Failed to read JD PDF: {e}")
            st.stop()

    if not jd_text.strip():
        st.error("Please provide a Job Description (either PDF or text).")
        st.stop()

    with st.spinner("Analyzing... (this may take a bit for PDF extraction)"):
        try:
            resume_pdf_path = _save_upload(resume_file)
            config_path = config_choice.strip() or None

            report_path = run_analysis(
                resume_pdf_path=resume_pdf_path,
                jd_text=jd_text,
                config_path=config_path,
                output_dir=output_dir,
                market_benchmark_title=(market_benchmark_title.strip() or None),
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"Analysis failed: {e}")
            raise

    st.success(f"Report generated: {report_path}")

    # Load and display JSON report
    try:
        import json

        report_json = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        report_json = None

    # ATS-style score (heuristic composite)
    st.divider()
    st.subheader("ATS-style score")
    st.caption(
        "Single 0–100 score blending **JD skills**, **JD keyword overlap** (phrase match), "
        "optional **market skills**, and resume length. For demos only — not a vendor ATS."
    )
    if report_json and report_json.get("ats"):
        ats = report_json["ats"]
        a1, a2 = st.columns([1, 2])
        with a1:
            st.metric(
                "Score / 100",
                f"{float(ats.get('ats_score', 0)):.1f}",
                help=str(ats.get("disclaimer", "")),
            )
            st.markdown(f"**{ats.get('grade', '—')}** fit")
        with a2:
            st.write(ats.get("formula", ""))
            st.write(ats.get("length_note", ""))
            with st.expander("Score breakdown (components)"):
                comp = ats.get("components") or {}
                for k, v in comp.items():
                    st.write(f"- **{k}:** `{v}`")
                st.caption(str(ats.get("disclaimer", "")))
    elif report_json:
        st.warning("ATS block missing from report (re-run analysis with latest code).")

    if report_json and report_json.get("ats"):
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("#### 🚀 Actionable Steps to Improve ATS Score")
        
        recs = []
        jd_missing = report_json.get("missing_skills", [])
        if jd_missing:
            recs.append(("Add missing core skills", f"The JD asks for **{', '.join(jd_missing[:5])}** which were not found in your resume.", "🎯"))
            
        ats_comp = report_json["ats"].get("components", {})
        kw_hit = ats_comp.get("jd_keyword_hit_pct")
        if kw_hit is not None and kw_hit < 70:
            recs.append(("Use exact phrases", f"Your exact keyword overlap is **{kw_hit:.0f}%**. Try borrowing exact wording from the JD to get past basic ATS filters.", "📝"))
            
        length_note = report_json["ats"].get("length_note", "")
        if "short" in length_note.lower():
            recs.append(("Flesh out your experience", "Your resume text is shorter than average. Add more context to your accomplishments.", "📏"))
        elif "long" in length_note.lower():
            recs.append(("Be more concise", "Your resume is longer than average. Consider trimming older or less relevant roles.", "✂️"))
            
        if not recs:
            st.success("Your resume is well-optimized for this role!", icon="✅")
        else:
            rec_cols = st.columns(len(recs) if len(recs) > 0 else 1)
            for i, (title, desc, icon) in enumerate(recs):
                with rec_cols[i % len(rec_cols)]:
                    st.info(f"**{title}**\\n\\n{desc}", icon=icon)

    # Summary metrics (A + B headline numbers)
    st.divider()
    st.subheader("Results at a glance")
    match_score = float(report_json.get("match_score", 0.0)) if report_json else 0.0

    import pandas as pd

    bench = None
    agg = None
    try:
        from placex.market.dataset_benchmark import compare_resume_to_market, load_market_aggregate

        agg = load_market_aggregate(market_benchmark_title.strip() or "Data Analyst")
        if agg and report_json:
            bench = compare_resume_to_market(report_json.get("resume_skills") or [], agg)
    except Exception:  # noqa: BLE001
        pass

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("A · JD match score", f"{match_score:.1f}%", help="Resume vs pasted job description (skill lexicon).")
    with m2:
        if bench:
            st.metric(
                "B · Market alignment",
                f"{bench['market_alignment_pct']:.1f}%",
                help="Share of top market skills that overlap with your resume.",
            )
        else:
            st.metric("B · Market alignment", "—", help="Build aggregate JSON for the market title.")
    with m3:
        sal = (bench or {}).get("salary_summary") or {}
        if isinstance(sal, dict) and sal.get("median") is not None:
            st.metric(
                "B · Median salary (slice)",
                f"{sal.get('median'):,.0f}",
                help=f"Dataset salary field in matched postings (n={sal.get('n_salary_samples', 0)}).",
            )
        else:
            st.metric("B · Median salary (slice)", "—", help="Needs aggregate + salary values in postings slice.")

    # A · Resume vs JD
    st.divider()
    st.subheader("A · Resume vs job description")
    if report_json:
        matched = report_json.get("matched_skills", [])
        missing = report_json.get("missing_skills", [])

        a, b = st.columns(2)
        with a:
            st.markdown("#### Matching skills")
            st.write(matched if matched else ["None found"])
        with b:
            st.markdown("#### Missing skills (what the JD asks, not on resume)")
            st.write(missing if missing else ["None found"])

    # C · JD gap vs market gap
    st.divider()
    st.subheader("C · Gap comparison: this job vs market demand")
    st.caption(
        "Left: skills the **JD** expects that didn’t show up as resume skills. "
        "Right: top **market** skills for your *Market benchmark* title that your resume doesn’t cover."
    )
    if report_json:
        jd_missing = report_json.get("missing_skills") or []
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("#### Gaps for this job description")
            st.write(jd_missing if jd_missing else ["None — great JD fit on extracted skills"])
        with g2:
            try:
                from placex.market.dataset_benchmark import load_market_aggregate, market_top_skill_gaps

                _agg = agg or load_market_aggregate(market_benchmark_title.strip() or "Data Analyst")
                if _agg:
                    mk_gaps = market_top_skill_gaps(
                        report_json.get("resume_skills") or [],
                        _agg,
                        top_n=15,
                    )
                    st.markdown("#### Gaps vs market (top 15 demand skills)")
                    st.write(mk_gaps if mk_gaps else ["None — you cover all top market skills in this slice"])
                else:
                    st.info("Build an aggregate first (see sidebar help).")
            except Exception as e:  # noqa: BLE001
                st.warning(str(e))

    # B · Market view (chart + context)
    st.divider()
    st.subheader("B · Market view (dataset)")
    try:
        from placex.market.dataset_benchmark import load_market_aggregate

        _agg2 = agg or load_market_aggregate(market_benchmark_title.strip() or "Data Analyst")
        if _agg2 and report_json:
            st.caption(
                f"Title filter: **`{_agg2.get('title_filter', market_benchmark_title)}`** — "
                f"**{_agg2.get('job_postings_matched', '?')}** postings in slice. "
                "Skills = frequency of `skill_abr` linked to those jobs."
            )
            sal2 = _agg2.get("salary") or {}
            if isinstance(sal2, dict) and sal2.get("median") is not None:
                st.caption(
                    f"Median salary in slice: **{sal2.get('median'):,.0f}** "
                    f"(p25–p75: {sal2.get('p25'):,.0f} – {sal2.get('p75'):,.0f}, "
                    f"n={sal2.get('n_salary_samples', 0)})"
                )
            rows = _agg2.get("top_skills") or []
            if rows:
                chart_df = pd.DataFrame(
                    [{"skill": r.get("skill_name", r.get("skill_abr")), "count": r.get("count", 0)} for r in rows]
                )
                st.markdown("##### Top skills in this market slice")
                st.bar_chart(chart_df.set_index("skill")["count"])
        elif report_json:
            st.info(
                f"No market aggregate for **{market_benchmark_title!r}**. Run: "
                f"`python scripts/build_linkedin_aggregates.py --title {market_benchmark_title!r}`"
            )
    except Exception as e:  # noqa: BLE001
        st.warning(f"Market view skipped: {e}")

    # Cover Letter Generation
    st.divider()
    st.subheader("D · Automated Cover Letter Generation")
    st.caption("Use a Hugging Face serverless inference model to automatically draft a tailored cover letter addressing your skill gaps.")
    
    if report_json:
        hf_token = st.text_input("Hugging Face API Token (optional)", type="password", help="Leave blank to use the free public rate-limited inference API, or provide a token for higher limits.")
        
        if st.button("Generate Targeted Cover Letter ✨"):
            with st.spinner("Generating cover letter using AI... this may take a few seconds."):
                try:
                    from placex.nlp.cover_letter import generate_cover_letter
                    
                    r_skills = report_json.get("resume_skills", [])
                    m_skills = report_json.get("missing_skills", [])
                    letter = generate_cover_letter(jd_text, r_skills, m_skills, hf_token)
                    st.success("Cover Letter Generated!")
                    st.text_area("Your Cover Letter (Edit & Copy)", value=letter, height=400)
                except Exception as e:
                    st.error(f"Failed to generate: {e}")

    # Charts + Google Trends (interactive when API returns series)
    st.divider()
    st.subheader("Charts")
    if report_json:
        st.markdown("#### Google Trends (search interest over time)")
        st.caption(
            "Live **Google Trends** data from `pytrends` (needs internet). "
            "Up to 5 skills from your JD gap / match lists — normalized 0–100 by Google. "
            "If this is empty, try again online or check rate limits."
        )
        trends_raw = report_json.get("trends") or {}
        if trends_raw:
            trend_rows: dict[str, dict] = {}
            n_common: int | None = None
            for kw, ser in trends_raw.items():
                dates = ser.get("dates") or []
                vals = ser.get("values") or []
                ln = min(len(dates), len(vals))
                if ln == 0:
                    continue
                if n_common is None:
                    n_common = ln
                else:
                    n_common = min(n_common, ln)
                trend_rows[str(kw)] = {"dates": dates[:ln], "values": vals[:ln]}
            if trend_rows and n_common and n_common > 0:
                first = next(iter(trend_rows.values()))
                idx = first["dates"][:n_common]
                trend_df = pd.DataFrame(
                    {k: trend_rows[k]["values"][:n_common] for k in trend_rows},
                    index=idx,
                )
                st.line_chart(trend_df)
            else:
                st.info("Trend payload was empty after parsing.")
        else:
            trend_png = Path((report_json.get("charts") or {}).get("skill_trendline", ""))
            if trend_png.exists():
                st.image(str(trend_png), caption="Google Trends (saved chart fallback)", use_container_width=True)
            else:
                st.info(
                    "No Google Trends series returned (offline, rate limit, or blocked). "
                    "Pipeline still completed; other charts below use local NLP + data."
                )

        st.markdown("#### Other charts")
        charts = report_json.get("charts") or {}
        chart_cols = st.columns(2)
        idx_chart = 0
        for label, path in charts.items():
            if label == "skill_trendline":
                continue
            if not path:
                continue
            target_col = chart_cols[idx_chart % 2]
            idx_chart += 1
            with target_col:
                p = Path(path)
                if p.exists():
                    target_col.image(str(p), caption=label, use_container_width=True)
                else:
                    target_col.write(f"{label}: not generated")

