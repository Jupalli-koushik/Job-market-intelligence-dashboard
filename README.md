# India Data & AI Job Market Intelligence

Phase 1 captures a raw Adzuna India API dump for the bronze data layer.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:ADZUNA_APP_ID = "your_app_id"
$env:ADZUNA_APP_KEY = "your_app_key"
```

## Pull raw data

```powershell
py scripts\pull_adzuna.py
```

The script searches each target role with exact and broader fallback terms, retrieves up to three pages per term, and saves each response under a UTC-stamped directory in `data/bronze/`. It also captures the salary-history and top-companies responses for each role. API responses, including non-success responses, are retained as JSON for inspection; the raw layer is intentionally not cleaned.

Useful options:

```powershell
py scripts\pull_adzuna.py --max-pages 5 --results-per-page 50 --delay-seconds 1
```

## Clean and extract skills

After a bronze run exists, pass its timestamped directory to the Phase 2 cleaner:

```powershell
py -m pip install -r requirements.txt
py scripts\clean_jobs.py data\bronze\20260827T120000Z
```

The cleaner writes `data/silver/jobs_clean.csv` with one row per unique posting, standardized city and salary fields, and boolean columns for SQL, Python, Power BI, Tableau, Excel, Azure, AWS, Spark, R, Snowflake, dbt, and GenAI/LLM. Passing `data/bronze` instead automatically selects the newest run. Missing salaries are left blank and raw bronze files are unchanged.
