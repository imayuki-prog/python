"""
Alert notifications for low/zero inventory.
Supports Email (SMTP) and Slack webhook.
"""

import smtplib
import json
import os
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailNotifier:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        password: str,
        recipients: list[str],
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
        self.recipients = recipients
        self.use_tls = use_tls

    def send(self, subject: str, body: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.recipients, msg.as_string())

    @classmethod
    def from_gmail(cls, sender: str, app_password: str, recipients: list[str]):
        return cls("smtp.gmail.com", 587, sender, app_password, recipients)

    @classmethod
    def from_outlook(cls, sender: str, password: str, recipients: list[str]):
        return cls("smtp.office365.com", 587, sender, password, recipients)


class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, subject: str, body: str):
        payload = json.dumps({"text": f"*{subject}*\n{body}"}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)


def build_notifier_from_env():
    """
    Build a notifier from environment variables.
    Set NOTIFY_TYPE=email or NOTIFY_TYPE=slack (default: email).
    """
    notify_type = os.environ.get("NOTIFY_TYPE", "email").lower()

    if notify_type == "slack":
        webhook = os.environ["SLACK_WEBHOOK_URL"]
        return SlackNotifier(webhook)

    # Email
    sender = os.environ["NOTIFY_EMAIL"]
    password = os.environ["NOTIFY_EMAIL_PASSWORD"]
    recipients = os.environ["NOTIFY_RECIPIENTS"].split(",")
    provider = os.environ.get("NOTIFY_EMAIL_PROVIDER", "gmail").lower()

    if provider == "gmail":
        return EmailNotifier.from_gmail(sender, password, recipients)
    elif provider == "outlook":
        return EmailNotifier.from_outlook(sender, password, recipients)
    else:
        host = os.environ["NOTIFY_SMTP_HOST"]
        port = int(os.environ.get("NOTIFY_SMTP_PORT", "587"))
        return EmailNotifier(host, port, sender, password, recipients)
