# Job Market Intelligence Dashboard

This project builds a data pipeline for India’s job market using the Adzuna Jobs API, then cleans and enriches the raw postings to analyze role trends and skill demand across data-focused jobs.


![Project demo](Screenshots%20and%20Recordings/final%20recording.gif)



## Project goal

Collect live job postings for high-demand data roles in India, normalize the records, and extract technology and analytics skill mentions from raw job descriptions. The final silver layer is designed for dashboarding and market-analysis workflows.

## Current pipeline status

The repository currently contains a bronze run and a silver output generated from it:

- Bronze run: `data/bronze/20260827T062819Z`
- Raw postings loaded: 1,800
- Unique postings written: 1,285
- Skill columns included: SQL, Python, Power BI, Tableau, Excel, Azure, AWS, Spark, R, Snowflake, dbt, GenAI/LLM

## Architecture

- `scripts/pull_adzuna.py` pulls raw Adzuna results into a time-stamped bronze dataset
- `scripts/clean_jobs.py` standardizes postings and extracts skill flags into a clean table
- `data/bronze/` stores raw API responses and per-role aggregate metadata
- `data/silver/jobs_clean.csv` stores the cleaned deduplicated output table
- `data/silver/cleaning_summary.json` stores the run summary

## Setup

Requirements:

- Python 3.10+
- A valid Adzuna account with `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
$env:ADZUNA_APP_ID = "your_app_id"
$env:ADZUNA_APP_KEY = "your_app_key"
```

## 1) Pull raw job data

```powershell
py scripts\pull_adzuna.py
```

This script searches predefined roles and related terms, saves each API response under a timestamped folder in `data/bronze/`, and stores salary-history and top-company summaries for each role.

Optional arguments:

```powershell
py scripts\pull_adzuna.py --max-pages 3 --results-per-page 50 --delay-seconds 1
```

## 2) Clean and enrich the postings

```powershell
py scripts\clean_jobs.py data\bronze\20260827T062819Z
```

The cleaner does the following:

- reads the bronze job JSON files
- deduplicates postings by posting ID
- standardizes city names
- converts salary values to numeric fields
- flags skill mentions using regex-based matching for common data and AI tools
- writes both the cleaned CSV and a summary JSON file

## Output files

`data/silver/jobs_clean.csv`
- One row per unique job posting
- City, company, posted date, and salary columns
- Boolean skill columns for `sql`, `python`, `power_bi`, `tableau`, `excel`, `azure`, `aws`, `spark`, `r`, `snowflake`, `dbt`, and `genai_llm`

`data/silver/cleaning_summary.json`
- Stores metadata for the bronze run and final clean-row count

## Notes

- Raw bronze files are intentionally preserved for traceability.
- Missing salary values remain blank.
- The dataset is focused on India and roles such as data analyst, data engineer, data scientist, AI engineer, and business analyst.

## Repository structure

```text
Job market intelligence/
├── data/
│   ├── bronze/
│   └── silver/
├── notebooks/
├── scripts/
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

## Example use cases

This project supports:

- job-market trend analysis by city and role
- skill-demand analysis across India
- salary benchmark comparisons for data roles
- dashboarding and reporting in Power BI or Tableau
