
"""Gmail SMTP email delivery service for CareerPilotAI."""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(*, to: str, subject: str, html: str) -> str:
    """Send a transactional email using Gmail SMTP."""

    if not settings.smtp_email or not settings.smtp_password:
        logger.error("Gmail SMTP credentials are not configured.")
        raise RuntimeError("Email service is not configured.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_email
    message["To"] = to
    message["Message-ID"] = f"<{uuid4()}@careerpilotai.local>"

    message.set_content(
        "This email contains HTML content. Please use an email client "
        "that supports HTML to view it."
    )
    message.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            context=context,
            timeout=30,
        ) as server:
            server.login(
                settings.smtp_email,
                settings.smtp_password,
            )
            server.send_message(message)

        logger.info(
            "Email accepted by Gmail SMTP for recipient domain %s",
            to.rsplit("@", 1)[-1] if "@" in to else "unknown",
        )
        return message["Message-ID"]

    except (smtplib.SMTPException, OSError) as exc:
        logger.exception(
            "Gmail SMTP delivery failed for recipient domain %s",
            to.rsplit("@", 1)[-1] if "@" in to else "unknown",
        )
        raise RuntimeError(
            "Failed to send email. Please try again later."
        ) from exc


def send_verification_email(*, to: str, token: str) -> str:
    """Send an email-verification link to a newly registered user."""

    link = (
        f"{settings.frontend_base_url}"
        f"/pages/verify-email.html?token={token}"
    )

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0F172A;color:#F1F5F9;border-radius:12px;">
        <h2 style="margin-top:0;color:#3B82F6;">Verify your email</h2>
        <p>Welcome to <strong>CareerPilotAI</strong>! Click the button below to verify your email address.
           This link expires in <strong>24 hours</strong>.</p>
        <a href="{link}"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#3B82F6;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
            Verify Email
        </a>
        <p style="font-size:12px;color:#94A3B8;">
            If you did not create a CareerPilotAI account, you can safely ignore this email.
        </p>
    </div>
    """

    return _send(
        to=to,
        subject="Verify your CareerPilotAI email address",
        html=html,
    )


def send_password_reset_email(*, to: str, token: str) -> str:
    """Send a password-reset link to a user."""

    link = (
        f"{settings.frontend_base_url}"
        f"/pages/reset-password.html?token={token}"
    )

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0F172A;color:#F1F5F9;border-radius:12px;">
        <h2 style="margin-top:0;color:#3B82F6;">Reset your password</h2>
        <p>We received a request to reset the password for your <strong>CareerPilotAI</strong> account.
           Click the button below — this link expires in <strong>1 hour</strong>.</p>
        <a href="{link}"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#3B82F6;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
            Reset Password
        </a>
        <p style="font-size:12px;color:#94A3B8;">
            If you did not request a password reset, you can safely ignore this email.
        </p>
    </div>
    """

    return _send(
        to=to,
        subject="Reset your CareerPilotAI password",
        html=html,
    )
