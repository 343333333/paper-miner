"""Send the HTML digest via Gmail SMTP."""

import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_digest(html_body: str, n_papers: int) -> None:
    """Send the HTML digest email. Raises on failure so the caller can log it."""
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not gmail_address:
        raise ValueError("GMAIL_ADDRESS environment variable not set")
    if not gmail_password:
        raise ValueError("GMAIL_APP_PASSWORD environment variable not set")
    if not recipient:
        raise ValueError("RECIPIENT_EMAIL environment variable not set")

    today = date.today().strftime("%Y-%m-%d")
    subject = f"\U0001f52c Biophysics Digest \u2014 {today} ({n_papers} papers)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())

    print(f"  Email sent to {recipient}: {subject}")


def send_no_papers_email() -> None:
    """Send a plain-text notification when no papers scored highly enough."""
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not gmail_address:
        raise ValueError("GMAIL_ADDRESS environment variable not set")
    if not gmail_password:
        raise ValueError("GMAIL_APP_PASSWORD environment variable not set")
    if not recipient:
        raise ValueError("RECIPIENT_EMAIL environment variable not set")

    today = date.today().strftime("%Y-%m-%d")
    subject = f"\U0001f52c Biophysics Digest \u2014 {today} (no new papers)"
    body = "No highly relevant papers found today."

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_password)
        server.sendmail(gmail_address, recipient, msg.as_string())

    print(f"  Email sent to {recipient}: {subject}")
