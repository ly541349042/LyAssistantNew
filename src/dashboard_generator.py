"""Dashboard generation for SYSTEM_SPEC.md section 7."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List


def _load_json(path: str) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sort_by_score_desc(analyses: List[Dict]) -> List[Dict]:
    return sorted(analyses, key=lambda row: row["score"], reverse=True)


def generate_dashboard_markdown(report_date: str, scanner_payload: Dict, analysis_results: List[Dict]) -> str:
    """Create a compact, email-friendly one-page markdown dashboard.

    Includes all required section-7 sections:
    - Market Overview
    - Top Opportunities
    - High-Risk Alerts
    - Earnings Watchlist
    - Strategy Evolution Notes
    """

    market_overview = scanner_payload.get("market_overview", {})
    strategy_notes = scanner_payload.get("strategy_evolution_notes", {})
    earnings_watchlist = scanner_payload.get("earnings_watchlist", [])
    sanity_report = scanner_payload.get("sanity_report", {})
    health_trend = scanner_payload.get("health_trend", {})

    ordered = _sort_by_score_desc(analysis_results)
    top_5 = ordered[:5]
    high_risk = [r for r in analysis_results if r.get("risk_level") == "High"]

    lines: List[str] = [
        "# Daily NASDAQ Scanner Dashboard",
        f"Date: {report_date}",
        "",
        "## Market Overview",
        f"- NASDAQ trend bias: {market_overview.get('nasdaq_trend_bias', 'N/A')}",
        f"- Tech sector sentiment: {market_overview.get('tech_sector_sentiment', 'N/A')}",
        "",
        "## Top Opportunities",
    ]

    if sanity_report:
        lines.extend(
            [
                "",
                "## System Health Score",
                f"- Health Score: {sanity_report.get('health_score', 'N/A')}/100",
                f"- Daily sanity violations: {sanity_report.get('violation_count', 'N/A')}",
                f"- Health guard active: {sanity_report.get('health_guard_active', 'N/A')}",
                f"- BUY recommendations downgraded: {sanity_report.get('buy_recommendations_downgraded', 'N/A')}",
            ]
        )

    if health_trend:
        lines.extend(
            [
                "",
                "## Health Trend",
                f"- 5d moving average: {health_trend.get('moving_average_5d', 'N/A')}",
                f"- 20d moving average: {health_trend.get('moving_average_20d', 'N/A')}",
                f"- 7d slope: {health_trend.get('slope_7d', 'N/A')}",
                f"- 5d violation density: {health_trend.get('violation_density_5d', 'N/A')}",
                f"- 20d violation density: {health_trend.get('violation_density_20d', 'N/A')}",
                f"- Recovery time (days): {health_trend.get('recovery_time_days', 'N/A')}",
            ]
        )
        root_causes = health_trend.get("root_cause_summary", [])
        if root_causes:
            lines.append("- Top root causes:")
            for item in root_causes:
                lines.append(f"  - {item.get('violation', 'N/A')}: {item.get('count', 'N/A')}")

    if top_5:
        for row in top_5:
            lines.append(
                f"- {row['ticker']}: score {row['score']}, rating {row['rating']}, target ${row['target_price']}, expected return {row['expected_return_pct']}%"
            )
    else:
        lines.append("- No opportunities available.")

    lines.extend(["", "## High-Risk Alerts"])
    if high_risk:
        for row in high_risk:
            lines.append(
                f"- {row['ticker']}: score {row['score']}, rating {row['rating']}, risk {row['risk_level']}"
            )
    else:
        lines.append("- No high-risk alerts detected.")

    lines.extend(["", "## Earnings Watchlist"])
    if earnings_watchlist:
        for item in earnings_watchlist:
            lines.append(
                f"- {item.get('ticker', 'N/A')}: earnings date {item.get('earnings_date', 'N/A')} ({item.get('window', 'N/A')})"
            )
    else:
        lines.append("- No earnings watchlist entries provided.")

    lines.extend(
        [
            "",
            "## Strategy Evolution Notes",
            f"- What worked recently: {strategy_notes.get('worked', 'N/A')}",
            f"- What failed: {strategy_notes.get('failed', 'N/A')}",
        ]
    )

    return "\n".join(lines) + "\n"


def generate_summary_text(analysis_results: List[Dict]) -> str:
    """Generate concise summary for email body."""

    count = len(analysis_results)
    if count == 0:
        return "No stocks analyzed for this run."

    ordered = _sort_by_score_desc(analysis_results)
    top = ordered[0]
    return (
        f"Analyzed {count} stocks. "
        f"Top pick: {top['ticker']} (score {top['score']}, rating {top['rating']}, "
        f"expected return {top['expected_return_pct']}%)."
    )


def build_daily_dashboard(
    scanner_input_path: str,
    analysis_results_path: str,
    dashboard_output_path: str,
    summary_output_path: str,
) -> None:
    """Read scanner + analysis files and write dashboard artifacts."""

    scanner_payload = _load_json(scanner_input_path)
    analysis_results = _load_json(analysis_results_path)

    report_date = scanner_payload.get("report_date", date.today().isoformat())

    markdown = generate_dashboard_markdown(report_date, scanner_payload, analysis_results)
    summary = generate_summary_text(analysis_results)

    Path(dashboard_output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(dashboard_output_path).write_text(markdown, encoding="utf-8")
    Path(summary_output_path).write_text(summary + "\n", encoding="utf-8")
