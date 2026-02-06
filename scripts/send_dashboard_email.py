#!/usr/bin/env python3
"""Send dashboard email using SMTP env vars."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.email_sender import send_dashboard_email_from_env  # noqa: E402


if __name__ == "__main__":
    send_dashboard_email_from_env()
