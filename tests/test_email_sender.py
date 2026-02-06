import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.email_sender import send_dashboard_email


class EmailSenderTests(unittest.TestCase):
    @patch("smtplib.SMTP")
    def test_send_dashboard_email_builds_and_sends_message(self, mock_smtp) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dashboard_path = Path(tmp_dir) / "daily_dashboard.md"
            dashboard_path.write_text("# dashboard", encoding="utf-8")

            send_dashboard_email(
                smtp_server="smtp.example.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="pass",
                sender="from@example.com",
                recipients="to@example.com",
                subject="Subject",
                dashboard_path=str(dashboard_path),
                summary_text="Summary text",
                use_tls=True,
            )

            instance = mock_smtp.return_value.__enter__.return_value
            instance.starttls.assert_called_once()
            instance.login.assert_called_once_with("user", "pass")
            instance.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
