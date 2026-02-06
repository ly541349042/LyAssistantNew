"""Daily sanity evaluation and Health Score controls.

This module is intentionally separate from core scoring logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date
from typing import Dict, List, Optional, Tuple


def load_sanity_config(config_path: str = "config/sanity_rules.json") -> Dict:
    """Load sanity-layer configuration from JSON."""

    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _check_rating_alignment(row: Dict, cfg: Dict) -> List[str]:
    thresholds = cfg["rating_thresholds"]
    score = int(row.get("score", 0))
    rating = str(row.get("rating", "")).upper()

    expected = "SELL"
    if score >= thresholds["buy_min"]:
        expected = "BUY"
    elif score >= thresholds["hold_min"]:
        expected = "HOLD"

    if rating != expected:
        return [f"rating_mismatch: expected {expected} from score {score}, got {rating}"]
    return []


def _check_target_consistency(row: Dict, tolerance_pct: float) -> List[str]:
    current_price = float(row.get("current_price", 0))
    target_price = float(row.get("target_price", 0))
    expected_return_pct = float(row.get("expected_return_pct", 0))

    if current_price <= 0:
        return ["invalid_current_price: must be > 0"]

    implied_return_pct = ((target_price / current_price) - 1.0) * 100.0
    if abs(implied_return_pct - expected_return_pct) > tolerance_pct:
        return [
            "target_return_mismatch: "
            f"implied {implied_return_pct:.2f}% vs expected {expected_return_pct:.2f}%"
        ]
    return []


def evaluate_daily_sanity(analysis_results: List[Dict], config: Dict) -> Dict:
    """Evaluate sanity rule violations for this day and compute Health Score."""

    rules_cfg = config["rules"]
    penalties = config["health_score"]["penalties"]
    violation_limit = config["health_score"]["violation_cap"]

    per_stock: List[Dict] = []
    total_penalty = 0

    for row in analysis_results:
        ticker = row.get("ticker", "UNKNOWN")
        violations: List[str] = []

        violations.extend(_check_rating_alignment(row, rules_cfg))
        violations.extend(_check_target_consistency(row, rules_cfg["target_return_tolerance_pct"]))

        if str(row.get("risk_level", "")).lower() == "high" and str(row.get("rating", "")).upper() == "BUY":
            violations.append("high_risk_buy: high-risk stock should not be BUY without manual review")

        if not row.get("key_reasons"):
            violations.append("missing_key_reasons")

        if not row.get("invalidating_factors"):
            violations.append("missing_invalidating_factors")

        penalty = min(len(violations), violation_limit) * penalties["per_violation"]
        total_penalty += penalty
        per_stock.append({"ticker": ticker, "violations": violations, "penalty": penalty})

    health_score = max(0, 100 - total_penalty)

    return {
        "health_score": health_score,
        "max_health_score": 100,
        "total_penalty": total_penalty,
        "violation_count": sum(len(item["violations"]) for item in per_stock),
        "per_stock": per_stock,
    }


def apply_health_controls(analysis_results: List[Dict], sanity_report: Dict, config: Dict) -> Tuple[List[Dict], Dict]:
    """Apply automatic behavior controls based on Health Score.

    Controls are additive metadata so the base score/rating logic remains unchanged.
    """

    control_cfg = config["behavior_controls"]
    health_score = int(sanity_report["health_score"])

    guard_active = health_score < int(control_cfg["block_buy_below_health_score"])
    adjusted: List[Dict] = []
    adjusted_count = 0

    for row in analysis_results:
        enriched = dict(row)
        enriched["health_score"] = health_score
        enriched["sanity_guard_active"] = guard_active
        enriched["base_rating"] = row.get("rating")

        if guard_active and row.get("rating") == "BUY":
            enriched["rating"] = "HOLD"
            enriched["sanity_adjustment_reason"] = "health_guard_blocked_buy"
            adjusted_count += 1

        adjusted.append(enriched)

    controls = {
        "health_guard_active": guard_active,
        "buy_recommendations_downgraded": adjusted_count,
        "policy": {
            "block_buy_below_health_score": control_cfg["block_buy_below_health_score"],
        },
    }
    return adjusted, controls


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def update_health_history(
    history_path: str,
    report_date: str,
    analysis_results: List[Dict],
    sanity_report: Dict,
) -> List[Dict]:
    """Persist daily Health Score snapshots and return the updated history."""

    path = Path(history_path)
    if path.exists():
        history = json.loads(path.read_text(encoding="utf-8"))
    else:
        history = []

    report_day = _parse_date(report_date)
    entry = {
        "date": report_date,
        "health_score": sanity_report["health_score"],
        "violation_count": sanity_report["violation_count"],
        "stock_count": len(analysis_results),
        "violations_by_ticker": [
            {
                "ticker": item["ticker"],
                "violations": item["violations"],
            }
            for item in sanity_report.get("per_stock", [])
        ],
    }

    history = [row for row in history if row.get("date") != report_date]
    history.append(entry)
    history.sort(key=lambda row: _parse_date(row["date"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return history


def _moving_average(values: List[int], window: int) -> Optional[float]:
    if not values:
        return None
    window_values = values[-window:]
    return round(sum(window_values) / len(window_values), 2)


def _slope(values: List[int]) -> Optional[float]:
    if len(values) < 2:
        return None
    return round((values[-1] - values[0]) / (len(values) - 1), 3)


def _violation_density(history: List[Dict], window: int) -> Optional[float]:
    if not history:
        return None
    window_rows = history[-window:]
    total_violations = sum(int(row.get("violation_count", 0)) for row in window_rows)
    total_stocks = sum(int(row.get("stock_count", 0)) for row in window_rows)
    if total_stocks == 0:
        return 0.0
    return round(total_violations / total_stocks, 3)


def _recovery_time_days(history: List[Dict], threshold: int = 85) -> Optional[int]:
    if not history:
        return None
    latest_date = _parse_date(history[-1]["date"])
    last_healthy: Optional[date] = None
    for row in reversed(history):
        if int(row.get("health_score", 0)) >= threshold:
            last_healthy = _parse_date(row["date"])
            break
    if last_healthy is None:
        return None
    return (latest_date - last_healthy).days


def _root_cause_summary(history: List[Dict], window: int) -> List[Dict]:
    if not history:
        return []
    window_rows = history[-window:]
    counts: Dict[str, int] = {}
    for row in window_rows:
        for item in row.get("violations_by_ticker", []):
            for violation in item.get("violations", []):
                counts[violation] = counts.get(violation, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{"violation": violation, "count": count} for violation, count in ranked[:5]]


def compute_health_trend(history: List[Dict]) -> Dict:
    """Compute moving averages, slope, violation density, and recovery time."""

    scores = [int(row.get("health_score", 0)) for row in history]

    return {
        "moving_average_5d": _moving_average(scores, 5),
        "moving_average_20d": _moving_average(scores, 20),
        "slope_7d": _slope(scores[-7:]),
        "violation_density_5d": _violation_density(history, 5),
        "violation_density_20d": _violation_density(history, 20),
        "recovery_time_days": _recovery_time_days(history, threshold=85),
        "root_cause_summary": _root_cause_summary(history, 20),
    }
