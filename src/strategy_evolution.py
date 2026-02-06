"""Strategy self-evolution logic with transparent change reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.performance_tracker import load_evolution_config, load_outcomes, summarize_strategy_performance


@dataclass(frozen=True)
class WeightChange:
    strategy_id: str
    weight_key: str
    old_weight: int
    new_weight: int
    reason: str


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _round_preserve_total(values: Dict[str, float], total: int = 100) -> Dict[str, int]:
    floors = {k: int(v) for k, v in values.items()}
    remainder = total - sum(floors.values())

    fractions = sorted(
        ((k, values[k] - floors[k]) for k in values),
        key=lambda item: (-item[1], item[0]),
    )

    result = dict(floors)
    if not fractions:
        return result

    for index in range(max(0, remainder)):
        result[fractions[index % len(fractions)][0]] += 1
    return result


def _days_since(last_date: str, current_date: str) -> int:
    return (date.fromisoformat(current_date) - date.fromisoformat(last_date)).days


def _read_evolution_state(state_path: str) -> Dict[str, Any]:
    if not Path(state_path).exists():
        return {}
    return json.loads(Path(state_path).read_text(encoding="utf-8"))


def _write_evolution_state(state_path: str, state: Dict[str, Any]) -> None:
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    Path(state_path).write_text(json.dumps(state, indent=2), encoding="utf-8")


def _cooldown_active(evolution_config: Dict[str, Any], state: Dict[str, Any], current_date: str) -> bool:
    guard_cfg = evolution_config.get("safety_guards", {})
    override_cfg = guard_cfg.get("manual_overrides", {})
    if override_cfg.get("disable_evolution_cooldown", False):
        return False

    cooldown_days = int(guard_cfg.get("cooldown_days", 0))
    if cooldown_days <= 0:
        return False

    last_date = state.get("last_weight_update_date")
    if not last_date:
        return False

    return _days_since(last_date, current_date) < cooldown_days


def evolve_weights(
    current_weights: Dict[str, int],
    performance_summary: Dict[str, Dict[str, Any]],
    evolution_config: Dict[str, Any],
) -> Tuple[Dict[str, int], List[WeightChange]]:
    mapping = evolution_config["strategy_to_weight_key"]
    adjust_cfg = evolution_config["weight_adjustment"]
    step = adjust_cfg["step_pct"]

    # TODO(SPEC-CLARITY): Spec defines degradation criteria explicitly but does not
    # define outperformance criteria. We use non-degraded status as outperforming proxy.
    degraded = {sid for sid, row in performance_summary.items() if row["degraded"]}
    outperforming = {sid for sid, row in performance_summary.items() if not row["degraded"]}

    candidate = {k: float(v) for k, v in current_weights.items()}
    changes: List[WeightChange] = []

    total_shift = 0
    max_shift = adjust_cfg["max_total_adjustment_pct"]

    for strategy_id in sorted(mapping):
        if total_shift >= max_shift:
            break

        weight_key = mapping[strategy_id]
        old_weight = int(candidate[weight_key])
        if strategy_id in degraded:
            new_weight = max(adjust_cfg["min_weight"], old_weight - step)
            reason = "degraded performance detected"
        elif strategy_id in outperforming:
            new_weight = min(adjust_cfg["max_weight"], old_weight + step)
            reason = "relative outperformance detected"
        else:
            new_weight = old_weight
            reason = "insufficient data"

        if new_weight != old_weight:
            candidate[weight_key] = float(new_weight)
            total_shift += abs(new_weight - old_weight)
            changes.append(
                WeightChange(
                    strategy_id=strategy_id,
                    weight_key=weight_key,
                    old_weight=old_weight,
                    new_weight=new_weight,
                    reason=reason,
                )
            )

    normalized = _round_preserve_total(candidate, total=100)
    return normalized, changes


def generate_evolution_report(
    performance_summary: Dict[str, Dict[str, Any]],
    old_weights: Dict[str, int],
    new_weights: Dict[str, int],
    changes: List[WeightChange],
    cooldown_active: bool,
) -> Dict[str, Any]:
    worked = [sid for sid, row in sorted(performance_summary.items()) if not row["degraded"]]
    failed = [sid for sid, row in sorted(performance_summary.items()) if row["degraded"]]

    return {
        "strategy_evolution_report": {
            "cooldown_active": cooldown_active,
            "what_worked_recently": worked,
            "what_failed": failed,
            "old_weights": old_weights,
            "new_weights": new_weights,
            "applied_changes": [
                {
                    "strategy_id": item.strategy_id,
                    "weight_key": item.weight_key,
                    "old_weight": item.old_weight,
                    "new_weight": item.new_weight,
                    "reason": item.reason,
                }
                for item in changes
            ],
            "performance_details": performance_summary,
        }
    }


def run_strategy_evolution(
    analysis_config_path: str,
    evolution_config_path: str,
    outcomes_path: str,
    report_output_path: str,
    state_path: str,
    current_date: str,
) -> Dict[str, Any]:
    analysis_config = _load_json(analysis_config_path)
    old_weights = analysis_config["weights"]

    evolution_config = load_evolution_config(evolution_config_path)
    outcomes = load_outcomes(outcomes_path)
    performance_summary = summarize_strategy_performance(outcomes, evolution_config)

    guard_cfg = evolution_config.get("safety_guards", {})
    override_cfg = guard_cfg.get("manual_overrides", {})

    state = _read_evolution_state(state_path)
    cooldown_active = _cooldown_active(evolution_config, state, current_date)

    if override_cfg.get("disable_weight_updates", False) or cooldown_active:
        new_weights = old_weights
        changes: List[WeightChange] = []
    else:
        new_weights, changes = evolve_weights(old_weights, performance_summary, evolution_config)
        if changes:
            _write_evolution_state(state_path, {"last_weight_update_date": current_date})

    report = generate_evolution_report(
        performance_summary,
        old_weights,
        new_weights,
        changes,
        cooldown_active,
    )

    Path(report_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
