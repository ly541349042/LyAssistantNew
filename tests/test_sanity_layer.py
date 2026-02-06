import tempfile
import unittest
from pathlib import Path

from src.sanity_layer import (
    apply_health_controls,
    compute_health_trend,
    evaluate_daily_sanity,
    load_sanity_config,
    update_health_history,
)


class SanityLayerTests(unittest.TestCase):
    def test_daily_sanity_and_health_control(self) -> None:
        config = load_sanity_config()
        analysis_results = [
            {
                "ticker": "ABCD",
                "score": 72,
                "rating": "BUY",
                "current_price": 100.0,
                "target_price": 110.0,
                "expected_return_pct": 10.0,
                "risk_level": "High",
                "key_reasons": ["x"],
                "invalidating_factors": ["y"],
            },
            {
                "ticker": "EFGH",
                "score": 60,
                "rating": "BUY",
                "current_price": 200.0,
                "target_price": 180.0,
                "expected_return_pct": -10.0,
                "risk_level": "Medium",
                "key_reasons": [],
                "invalidating_factors": [],
            },
        ]

        config["behavior_controls"]["block_buy_below_health_score"] = 100

        report = evaluate_daily_sanity(analysis_results, config)
        self.assertGreater(report["violation_count"], 0)
        self.assertLess(report["health_score"], 100)

        adjusted, controls = apply_health_controls(analysis_results, report, config)
        self.assertTrue(controls["health_guard_active"])
        self.assertEqual(adjusted[0]["rating"], "HOLD")
        self.assertEqual(adjusted[0]["base_rating"], "BUY")

    def test_health_trend_metrics(self) -> None:
        config = load_sanity_config()
        analysis_results = [
            {
                "ticker": "ABCD",
                "score": 72,
                "rating": "BUY",
                "current_price": 100.0,
                "target_price": 110.0,
                "expected_return_pct": 10.0,
                "risk_level": "Medium",
                "key_reasons": ["x"],
                "invalidating_factors": ["y"],
            }
        ]
        report = evaluate_daily_sanity(analysis_results, config)
        with tempfile.TemporaryDirectory() as tmp_dir:
            history = update_health_history(
                history_path=str(Path(tmp_dir) / "health_history.json"),
                report_date="2026-01-15",
                analysis_results=analysis_results,
                sanity_report=report,
            )
        trend = compute_health_trend(history)
        self.assertIn("moving_average_5d", trend)
        self.assertIn("slope_7d", trend)
        self.assertIn("violation_density_5d", trend)
        self.assertIn("recovery_time_days", trend)
        self.assertIn("root_cause_summary", trend)


if __name__ == "__main__":
    unittest.main()
