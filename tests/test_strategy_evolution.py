import json
import tempfile
import unittest
from pathlib import Path

from src.performance_tracker import load_evolution_config, load_outcomes, summarize_strategy_performance
from src.strategy_evolution import evolve_weights, run_strategy_evolution


class StrategyEvolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evolution_config = load_evolution_config("config/evolution_config.json")
        self.outcomes = load_outcomes("examples/strategy_outcomes.example.json")

    def test_performance_tracking_includes_required_horizons(self) -> None:
        summary = summarize_strategy_performance(self.outcomes, self.evolution_config)
        strategy = summary["trend_momentum"]
        self.assertIn("1d", strategy["metrics"])
        self.assertIn("5d", strategy["metrics"])
        self.assertIn("20d", strategy["metrics"])

    def test_degradation_detection_matches_spec_thresholds(self) -> None:
        summary = summarize_strategy_performance(self.outcomes, self.evolution_config)
        self.assertTrue(summary["news_sentiment"]["degraded"])
        self.assertTrue(summary["earnings_context"]["degraded"])
        self.assertFalse(summary["trend_momentum"]["degraded"])

    def test_conservative_weight_adjustment(self) -> None:
        summary = summarize_strategy_performance(self.outcomes, self.evolution_config)
        old_weights = {
            "trend_momentum": 25,
            "fundamentals": 25,
            "news_sentiment": 20,
            "earnings_context": 15,
            "risk_volatility": 15,
        }
        new_weights, changes = evolve_weights(old_weights, summary, self.evolution_config)

        self.assertEqual(sum(new_weights.values()), 100)
        self.assertTrue(len(changes) > 0)
        for key, old_value in old_weights.items():
            self.assertLessEqual(
                abs(new_weights[key] - old_value),
                self.evolution_config["weight_adjustment"]["max_total_adjustment_pct"],
            )

    def test_report_generation_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            state_path = Path(tmp_dir) / "state.json"
            report = run_strategy_evolution(
                analysis_config_path="config/analysis_config.json",
                evolution_config_path="config/evolution_config.json",
                outcomes_path="examples/strategy_outcomes.example.json",
                report_output_path=str(report_path),
                state_path=str(state_path),
                current_date="2026-01-10",
            )
            loaded = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("strategy_evolution_report", loaded)
            self.assertEqual(
                report["strategy_evolution_report"]["new_weights"],
                loaded["strategy_evolution_report"]["new_weights"],
            )

    def test_cooldown_blocks_weight_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            state_path = Path(tmp_dir) / "state.json"
            state_path.write_text(json.dumps({"last_weight_update_date": "2026-01-09"}), encoding="utf-8")

            report = run_strategy_evolution(
                analysis_config_path="config/analysis_config.json",
                evolution_config_path="config/evolution_config.json",
                outcomes_path="examples/strategy_outcomes.example.json",
                report_output_path=str(report_path),
                state_path=str(state_path),
                current_date="2026-01-10",
            )
            payload = report["strategy_evolution_report"]
            self.assertTrue(payload["cooldown_active"])
            self.assertEqual(payload["old_weights"], payload["new_weights"])
            self.assertEqual(payload["applied_changes"], [])


if __name__ == "__main__":
    unittest.main()
