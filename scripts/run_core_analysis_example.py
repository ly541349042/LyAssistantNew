#!/usr/bin/env python3
"""Run a deterministic example analysis for Phase 2 validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core_analysis import (  # noqa: E402
    AnalysisInput,
    ComponentScores,
    analyze_stock,
    load_analysis_config,
)


def main() -> None:
    config = load_analysis_config()

    sample_input = AnalysisInput(
        ticker="AAPL",
        mode="PRE_EARNINGS",
        current_price=195.20,
        scores=ComponentScores(
            trend_momentum=78,
            fundamentals=81,
            news_sentiment=72,
            earnings_context_pre=75,
            earnings_context_post=60,
            risk_volatility=66,
        ),
    )

    result = analyze_stock(sample_input, config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
