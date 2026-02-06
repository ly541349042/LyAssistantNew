
---

# 📄 `spec/STRATEGY_MATRIX.md`

```md
# Strategy × Regime × Confidence Matrix Specification

## Purpose
Determine whether each strategy is allowed to influence system decisions
based on market environment suitability.

This system prioritizes *environmental fitness* over raw performance.

---

## Strategy Declaration (Required)

Each strategy must declare metadata:

```json
{
  "strategy_id": "example_strategy",
  "preferred_regimes": ["BULL", "SIDEWAYS"],
  "min_confidence": "MEDIUM",
  "risk_profile": "AGGRESSIVE | NEUTRAL | DEFENSIVE",
  "fallback_mode": "DISABLED | DEGRADED"
}
```

Strategies without a declaration are disabled by default.

Global Hard Rules

If regime confidence == COLLAPSE:

All non-defensive strategies are DISABLED.

If regime not in preferred_regimes:

Strategy is DISABLED.

If confidence < min_confidence:

Strategy is DISABLED.

These rules override all matrix entries.

Strategy States

ENABLED : Full participation

DEGRADED : Reduced weight and influence

DISABLED : No influence on outputs or Health Score

Weight Semantics

Weight ∈ [0.0, 1.0]

DEGRADED strategies must have weight < 0.5

DISABLED strategies must have weight = 0.0

Example Matrix (Conceptual)
Trend-Following Strategy
Regime	Confidence	State	Weight
BULL	HIGH	ENABLED	1.0
BULL	MEDIUM	ENABLED	0.7
BULL	LOW	DEGRADED	0.3
ANY	COLLAPSE	DISABLED	0.0
SIDEWAYS	ANY	DISABLED	0.0
Mean-Reversion Strategy
Regime	Confidence	State	Weight
SIDEWAYS	HIGH	ENABLED	1.0
SIDEWAYS	MEDIUM	ENABLED	0.8
SIDEWAYS	LOW	DEGRADED	0.4
BULL	HIGH	DEGRADED	0.3
BEAR	HIGH	DEGRADED	0.3
Output Schema (Required)
{
  "strategy_id": "example_strategy",
  "enabled": true,
  "state": "DEGRADED",
  "weight": 0.3,
  "reasons": [
    "LOW regime confidence",
    "Weight reduced by matrix rule"
  ]
}

Health Score Interaction

DISABLED strategies must not contribute to Health Score.

DEGRADED strategies must contribute proportionally by weight.

Strategy conflicts must be surfaced as Health violations.

Non-Goals

This matrix does not decide BUY / SELL.

This matrix does not rank strategies by profitability.
