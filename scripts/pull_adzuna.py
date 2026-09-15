"""Pull raw Adzuna India job-market data for the dashboard bronze layer."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
DEFAULT_ROLES = {
    "data_analyst": ["data analyst", "analyst", "BI"],
    "data_engineer": ["data engineer", "data"],
    "data_scientist": ["data scientist", "data science"],
    "ai_engineer": ["AI engineer", "machine learning engineer", "AI"],
    "business_analyst": ["business analyst", "analyst"],
}


def get_required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def request_json(
    session: requests.Session,
    endpoint: str,
    params: dict[str, Any],
    output_path: Path,
    timeout: int,
) -> None:
    url = f"{BASE_URL}/{endpoint}"
    request_record: dict[str, Any] = {
        "url": url,
        "params": {key: value for key, value in params.items() if key not in {"app_id", "app_key"}},
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        response = session.get(url, params=params, timeout=timeout)
        request_record["status_code"] = response.status_code
        request_record["response_url"] = response.url
        try:
            request_record["body"] = response.json()
        except ValueError:
            request_record["body"] = {"raw_text": response.text}
    except requests.RequestException as error:
        request_record["error"] = {"type": type(error).__name__, "message": str(error)}

    output_path.write_text(json.dumps(request_record, indent=2), encoding="utf-8")


def pull_role(
    session: requests.Session,
    role_name: str,
    search_terms: list[str],
    output_dir: Path,
    app_id: str,
    app_key: str,
    max_pages: int,
    results_per_page: int,
    timeout: int,
    delay_seconds: float,
) -> None:
    role_dir = output_dir / "jobs" / role_name
    role_dir.mkdir(parents=True, exist_ok=True)
    common_params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "content-type": "application/json",
        "where": "India",
    }

    for term_index, search_term in enumerate(search_terms, start=1):
        for page in range(1, max_pages + 1):
            params = {**common_params, "what": search_term}
            request_json(
                session,
                f"in/search/{page}",
                params,
                role_dir / f"term_{term_index:02d}_page_{page:03d}.json",
                timeout,
            )
            time.sleep(delay_seconds)

    aggregate_dir = output_dir / "aggregates" / role_name
    aggregate_dir.mkdir(parents=True, exist_ok=True)
    for endpoint, filename in (
        ("history", "salary_history.json"),
        ("top_companies", "top_companies.json"),
    ):
        request_json(
            session,
            f"in/{endpoint}",
            {**common_params, "what": search_terms[0]},
            aggregate_dir / filename,
            timeout,
        )
        time.sleep(delay_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/bronze"))
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--results-per-page", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_pages < 1 or args.results_per_page < 1:
        raise ValueError("--max-pages and --results-per-page must be positive")

    app_id = get_required_environment("ADZUNA_APP_ID")
    app_key = get_required_environment("ADZUNA_APP_KEY")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_config.json").write_text(
        json.dumps(
            {
                "source": "Adzuna Jobs API",
                "country": "in",
                "run_id": run_id,
                "roles": DEFAULT_ROLES,
                "max_pages": args.max_pages,
                "results_per_page": args.results_per_page,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with requests.Session() as session:
        for role_name, search_terms in DEFAULT_ROLES.items():
            pull_role(
                session,
                role_name,
                search_terms,
                output_dir,
                app_id,
                app_key,
                args.max_pages,
                args.results_per_page,
                args.timeout,
                args.delay_seconds,
            )

    print(f"Raw Adzuna pull saved to {output_dir}")


if __name__ == "__main__":
    main()
