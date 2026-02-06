import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.email_sender import send_dashboard_email


class DeterministicDailyPipelineTests(unittest.TestCase):
    def test_full_pipeline_end_to_end_with_fixed_inputs(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        fixed_input_path = project_root / "config" / "daily_scanner_input.example.json"

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            scanner_output = tmp_path / "scanner_output.json"
            analysis_output = tmp_path / "analysis_results.json"
            dashboard_output = tmp_path / "daily_dashboard.md"
            summary_output = tmp_path / "daily_summary.txt"
            sanity_output = tmp_path / "sanity_report.json"
            health_output = tmp_path / "health_score.json"
            history_output = tmp_path / "health_history.json"

            env = {
                **os.environ,
                "SCANNER_INPUT_PATH": str(fixed_input_path),
                "SCANNER_OUTPUT_PATH": str(scanner_output),
                "ANALYSIS_OUTPUT_PATH": str(analysis_output),
                "DASHBOARD_OUTPUT_PATH": str(dashboard_output),
                "DASHBOARD_SUMMARY_PATH": str(summary_output),
                "SANITY_REPORT_PATH": str(sanity_output),
                "HEALTH_SCORE_PATH": str(health_output),
                "HEALTH_HISTORY_PATH": str(history_output),
            }

            subprocess.run(
                ["python", "scripts/run_daily_scanner.py"],
                cwd=project_root,
                env=env,
                check=True,
            )
            subprocess.run(
                ["python", "scripts/generate_dashboard.py"],
                cwd=project_root,
                env=env,
                check=True,
            )

            scanner_payload = json.loads(scanner_output.read_text(encoding="utf-8"))
            self.assertEqual(scanner_payload["report_date"], "2026-01-15")
            self.assertEqual(len(scanner_payload["stocks"]), 5)

            analysis_payload = json.loads(analysis_output.read_text(encoding="utf-8"))
            self.assertEqual(len(analysis_payload), 5)

            sanity_payload = json.loads(sanity_output.read_text(encoding="utf-8"))
            self.assertIn("health_score", sanity_payload)
            health_payload = json.loads(health_output.read_text(encoding="utf-8"))
            self.assertIn("health_score", health_payload)
            history_payload = json.loads(history_output.read_text(encoding="utf-8"))
            self.assertEqual(len(history_payload), 1)

            dashboard_text = dashboard_output.read_text(encoding="utf-8")
            self.assertIn("## Market Overview", dashboard_text)
            self.assertIn("## System Health Score", dashboard_text)
            self.assertIn("## Top Opportunities", dashboard_text)
            self.assertIn("## High-Risk Alerts", dashboard_text)
            self.assertIn("## Earnings Watchlist", dashboard_text)
            self.assertIn("## Strategy Evolution Notes", dashboard_text)

            summary_text = summary_output.read_text(encoding="utf-8")
            self.assertIn("Analyzed 5 stocks.", summary_text)

            with patch("smtplib.SMTP") as mock_smtp:
                send_dashboard_email(
                    smtp_server="smtp.example.com",
                    smtp_port=587,
                    smtp_username="smtp-user",
                    smtp_password="smtp-password",
                    sender="noreply@example.com",
                    recipients="investor@example.com",
                    subject="Deterministic Pipeline Test",
                    dashboard_path=str(dashboard_output),
                    summary_text=summary_text,
                    use_tls=True,
                )
                smtp_instance = mock_smtp.return_value.__enter__.return_value
                smtp_instance.starttls.assert_called_once()
                smtp_instance.login.assert_called_once_with("smtp-user", "smtp-password")
                smtp_instance.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
