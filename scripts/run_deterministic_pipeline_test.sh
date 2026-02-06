#!/usr/bin/env bash
set -euo pipefail

python -m unittest tests/test_daily_pipeline_deterministic.py
