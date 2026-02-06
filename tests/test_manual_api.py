import json
import unittest

from src.core_analysis import load_analysis_config
from src.manual_api import handle_manual_analysis, validate_manual_request


class ManualApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_analysis_config()
        self.valid_payload = {
            "ticker": "AAPL",
            "mode": "PRE_EARNINGS",
            "current_price_override": 195.2,
            "strategy_parameters": {
                "risk_tolerance": "medium",
                "time_horizon": "swing",
                "expected_profit_target": "10%",
            },
            "component_scores": {
                "trend_momentum": 78,
                "fundamentals": 81,
                "news_sentiment": 72,
                "earnings_context_pre": 75,
                "earnings_context_post": 60,
                "risk_volatility": 66,
            },
        }

    def test_validate_manual_request_success(self) -> None:
        analysis_input, strategy, err = validate_manual_request(self.valid_payload)
        self.assertIsNone(err)
        self.assertEqual(analysis_input.ticker, "AAPL")
        self.assertEqual(strategy.time_horizon, "swing")

    def test_validate_manual_request_rejects_invalid_mode(self) -> None:
        payload = json.loads(json.dumps(self.valid_payload))
        payload["mode"] = "INVALID"
        _, _, err = validate_manual_request(payload)
        self.assertIsNotNone(err)
        self.assertEqual(err[0], 400)

    def test_handle_manual_analysis_returns_structured_json(self) -> None:
        status, response = handle_manual_analysis(self.valid_payload, self.config)
        self.assertEqual(status, 200)
        self.assertEqual(response["ticker"], "AAPL")
        self.assertIn("score", response)
        self.assertIn("strategy_parameters", response)


if __name__ == "__main__":
    unittest.main()
