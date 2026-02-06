#!/usr/bin/env python3
"""Run manual analysis API endpoint server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.manual_api import run_manual_analysis_api  # noqa: E402


if __name__ == "__main__":
    host = os.environ.get("MANUAL_API_HOST", "0.0.0.0")
    port = int(os.environ.get("MANUAL_API_PORT", "8080"))
    config_path = os.environ.get("ANALYSIS_CONFIG_PATH", "config/analysis_config.json")
    run_manual_analysis_api(host=host, port=port, config_path=config_path)
