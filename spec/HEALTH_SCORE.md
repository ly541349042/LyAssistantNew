
---

# 📄 `spec/HEALTH_SCORE.md`

```md
# System Health Score Specification

## Purpose
The Health Score represents the *trustworthiness* of the system's daily output,
not expected profitability.

It answers:
"Should the system be trusted today?"

---

## Score Range

- Integer range: 0 – 100
- Higher is healthier
- Neutral baseline: 70

---

## Health Dimensions

Health Score is composed of multiple dimensions:

1. Data Integrity
   - Missing data
   - Stale inputs
   - Inconsistent prices

2. Signal Sanity
   - Excessive BUY or SELL concentration
   - Extreme reversals
   - Indicator contradictions

3. Strategy Behavior
   - Strategy conflicts
   - Overfitting symptoms
   - Disabled strategies still contributing

4. Regime Reliability
   - Regime confidence
   - Regime stability
   - Collapse conditions

5. Evolution Safety
   - Strategy learning frozen when required
   - Failed strategies not reinforced

---

## Adjustment Principles (Hard Rules)

- Health Score must never increase due to market regime.
- Health Score may be capped or degraded due to regime confidence.
- All penalties must be explainable and auditable.

---

## Regime Interaction Rules

| Condition | Effect |
|---|---|
| Regime confidence HIGH | No adjustment |
| Regime confidence MEDIUM | Minor uncertainty penalty |
| Regime confidence LOW | Health Score capped at 70 |
| Regime confidence COLLAPSE | Health Score capped at 50 |

---

## Output Schema (Required)

```json
{
  "health_score": 0,
  "status": "HEALTHY | DEGRADED | CRITICAL",
  "caps_applied": [
    "LOW_REGIME_CONFIDENCE"
  ],
  "violations": [
    "EXCESSIVE_BUY_SIGNALS"
  ],
  "explanations": [
    "Trend strategies degraded due to LOW regime confidence"
  ]
}
```

Status Mapping
Health Score	Status
≥ 85	HEALTHY
70 – 84	DEGRADED
50 – 69	DEGRADED
< 50	CRITICAL
Failure Semantics

If Health Score < 50:

Trading recommendations must be suppressed.

GitHub Actions workflow must fail.

A system alert must still be emitted.

Non-Goals

Health Score does not predict returns.

Health Score does not select stocks.
