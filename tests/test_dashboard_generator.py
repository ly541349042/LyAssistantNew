import json
import tempfile
import unittest
from pathlib import Path

from src.dashboard_generator import build_daily_dashboard


class DashboardGeneratorTests(unittest.TestCase):
    def test_dashboard_includes_all_required_sections(self) -> None:
        scanner_payload = {
            "report_date": "2026-01-15",
            "market_overview": {
                "nasdaq_trend_bias": "Bullish",
                "tech_sector_sentiment": "Positive",
            },
            "earnings_watchlist": [{"ticker": "AAPL", "earnings_date": "2026-01-20", "window": "approaching"}],
            "strategy_evolution_notes": {"worked": "Momentum worked", "failed": "Mean reversion failed"},
            "sanity_report": {
                "health_score": 95,
                "violation_count": 1,
                "health_guard_active": False,
                "buy_recommendations_downgraded": 0
            },
            "health_trend": {
                "moving_average_5d": 90.5,
                "moving_average_20d": 88.2,
                "slope_7d": 0.3,
                "violation_density_5d": 0.2,
                "violation_density_20d": 0.25,
                "recovery_time_days": 2,
                "root_cause_summary": [
                    {"violation": "missing_key_reasons", "count": 4}
                ],
            },
        }
        analyses = [
            {
                "ticker": "AAPL",
                "score": 80,
                "rating": "BUY",
                "target_price": 210.0,
                "expected_return_pct": 8.0,
                "risk_level": "Medium",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            scanner_path = Path(tmp_dir) / "scanner.json"
            analysis_path = Path(tmp_dir) / "analysis.json"
            dashboard_path = Path(tmp_dir) / "dashboard.md"
            summary_path = Path(tmp_dir) / "summary.txt"

            scanner_path.write_text(json.dumps(scanner_payload), encoding="utf-8")
            analysis_path.write_text(json.dumps(analyses), encoding="utf-8")

            build_daily_dashboard(
                scanner_input_path=str(scanner_path),
                analysis_results_path=str(analysis_path),
                dashboard_output_path=str(dashboard_path),
                summary_output_path=str(summary_path),
            )

            dashboard_text = dashboard_path.read_text(encoding="utf-8")
            self.assertIn("## Market Overview", dashboard_text)
            self.assertIn("## System Health Score", dashboard_text)
            self.assertIn("## Health Trend", dashboard_text)
            self.assertIn("## Top Opportunities", dashboard_text)
            self.assertIn("## High-Risk Alerts", dashboard_text)
            self.assertIn("## Earnings Watchlist", dashboard_text)
            self.assertIn("## Strategy Evolution Notes", dashboard_text)


if __name__ == "__main__":
    unittest.main()
