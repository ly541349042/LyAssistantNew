#!/usr/bin/env python3
"""Run strategy performance tracking and evolution report generation."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.strategy_evolution import run_strategy_evolution  # noqa: E402


if __name__ == "__main__":
    analysis_config_path = os.environ.get("ANALYSIS_CONFIG_PATH", "config/analysis_config.json")
    evolution_config_path = os.environ.get("EVOLUTION_CONFIG_PATH", "config/evolution_config.json")
    outcomes_path = os.environ.get("OUTCOMES_PATH", "examples/strategy_outcomes.example.json")
    report_output_path = os.environ.get(
        "STRATEGY_EVOLUTION_REPORT_PATH", "examples/strategy_evolution_report.example.json"
    )
    state_path = os.environ.get("STRATEGY_EVOLUTION_STATE_PATH", "artifacts/strategy_evolution_state.json")
    current_date = os.environ.get("CURRENT_DATE", date.today().isoformat())

    run_strategy_evolution(
        analysis_config_path=analysis_config_path,
        evolution_config_path=evolution_config_path,
        outcomes_path=outcomes_path,
        report_output_path=report_output_path,
        state_path=state_path,
        current_date=current_date,
    )
    print(f"Strategy evolution report written to {report_output_path}")
