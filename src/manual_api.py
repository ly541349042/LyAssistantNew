"""Manual analysis HTTP endpoint for single-stock queries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

from src.core_analysis import AnalysisInput, ComponentScores, analyze_stock, load_analysis_config

Mode = Literal["PRE_EARNINGS", "POST_EARNINGS"]
RiskTolerance = Literal["low", "medium", "high"]
TimeHorizon = Literal["short", "swing", "long"]


@dataclass(frozen=True)
class StrategyParameters:
    risk_tolerance: RiskTolerance
    time_horizon: TimeHorizon
    expected_profit_target: str


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _error(message: str, status: int = HTTPStatus.BAD_REQUEST) -> Tuple[int, Dict[str, Any]]:
    return status, {"error": message}


def _validate_mode(payload: Dict[str, Any]) -> Tuple[Optional[Mode], Optional[Tuple[int, Dict[str, Any]]]]:
    mode = payload.get("mode")
    if mode not in ("PRE_EARNINGS", "POST_EARNINGS"):
        return None, _error("mode must be PRE_EARNINGS or POST_EARNINGS")
    return mode, None


def _validate_strategy(payload: Dict[str, Any]) -> Tuple[Optional[StrategyParameters], Optional[Tuple[int, Dict[str, Any]]]]:
    strategy = payload.get("strategy_parameters")
    if not isinstance(strategy, dict):
        return None, _error("strategy_parameters must be an object")

    risk_tolerance = strategy.get("risk_tolerance")
    if risk_tolerance not in ("low", "medium", "high"):
        return None, _error("strategy_parameters.risk_tolerance must be low, medium, or high")

    time_horizon = strategy.get("time_horizon")
    if time_horizon not in ("short", "swing", "long"):
        return None, _error("strategy_parameters.time_horizon must be short, swing, or long")

    expected_profit_target = strategy.get("expected_profit_target")
    if not isinstance(expected_profit_target, str) or not expected_profit_target.strip():
        return None, _error("strategy_parameters.expected_profit_target must be a non-empty string")

    return (
        StrategyParameters(
            risk_tolerance=risk_tolerance,
            time_horizon=time_horizon,
            expected_profit_target=expected_profit_target.strip(),
        ),
        None,
    )


def _validate_component_scores(payload: Dict[str, Any]) -> Tuple[Optional[ComponentScores], Optional[Tuple[int, Dict[str, Any]]]]:
    scores = payload.get("component_scores")
    if not isinstance(scores, dict):
        return None, _error("component_scores must be an object")

    required = (
        "trend_momentum",
        "fundamentals",
        "news_sentiment",
        "earnings_context_pre",
        "earnings_context_post",
        "risk_volatility",
    )

    missing = [field for field in required if field not in scores]
    if missing:
        return None, _error(f"component_scores missing fields: {', '.join(missing)}")

    try:
        component_scores = ComponentScores(
            trend_momentum=float(scores["trend_momentum"]),
            fundamentals=float(scores["fundamentals"]),
            news_sentiment=float(scores["news_sentiment"]),
            earnings_context_pre=float(scores["earnings_context_pre"]),
            earnings_context_post=float(scores["earnings_context_post"]),
            risk_volatility=float(scores["risk_volatility"]),
        )
    except (TypeError, ValueError):
        return None, _error("component_scores values must be numeric")

    return component_scores, None


def _resolve_current_price(payload: Dict[str, Any]) -> Tuple[Optional[float], Optional[Tuple[int, Dict[str, Any]]]]:
    # TODO(SPEC-CLARITY): Manual mode says current price override is optional, implying live price fetch.
    # Live market data integration is not in this phase, so request must include either
    # current_price_override or current_price.
    price_value = payload.get("current_price_override", payload.get("current_price"))
    if price_value is None:
        return None, _error("current_price_override or current_price is required")

    try:
        price = float(price_value)
    except (TypeError, ValueError):
        return None, _error("current_price_override/current_price must be numeric")

    if price <= 0:
        return None, _error("current_price_override/current_price must be > 0")

    return price, None


def validate_manual_request(payload: Dict[str, Any]) -> Tuple[Optional[AnalysisInput], Optional[StrategyParameters], Optional[Tuple[int, Dict[str, Any]]]]:
    ticker = payload.get("ticker")
    if not isinstance(ticker, str) or not ticker.strip():
        return None, None, _error("ticker must be a non-empty string")

    mode, mode_error = _validate_mode(payload)
    if mode_error:
        return None, None, mode_error

    strategy, strategy_error = _validate_strategy(payload)
    if strategy_error:
        return None, None, strategy_error

    component_scores, scores_error = _validate_component_scores(payload)
    if scores_error:
        return None, None, scores_error

    current_price, price_error = _resolve_current_price(payload)
    if price_error:
        return None, None, price_error

    analysis_input = AnalysisInput(
        ticker=ticker.strip().upper(),
        mode=mode,
        current_price=current_price,
        scores=component_scores,
    )
    return analysis_input, strategy, None


def handle_manual_analysis(payload: Dict[str, Any], config: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    analysis_input, strategy, err = validate_manual_request(payload)
    if err:
        return err

    result = analyze_stock(analysis_input, config)
    result["strategy_parameters"] = {
        "risk_tolerance": strategy.risk_tolerance,
        "time_horizon": strategy.time_horizon,
        "expected_profit_target": strategy.expected_profit_target,
    }
    return HTTPStatus.OK, result


class ManualAnalysisHandler(BaseHTTPRequestHandler):
    """JSON-only POST endpoint handler for /api/manual-analysis."""

    config: Dict[str, Any] = {}

    def _write_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/manual-analysis":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "invalid Content-Length"})
            return

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "request body must be valid JSON"})
            return

        if not isinstance(payload, dict):
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "request body must be a JSON object"})
            return

        status, response = handle_manual_analysis(payload, self.config)
        self._write_json(status, response)


def run_manual_analysis_api(host: str, port: int, config_path: str = "config/analysis_config.json") -> None:
    """Start manual analysis API server."""

    config = load_analysis_config(config_path)
    ManualAnalysisHandler.config = config

    server = ThreadingHTTPServer((host, port), ManualAnalysisHandler)
    print(f"Manual analysis API listening on http://{host}:{port}/api/manual-analysis")
    server.serve_forever()
