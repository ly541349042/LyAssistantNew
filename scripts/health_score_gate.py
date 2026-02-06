#!/usr/bin/env python3
"""Health score gate for CI workflow.

This script only enforces gate outcomes; business rules live in config/logic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/health_score_gate.py <health_score.json>")

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    health_score = int(payload.get("health_score", 0))

    if health_score >= 85:
        print(f"Health score {health_score}: normal success.")
        return

    if 70 <= health_score <= 84:
        print(f"::warning::Health score {health_score}: success with warning.")
        return

    if 50 <= health_score <= 69:
        print(
            f"::warning::Health score {health_score}: success with warning; HOLD bias should already be applied."
        )
        return

    print(f"::error::Health score {health_score}: below 50, failing workflow.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
