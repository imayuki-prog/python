"""
OTP (One-Time Password) fetcher for email-based 2FA codes.
Supports Gmail, Outlook, and any IMAP-compatible email service.
"""

import imaplib
import email
import re
import time
import os
from datetime import datetime, timedelta
from email.header import decode_header
from typing import Optional


# --- OTP extraction patterns ---
# Matches 4-8 digit codes typically used in 2FA
OTP_PATTERNS = [
    r"\b(\d{6})\b",          # Standard 6-digit OTP
    r"\b(\d{4})\b",          # 4-digit PIN
    r"\b(\d{8})\b",          # 8-digit code (some services)
    r"code[:\s]+(\d{4,8})",  # "code: 123456"
    r"OTP[:\s]+(\d{4,8})",   # "OTP: 123456"
    r"(\d{4,8})\s+is your",  # "123456 is your code"
]

# Known 2FA sender addresses
KNOWN_SENDERS = {
    "amazon":  ["no-reply@amazon.com", "account-update@amazon.com"],
    "walmart": ["no-reply@walmart.com", "help@walmart.com"],
    "google":  ["no-reply@accounts.google.com"],
    "apple":   ["no_reply@email.apple.com"],
}

# IMAP server presets
IMAP_SERVERS = {
    "gmail":   ("imap.gmail.com", 993),
    "outlook": ("outlook.office365.com", 993),
    "yahoo":   ("imap.mail.yahoo.com", 993),
    "icloud":  ("imap.mail.me.com", 993),
}


class OTPFetcher:
    def __init__(
        self,
        email_address: str,
        password: str,
        provider: str = "gmail",
        imap_host: Optional[str] = None,
        imap_port: int = 993,
    ):
        """
        Args:
            email_address: Your email address
            password:      App password (Gmail) or regular password
            provider:      "gmail", "outlook", "yahoo", or "icloud"
            imap_host:     Custom IMAP host (overrides provider preset)
            imap_port:     Custom IMAP port (overrides provider preset)
        """
        self.email_address = email_address

        if imap_host:
            self.imap_host = imap_host
            self.imap_port = imap_port
        else:
            preset = IMAP_SERVERS.get(provider.lower())
            if not preset:
                raise ValueError(f"Unknown provider '{provider}'. Use imap_host instead.")
            self.imap_host, self.imap_port = preset

        self.password = password
        self._conn: Optional[imaplib.IMAP4_SSL] = None

    def connect(self):
        self._conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        self._conn.login(self.email_address, self.password)
        self._conn.select("INBOX")

    def disconnect(self):
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def _decode_str(self, value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value or ""

    def _extract_otp(self, text: str) -> Optional[str]:
        for pattern in OTP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _get_email_body(self, msg) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype in ("text/plain", "text/html"):
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(charset, errors="replace")
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors="replace")
        return body

    def get_latest_otp(
        self,
        sender_filter: Optional[str] = None,
        subject_filter: Optional[str] = None,
        service: Optional[str] = None,
        max_age_minutes: int = 10,
    ) -> Optional[str]:
        """
        Search INBOX for a 2FA email and return the OTP code.

        Args:
            sender_filter:   Part of sender address to match, e.g. "amazon.com"
            subject_filter:  Keyword in subject, e.g. "verification"
            service:         Preset service name: "amazon", "walmart", etc.
            max_age_minutes: Ignore emails older than this many minutes

        Returns:
            OTP string, or None if not found
        """
        if not self._conn:
            self.connect()

        # Build IMAP search criteria
        since_date = (datetime.now() - timedelta(minutes=max_age_minutes)).strftime("%d-%b-%Y")
        criteria = [f'(SINCE "{since_date}")']

        if service and service.lower() in KNOWN_SENDERS:
            senders = KNOWN_SENDERS[service.lower()]
            sender_filter = sender_filter or senders[0]

        if sender_filter:
            criteria.append(f'FROM "{sender_filter}"')
        if subject_filter:
            criteria.append(f'SUBJECT "{subject_filter}"')

        search_str = " ".join(criteria) if len(criteria) > 1 else criteria[0]

        _, message_ids = self._conn.search(None, search_str)
        ids = message_ids[0].split()

        if not ids:
            return None

        # Check most recent email first
        for msg_id in reversed(ids):
            _, msg_data = self._conn.fetch(msg_id, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            body = self._get_email_body(msg)
            subject_raw, enc = decode_header(msg.get("Subject", ""))[0]
            subject = subject_raw.decode(enc or "utf-8") if isinstance(subject_raw, bytes) else subject_raw

            # Try subject first, then body
            otp = self._extract_otp(subject) or self._extract_otp(body)
            if otp:
                return otp

        return None

    def wait_for_otp(
        self,
        timeout_seconds: int = 120,
        poll_interval: int = 5,
        **kwargs,
    ) -> Optional[str]:
        """
        Poll the inbox until a new OTP arrives or timeout is reached.

        Passes **kwargs to get_latest_otp (sender_filter, service, etc.)
        """
        print(f"Waiting for OTP (timeout: {timeout_seconds}s)...")
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            otp = self.get_latest_otp(**kwargs)
            if otp:
                print(f"OTP found: {otp}")
                return otp
            remaining = int(deadline - time.time())
            print(f"  Not found yet, retrying... ({remaining}s left)")
            time.sleep(poll_interval)
        print("Timeout: OTP not received.")
        return None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
