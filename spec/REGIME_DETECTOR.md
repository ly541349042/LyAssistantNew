# Market Regime Detector Specification

## Purpose
Detect the current overall market regime for NASDAQ-focused analysis and
quantify the confidence of that detection.

This module is descriptive, not predictive.
It must never directly generate trading signals.

---

## Supported Market Regimes

- BULL      : Sustained upward trend with supportive breadth
- BEAR      : Sustained downward trend with risk-off characteristics
- SIDEWAYS : Range-bound or mixed signals without clear trend

---

## Inputs (Abstract Indicators)

The detector may consume normalized indicators in the following categories:

1. Trend Indicators
   - Index moving averages
   - Trend slope / direction

2. Volatility Indicators
   - VIX level and short-term change
   - Realized volatility

3. Breadth Indicators
   - Advance/decline ratios
   - Percentage of stocks above key averages

Exact indicator implementation is out of scope of this spec.

---

## Output Schema (Required)

The detector must output a machine-readable JSON object:

```json
{
  "regime": "BULL | BEAR | SIDEWAYS",
  "confidence": 0.0,
  "confidence_level": "HIGH | MEDIUM | LOW | COLLAPSE",
  "signals": {
    "trend": "bullish | bearish | neutral",
    "volatility": "low | elevated | high",
    "breadth": "strong | weak | neutral"
  }
}
```

Confidence Calculation (Conceptual)

Confidence represents regime reliability, not model certainty.

It must be derived from:

Signal agreement

Temporal stability

Volatility shock penalties

Confidence must be clamped to [0.0, 1.0].

Confidence Levels
Level	Range
HIGH	≥ 0.75
MEDIUM	0.55 – 0.74
LOW	0.35 – 0.54
COLLAPSE	< 0.35
Collapse Semantics (Hard Rule)

If confidence_level == COLLAPSE:

The regime is considered unreliable.

Downstream systems must not rely on regime-based adjustments.

The condition must be explicitly surfaced (no silent handling).

Non-Goals

This module must not emit BUY / SELL / HOLD signals.

This module must not modify Health Score directly.
