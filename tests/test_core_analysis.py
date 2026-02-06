import unittest

from src.core_analysis import AnalysisInput, ComponentScores, analyze_stock, load_analysis_config


class CoreAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_analysis_config()

    def test_pre_earnings_mode_uses_pre_score(self) -> None:
        analysis_input = AnalysisInput(
            ticker="NVDA",
            mode="PRE_EARNINGS",
            current_price=100.0,
            scores=ComponentScores(
                trend_momentum=80,
                fundamentals=80,
                news_sentiment=80,
                earnings_context_pre=100,
                earnings_context_post=0,
                risk_volatility=80,
            ),
        )
        result = analyze_stock(analysis_input, self.config)
        self.assertEqual(result["score"], 83)
        self.assertEqual(result["rating"], "BUY")

    def test_post_earnings_mode_uses_post_score(self) -> None:
        analysis_input = AnalysisInput(
            ticker="NVDA",
            mode="POST_EARNINGS",
            current_price=100.0,
            scores=ComponentScores(
                trend_momentum=80,
                fundamentals=80,
                news_sentiment=80,
                earnings_context_pre=100,
                earnings_context_post=0,
                risk_volatility=80,
            ),
        )
        result = analyze_stock(analysis_input, self.config)
        self.assertEqual(result["score"], 68)
        self.assertEqual(result["rating"], "BUY")

    def test_schema_keys_present(self) -> None:
        analysis_input = AnalysisInput(
            ticker="MSFT",
            mode="PRE_EARNINGS",
            current_price=410.0,
            scores=ComponentScores(
                trend_momentum=40,
                fundamentals=45,
                news_sentiment=50,
                earnings_context_pre=45,
                earnings_context_post=30,
                risk_volatility=35,
            ),
        )
        result = analyze_stock(analysis_input, self.config)

        expected_keys = {
            "ticker",
            "mode",
            "score",
            "rating",
            "current_price",
            "target_price",
            "expected_return_pct",
            "risk_level",
            "key_reasons",
            "invalidating_factors",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_daily_score_change_cap_applies(self) -> None:
        analysis_input = AnalysisInput(
            ticker="AAPL",
            mode="PRE_EARNINGS",
            current_price=100.0,
            scores=ComponentScores(
                trend_momentum=100,
                fundamentals=100,
                news_sentiment=100,
                earnings_context_pre=100,
                earnings_context_post=100,
                risk_volatility=100,
            ),
        )
        result = analyze_stock(analysis_input, self.config, previous_score=40)
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["score_before_daily_cap"], 100)


if __name__ == "__main__":
    unittest.main()
