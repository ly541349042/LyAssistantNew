"""Performance tracking for +1d/+5d/+20d recommendation outcomes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List


@dataclass(frozen=True)
class OutcomeRecord:
    """Single realized recommendation outcome for one strategy signal."""

    strategy_id: str
    timestamp: str
    returns_pct: Dict[str, float]


def load_evolution_config(config_path: str = "config/evolution_config.json") -> Dict[str, Any]:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def load_outcomes(outcomes_path: str) -> List[OutcomeRecord]:
    data = json.loads(Path(outcomes_path).read_text(encoding="utf-8"))
    records: List[OutcomeRecord] = []
    for row in data:
        records.append(
            OutcomeRecord(
                strategy_id=row["strategy_id"],
                timestamp=row["timestamp"],
                returns_pct={k: float(v) for k, v in row["returns_pct"].items()},
            )
        )
    return records


def summarize_strategy_performance(
    outcomes: List[OutcomeRecord],
    config: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Summarize per-strategy performance and degradation flags."""

    degradation_cfg = config["degradation"]
    horizons = config["tracking_horizons"]
    grouped: Dict[str, List[OutcomeRecord]] = defaultdict(list)

    for record in outcomes:
        grouped[record.strategy_id].append(record)

    summary: Dict[str, Dict[str, Any]] = {}
    for strategy_id in sorted(grouped):
        ordered = sorted(grouped[strategy_id], key=lambda r: r.timestamp)
        windowed = ordered[-degradation_cfg["window_size"] :]

        horizon_metrics: Dict[str, Dict[str, float]] = {}
        degraded_reasons: List[str] = []

        for horizon in horizons:
            values = [item.returns_pct[horizon] for item in windowed if horizon in item.returns_pct]
            if len(values) < degradation_cfg["min_trades_required"]:
                horizon_metrics[horizon] = {
                    "trade_count": len(values),
                    "win_rate": 0.0,
                    "avg_return_pct": 0.0,
                    "benchmark_return_pct": degradation_cfg["benchmark_return_by_horizon"][horizon],
                }
                continue

            wins = sum(1 for value in values if value > 0)
            win_rate = wins / len(values)
            avg_return = mean(values)
            benchmark = degradation_cfg["benchmark_return_by_horizon"][horizon]

            horizon_metrics[horizon] = {
                "trade_count": len(values),
                "win_rate": round(win_rate, 4),
                "avg_return_pct": round(avg_return, 4),
                "benchmark_return_pct": benchmark,
            }

            if win_rate < degradation_cfg["win_rate_threshold"]:
                degraded_reasons.append(
                    f"{horizon} win_rate {win_rate:.2%} below threshold {degradation_cfg['win_rate_threshold']:.2%}"
                )
            if avg_return < benchmark:
                degraded_reasons.append(
                    f"{horizon} avg_return {avg_return:.2f}% below benchmark {benchmark:.2f}%"
                )

        summary[strategy_id] = {
            "strategy_id": strategy_id,
            "metrics": horizon_metrics,
            "degraded": len(degraded_reasons) > 0,
            "degraded_reasons": degraded_reasons,
        }

    return summary
