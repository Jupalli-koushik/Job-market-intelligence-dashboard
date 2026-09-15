"""Transform timestamped Adzuna bronze JSON into a clean skills table."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

SKILL_PATTERNS = {
    "sql": r"\bsql\b|structured query language",
    "python": r"\bpython\b",
    "power_bi": r"power\s*bi|powerbi",
    "tableau": r"\btableau\b",
    "excel": r"\bexcel\b|ms\s*excel|microsoft\s+excel",
    "azure": r"\bazure\b|microsoft azure",
    "aws": r"\baws\b|amazon web services",
    "spark": r"\bapache spark\b|\bspark\b|pyspark",
    "r": r"(?<![a-z])r(?![a-z])|r programming|r language",
    "snowflake": r"\bsnowflake\b",
    "dbt": r"\bdbt\b|data build tool",
    "genai_llm": r"gen\s*ai|generative ai|large language model|\bllm\b",
}

CITY_ALIASES = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "new delhi": "Delhi",
    "delhi": "Delhi",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "pune": "Pune",
    "kolkata": "Kolkata",
    "noida": "Noida",
    "ahmedabad": "Ahmedabad",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bronze_dir", type=Path, help="Timestamped bronze run directory")
    parser.add_argument("--output-dir", type=Path, default=Path("data/silver"))
    return parser.parse_args()


def find_latest_run(bronze_root: Path) -> Path:
    runs = sorted(path for path in bronze_root.iterdir() if path.is_dir())
    if not runs:
        raise FileNotFoundError(f"No bronze runs found in {bronze_root}")
    return runs[-1]


def as_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def standardize_city(location: Any) -> str:
    if isinstance(location, dict):
        location = location.get("display_name") or location.get("area")
    if not location:
        return "Unknown"
    text = str(location).strip()
    lowered = text.casefold()
    for alias, city in sorted(CITY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return city
    return text.split(",")[0].strip() or "Unknown"


def skill_flags(description: Any) -> dict[str, bool]:
    text = str(description or "")
    return {
        skill: bool(re.search(pattern, text, flags=re.IGNORECASE))
        for skill, pattern in SKILL_PATTERNS.items()
    }


def load_postings(bronze_run: Path) -> list[dict[str, Any]]:
    postings: list[dict[str, Any]] = []
    for path in sorted((bronze_run / "jobs").glob("*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        body = record.get("body", {})
        if not isinstance(body, dict):
            continue
        for posting in body.get("results", []):
            if isinstance(posting, dict):
                postings.append({**posting, "_role_category": path.parent.name})
    return postings


def clean_postings(postings: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for posting in postings:
        description = posting.get("description", "")
        posting_id = posting.get("id")
        if not posting_id:
            posting_id = "|".join(
                str(posting.get(field, ""))
                for field in ("title", "created", "description")
            )
        row = {
            "posting_id": posting_id,
            "role_category": posting.get("_role_category", "unknown"),
            "city": standardize_city(posting.get("location")),
            "company": (posting.get("company") or {}).get("display_name", "Unknown")
            if isinstance(posting.get("company"), dict)
            else posting.get("company") or "Unknown",
            "salary_min": as_number(posting.get("salary_min")),
            "salary_max": as_number(posting.get("salary_max")),
            "posted_date": posting.get("created") or posting.get("posted_date"),
        }
        row.update(skill_flags(description))
        rows.append(row)

    columns = [
        "posting_id", "role_category", "city", "company", "salary_min", "salary_max", "posted_date",
        *SKILL_PATTERNS,
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame
    frame = frame.drop_duplicates(subset=["posting_id"], keep="first")
    frame["posted_date"] = pd.to_datetime(frame["posted_date"], errors="coerce", utc=True)
    frame["salary_min"] = frame["salary_min"].astype("Float64")
    frame["salary_max"] = frame["salary_max"].astype("Float64")
    for skill in SKILL_PATTERNS:
        frame[skill] = frame[skill].astype(bool)
    return frame.reset_index(drop=True)


def main() -> None:
    args = parse_args()
    bronze_run = args.bronze_dir
    if not (bronze_run / "jobs").exists():
        bronze_run = find_latest_run(bronze_run)

    postings = load_postings(bronze_run)
    clean = clean_postings(postings)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output_dir / "jobs_clean.csv", index=False, date_format="%Y-%m-%dT%H:%M:%SZ")
    (args.output_dir / "cleaning_summary.json").write_text(
        json.dumps(
            {
                "bronze_run": str(bronze_run),
                "raw_postings_loaded": len(postings),
                "unique_postings_written": len(clean),
                "skill_columns": list(SKILL_PATTERNS),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Clean table saved to {args.output_dir / 'jobs_clean.csv'} ({len(clean)} postings)")


if __name__ == "__main__":
    main()
