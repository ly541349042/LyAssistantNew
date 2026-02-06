#!/usr/bin/env python3
"""Generate daily dashboard artifacts from scanner and analysis outputs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard_generator import build_daily_dashboard  # noqa: E402


def main() -> None:
    scanner_input_path = os.environ.get("SCANNER_OUTPUT_PATH", "artifacts/scanner_output.json")
    analysis_results_path = os.environ.get("ANALYSIS_OUTPUT_PATH", "artifacts/analysis_results.json")
    dashboard_output_path = os.environ.get("DASHBOARD_OUTPUT_PATH", "artifacts/daily_dashboard.md")
    summary_output_path = os.environ.get("DASHBOARD_SUMMARY_PATH", "artifacts/daily_summary.txt")

    build_daily_dashboard(
        scanner_input_path=scanner_input_path,
        analysis_results_path=analysis_results_path,
        dashboard_output_path=dashboard_output_path,
        summary_output_path=summary_output_path,
    )

    print(f"Dashboard written to {dashboard_output_path}")
    print(f"Summary written to {summary_output_path}")


if __name__ == "__main__":
    main()
