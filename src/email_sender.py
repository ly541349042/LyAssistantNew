"""SMTP email sender for dashboard delivery."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_dashboard_email(
    smtp_server: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    sender: str,
    recipients: str,
    subject: str,
    dashboard_path: str,
    summary_text: str,
    use_tls: bool,
) -> None:
    """Send dashboard email with markdown attachment and plain-text body."""

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipients
    msg["Subject"] = subject

    msg.set_content(
        "\n".join(
            [
                "Daily NASDAQ scanner report is ready.",
                "",
                "Summary:",
                summary_text.strip(),
            ]
        )
    )

    dashboard_bytes = Path(dashboard_path).read_bytes()
    msg.add_attachment(
        dashboard_bytes,
        maintype="text",
        subtype="markdown",
        filename=Path(dashboard_path).name,
    )

    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)


def send_dashboard_email_from_env() -> None:
    """Environment-driven wrapper to keep workflow configuration externalized."""

    summary_text = Path(os.environ["DASHBOARD_SUMMARY_PATH"]).read_text(encoding="utf-8")

    send_dashboard_email(
        smtp_server=os.environ["SMTP_SERVER_ADDRESS"],
        smtp_port=int(os.environ["SMTP_SERVER_PORT"]),
        smtp_username=os.environ["SMTP_USERNAME"],
        smtp_password=os.environ["SMTP_PASSWORD"],
        sender=os.environ["DASHBOARD_EMAIL_FROM"],
        recipients=os.environ["DASHBOARD_EMAIL_TO"],
        subject=os.environ["DASHBOARD_EMAIL_SUBJECT"],
        dashboard_path=os.environ["DASHBOARD_OUTPUT_PATH"],
        summary_text=summary_text,
        use_tls=os.environ.get("SMTP_USE_TLS", "true").lower() == "true",
    )
