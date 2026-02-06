#!/usr/bin/env python3
"""Run daily scanner and write analysis results JSON."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core_analysis import AnalysisInput, ComponentScores, analyze_stock, load_analysis_config  # noqa: E402
from src.sanity_layer import (  # noqa: E402
    apply_health_controls,
    compute_health_trend,
    evaluate_daily_sanity,
    load_sanity_config,
    update_health_history,
)


def _load_previous_scores(path: str) -> dict[str, int]:
    if not Path(path).exists():
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        row["ticker"]: int(row["score"])
        for row in payload
        if isinstance(row, dict) and "ticker" in row and "score" in row
    }


def main() -> None:
    scanner_input_path = os.environ.get(
        "SCANNER_INPUT_PATH", "config/daily_scanner_input.example.json"
    )
    scanner_output_path = os.environ.get("SCANNER_OUTPUT_PATH", "artifacts/scanner_output.json")
    analysis_output_path = os.environ.get("ANALYSIS_OUTPUT_PATH", "artifacts/analysis_results.json")
    sanity_report_path = os.environ.get("SANITY_REPORT_PATH", "artifacts/sanity_report.json")
    health_score_path = os.environ.get("HEALTH_SCORE_PATH", "artifacts/health_score.json")
    health_history_path = os.environ.get("HEALTH_HISTORY_PATH", "artifacts/health_history.json")
    previous_analysis_path = os.environ.get("PREVIOUS_ANALYSIS_PATH", "")

    scanner_payload = json.loads(Path(scanner_input_path).read_text(encoding="utf-8"))
    config = load_analysis_config()
    sanity_config = load_sanity_config()

    if os.environ.get("DISABLE_SCORE_CHANGE_CAP", "false").lower() == "true":
        config.setdefault("safety_guards", {}).setdefault("manual_overrides", {})[
            "disable_score_change_cap"
        ] = True

    previous_scores = _load_previous_scores(previous_analysis_path) if previous_analysis_path else {}

    analyses = []
    for stock in scanner_payload.get("stocks", []):
        ticker = stock["ticker"]
        analysis_input = AnalysisInput(
            ticker=ticker,
            mode=stock["mode"],
            current_price=float(stock["current_price"]),
            scores=ComponentScores(**stock["scores"]),
        )
        analyses.append(analyze_stock(analysis_input, config, previous_scores.get(ticker)))

    sanity_report = evaluate_daily_sanity(analyses, sanity_config)
    analyses, behavior_controls = apply_health_controls(analyses, sanity_report, sanity_config)
    report_date = scanner_payload.get("report_date")
    if report_date is None:
        raise ValueError("Scanner payload must include report_date for health history tracking.")
    history = update_health_history(health_history_path, report_date, analyses, sanity_report)
    health_trend = compute_health_trend(history)

    scanner_payload["sanity_report"] = {
        "health_score": sanity_report["health_score"],
        "violation_count": sanity_report["violation_count"],
        "health_guard_active": behavior_controls["health_guard_active"],
        "buy_recommendations_downgraded": behavior_controls["buy_recommendations_downgraded"],
    }
    scanner_payload["health_trend"] = health_trend

    Path(scanner_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(scanner_output_path).write_text(json.dumps(scanner_payload, indent=2), encoding="utf-8")
    Path(analysis_output_path).write_text(json.dumps(analyses, indent=2), encoding="utf-8")
    Path(sanity_report_path).write_text(json.dumps(sanity_report, indent=2), encoding="utf-8")
    Path(health_score_path).write_text(
        json.dumps({"health_score": sanity_report["health_score"]}, indent=2), encoding="utf-8"
    )

    print(f"Scanner input copied to {scanner_output_path}")
    print(f"Analysis results written to {analysis_output_path}")
    print(f"Sanity report written to {sanity_report_path}")
    print(f"Health score written to {health_score_path}")
    print(f"Health history written to {health_history_path}")


if __name__ == "__main__":
    main()
