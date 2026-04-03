# PlaceX - Market-Aware Resume Analyzer

This is a hackathon-friendly initial architecture + end-to-end CLI + Streamlit + optional LinkedIn-style job dataset benchmarks.

## Step-by-step workflow (do in order)

**Step 1 — Install dependencies**

```bash
git clone git@github.com:premprakash-gupta/Campus-Placement.git
cd Campus-Placement
python -m pip install -r requirements.txt
OR
uv init  # Fastest way to create Python virtual environment.
uv venv
uv add -r requirements.txt

```

**Step 2 — Put job data in `data/raw/`** (optional but needed for market charts / `report.json` `market_benchmark`)

- Copy your CSV bundle here: `postings.csv`, and folders `jobs/`, `mappings/`, `companies/` under `data/raw/`.

**Step 3 — Verify CSVs are visible**

```powershell
python scripts\verify_linkedin_data.py
```

You should see a non-zero CSV count.

**Step 4 — Explore schemas (optional)**

```powershell
python scripts\explore_linkedin_dataset.py
```

Opens a summary at `data\interim\linkedin_schema_summary.json`.

**Step 5 — Build market aggregates** (one JSON per job-title filter; do this once per title you care about)

```powershell
python scripts\build_linkedin_aggregates.py --title "Data Analyst" --top-n 20
```

Output: `data\aggregates\market_data_analyst.json` (filename slug follows the title).

**Step 6 — Run analysis (CLI)**  
Use the **same** title string in `--market-title` as in Step 5 if you want `market_benchmark` inside the report.

```powershell
python scripts\run_cli.py --resume-pdf path\to\resume.pdf --job-description-text "Paste JD here..." --output outputs --market-title "Data Analyst"
```

Outputs:

- `outputs/reports/report.json` (includes `market_benchmark` when `--market-title` is set)
- Charts under `outputs/charts/` (if `--output outputs`; reports go under `outputs/reports/`)

**Step 7 — Or use Streamlit**

```powershell
streamlit run streamlit_app.py
```

Upload PDF, paste JD, set **Market benchmark (job title)** to match Step 5, click **Analyze**.

---

## Run (minimal, without dataset)

1. `pip install -r requirements.txt`
2. `python scripts/run_cli.py --resume-pdf path/to/resume.pdf --job-description-text "..." --output outputs`

## Notes

- Google Trends (`pytrends`) is best-effort: if it fails (no internet), the pipeline still works and charts are generated where possible.
- Override raw data folder: set env `PLACEX_LINKEDIN_RAW_DIR` to your CSV directory.
