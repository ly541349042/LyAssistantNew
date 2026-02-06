"""Core deterministic stock analysis engine for SYSTEM_SPEC.md Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

Mode = Literal["PRE_EARNINGS", "POST_EARNINGS"]


@dataclass(frozen=True)
class ComponentScores:
    """Normalized component scores (0-100) for composite scoring."""

    trend_momentum: float
    fundamentals: float
    news_sentiment: float
    earnings_context_pre: float
    earnings_context_post: float
    risk_volatility: float


@dataclass(frozen=True)
class AnalysisInput:
    """Input model for deterministic single-stock analysis."""

    ticker: str
    mode: Mode
    current_price: float
    scores: ComponentScores


def load_analysis_config(config_path: str = "config/analysis_config.json") -> Dict:
    """Load engine configuration from external JSON file."""

    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _validate_config(config: Dict) -> None:
    weights = config["weights"]
    weight_total = sum(weights.values())
    if weight_total != 100:
        raise ValueError(f"Weights must sum to 100, found {weight_total}")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _selected_earnings_score(mode: Mode, scores: ComponentScores) -> float:
    if mode == "PRE_EARNINGS":
        return scores.earnings_context_pre
    return scores.earnings_context_post


def calculate_score_breakdown(analysis_input: AnalysisInput, config: Dict) -> Dict[str, float]:
    bounds = config["score_bounds"]
    weights = config["weights"]

    earnings_score = _selected_earnings_score(analysis_input.mode, analysis_input.scores)

    raw_components = {
        "trend_momentum": analysis_input.scores.trend_momentum,
        "fundamentals": analysis_input.scores.fundamentals,
        "news_sentiment": analysis_input.scores.news_sentiment,
        "earnings_context": earnings_score,
        "risk_volatility": analysis_input.scores.risk_volatility,
    }

    clamped_components = {
        key: _clamp(value, bounds["min"], bounds["max"])
        for key, value in raw_components.items()
    }

    return {
        key: (clamped_components[key] * weights[key]) / 100.0
        for key in clamped_components
    }


def calculate_composite_score(score_breakdown: Dict[str, float], config: Dict) -> int:
    bounds = config["score_bounds"]
    score = round(sum(score_breakdown.values()))
    return int(_clamp(score, bounds["min"], bounds["max"]))


def apply_daily_score_change_cap(
    score: int,
    previous_score: Optional[int],
    config: Dict,
) -> int:
    """Cap daily score drift unless manually overridden."""

    if previous_score is None:
        return score

    guard_cfg = config.get("safety_guards", {})
    override_cfg = guard_cfg.get("manual_overrides", {})
    if override_cfg.get("disable_score_change_cap", False):
        return score

    max_change = guard_cfg.get("max_daily_score_change")
    if max_change is None:
        return score

    lower = int(previous_score - max_change)
    upper = int(previous_score + max_change)
    return int(_clamp(score, lower, upper))


def map_score_to_rating(score: int, config: Dict) -> str:
    thresholds = config["rating_thresholds"]
    if score >= thresholds["buy_min"]:
        return "BUY"
    if score >= thresholds["hold_min"]:
        return "HOLD"
    return "SELL"


def estimate_target_price(current_price: float, score: int, config: Dict) -> Tuple[float, float]:
    target_cfg = config["target_price"]
    delta_points = score - target_cfg["neutral_score"]

    expected_return_pct = delta_points * target_cfg["return_per_score_point"]
    expected_return_pct = _clamp(
        expected_return_pct,
        target_cfg["min_return_pct"],
        target_cfg["max_return_pct"],
    )

    target_price = current_price * (1 + expected_return_pct / 100.0)
    return round(target_price, 2), round(expected_return_pct, 1)


def classify_risk_level(risk_volatility_score: float, config: Dict) -> str:
    thresholds = config["risk_level_thresholds"]
    if risk_volatility_score >= thresholds["low_risk_min"]:
        return "Low"
    if risk_volatility_score >= thresholds["medium_risk_min"]:
        return "Medium"
    return "High"


def _component_label(component_key: str) -> str:
    return component_key.replace("_", " ").title()


def build_explanations(score_breakdown: Dict[str, float], config: Dict) -> Tuple[List[str], List[str]]:
    reason_cfg = config["reason_generation"]
    ordered = sorted(score_breakdown.items(), key=lambda item: item[1], reverse=True)

    top_positive = ordered[: reason_cfg["top_positive_reasons"]]
    top_negative = sorted(score_breakdown.items(), key=lambda item: item[1])[
        : reason_cfg["top_negative_factors"]
    ]

    key_reasons = [
        f"{_component_label(component)} contributed +{contribution:.2f} points"
        for component, contribution in top_positive
    ]
    invalidating_factors = [
        f"Weak {_component_label(component)} contribution ({contribution:.2f} points)"
        for component, contribution in top_negative
    ]
    return key_reasons, invalidating_factors


def analyze_stock(
    analysis_input: AnalysisInput,
    config: Dict,
    previous_score: Optional[int] = None,
) -> Dict:
    score_breakdown = calculate_score_breakdown(analysis_input, config)
    uncapped_score = calculate_composite_score(score_breakdown, config)
    score = apply_daily_score_change_cap(uncapped_score, previous_score, config)
    rating = map_score_to_rating(score, config)
    target_price, expected_return_pct = estimate_target_price(
        analysis_input.current_price, score, config
    )
    key_reasons, invalidating_factors = build_explanations(score_breakdown, config)

    result = {
        "ticker": analysis_input.ticker,
        "mode": analysis_input.mode,
        "score": score,
        "rating": rating,
        "current_price": round(analysis_input.current_price, 2),
        "target_price": target_price,
        "expected_return_pct": expected_return_pct,
        "risk_level": classify_risk_level(analysis_input.scores.risk_volatility, config),
        "key_reasons": key_reasons,
        "invalidating_factors": invalidating_factors,
    }
    if previous_score is not None:
        result["previous_score"] = previous_score
        result["score_before_daily_cap"] = uncapped_score
    return result
