SYSTEM_SPEC.md
Automated NASDAQ Tech Stock Analysis & Daily Scanner System
1. System Objective

Build a fully automated, daily NASDAQ tech stock analysis system that:

Runs every trading day before NASDAQ opens

Scans a predefined universe of NASDAQ-listed technology stocks

Generates a 1-page trading dashboard

Assigns each stock a numerical score (0–100)

Produces Buy / Hold / Sell suggestions

Provides target price & rationale

Supports pre-earnings vs post-earnings analysis modes

Learns from historical performance and self-evolves strategies

Delivers results via email

Exposes a manual API endpoint for on-demand single-stock analysis

This system is designed to be deployed via GitHub Actions + Web backend, with Codex implementing the code based on this specification.

2. Operating Modes
2.1 Daily Scanner Mode (Automatic)

Triggered by GitHub Actions on a cron schedule

Runs before NASDAQ market open

Analyzes all configured stocks

Outputs:

Dashboard summary

Per-stock analysis

Strategy notes

Sends email report

2.2 Manual Analysis Mode (On-Demand)

User provides:

Stock ticker

Current price (optional override)

Expected profit strategy

System returns:

Score (0–100)

Buy / Hold / Sell

Target price

Confidence explanation

2.3 Earnings Context Mode

Each analysis must explicitly run in one of:

PRE_EARNINGS

Focus on expectations, momentum, sentiment, risk

POST_EARNINGS

Focus on results vs expectations, guidance, reaction quality

Mode selection rules:

Automatic scanner infers mode from earnings calendar

Manual mode allows user override

3. Stock Universe
3.1 Default Scope

NASDAQ-listed technology-heavy stocks, including:

Large-cap (e.g. AAPL, MSFT, NVDA, AMZN, META)

Mid-cap growth tech

AI / Semiconductor / Cloud / Software companies

3.2 Configuration

Stock universe must be configurable via file:

/config/universe.json

4. Input Data Model
4.1 Market Data

For each stock:

Ticker

Current price

Recent price action (trend, volatility)

Volume changes

Support / resistance zones

4.2 Fundamental Signals

Revenue growth

Earnings growth

Margins

Guidance direction (if available)

4.3 News & Sentiment

Recent news headlines

Earnings-related news

Analyst upgrades / downgrades

Macro tech-sector signals

4.4 Strategy Inputs (User-Provided or Default)

Risk tolerance (low / medium / high)

Time horizon (short / swing / long)

Expected profit target (% or price)

5. Scoring System (0–100)

Each stock receives a composite score based on weighted factors:

Category	Weight
Trend & Momentum	25%
Fundamentals	25%
News & Sentiment	20%
Earnings Context	15%
Risk / Volatility	15%
Score Interpretation

80–100 → Strong Buy

65–79 → Buy

45–64 → Hold / Watch

30–44 → Sell / Reduce

0–29 → Strong Sell

6. Output Schema (Per Stock)

Each stock analysis must output:

{
  "ticker": "AAPL",
  "mode": "PRE_EARNINGS",
  "score": 82,
  "rating": "BUY",
  "current_price": 195.20,
  "target_price": 215.00,
  "expected_return_pct": 10.1,
  "risk_level": "Medium",
  "key_reasons": [
    "Positive earnings momentum",
    "Strong institutional buying",
    "Bullish pre-earnings sentiment"
  ],
  "invalidating_factors": [
    "Macro tech selloff",
    "Weak guidance"
  ]
}

7. Daily Dashboard (1-Page)

The daily dashboard must include:

Market Overview

NASDAQ trend bias

Tech sector sentiment

Top Opportunities

Top 5 highest-scoring stocks

High-Risk Alerts

Stocks with elevated volatility or downside risk

Earnings Watchlist

Stocks entering earnings window

Strategy Evolution Notes

What worked recently

What failed

8. Self-Evolution & Strategy Learning
8.1 Performance Tracking

For each recommendation:

Track outcome after:

+1 day

+5 days

+20 days

8.2 Failure Detection

A strategy is considered degraded if:

Win rate < 40% over last N trades

Or average return < benchmark

8.3 Adaptation Rules

When degradation detected:

Reduce weight of failing signals

Increase weight of outperforming signals

Log changes in evolution report

All changes must be transparent and auditable.

9. Automation & Delivery
9.1 Scheduling

GitHub Actions cron job

Runs every weekday

Time: configurable (default pre-market US time)

9.2 Email Delivery

Send daily dashboard via email

Email must include:

Summary

Top picks

Link to full dashboard

10. Deployment Requirements

Web-based backend (framework agnostic)

REST API for manual analysis

Configurable environment variables

GitHub Actions for automation

No hardcoded secrets

11. Non-Goals & Disclaimers

This system does not execute trades

This system provides decision support, not financial advice

Human judgment remains required

12. Success Criteria

This system is successful if:

Daily report is delivered reliably

Scores are consistent and explainable

Strategy evolves based on outcomes

Manual analysis works on demand

Codex can extend the system without ambiguity

End of Specification
