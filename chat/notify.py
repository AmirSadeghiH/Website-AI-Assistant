"""Out-of-band notifications for leads and handoff requests (#11, #12).

Channels: email (Django mail) and Telegram bot (ProviderSettings). Every
channel failure is logged and swallowed — a broken SMTP server must never
break the visitor-facing widget API.
"""

import logging

import httpx
from django.core.mail import mail_admins

logger = logging.getLogger(__name__)

TELEGRAM_TIMEOUT = 8.0


def _provider_contact_settings():
    from .models import ProviderSettings

    provider = ProviderSettings.objects.first()
    if not provider:
        return "", ""
    return (provider.telegram_bot_token or "", provider.telegram_chat_id or "")


def send_telegram_message(text):
    """Send text to the configured Telegram chat. Returns True on success."""
    bot_token, chat_id = _provider_contact_settings()
    if not bot_token or not chat_id:
        logger.info("Telegram not configured; skipping notification.")
        return False
    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text[:4000],
                "parse_mode": "HTML",
            },
            timeout=TELEGRAM_TIMEOUT,
            trust_env=False,
        )
        return response.status_code == 200
    except (httpx.HTTPError, OSError):
        logger.warning("Telegram notification failed", exc_info=True)
        return False


def send_email(subject, body):
    """Email the Django admins (ADMINS setting) — never raises."""
    try:
        mail_admins(subject[:200], body[:4000], fail_silently=True)
        return True
    except Exception:
        logger.warning("Email notification failed", exc_info=True)
        return False


def notify_lead_created(lead):
    body = (
        f"سرنخ جدید از ویجت پشتیبانی\n"
        f"نام: {lead.name}\n"
        f"ایمیل: {lead.email or '—'}\n"
        f"تلفن: {lead.phone or '—'}\n"
        f"کانال: {lead.get_source_display()}\n"
        f"یادداشت: {lead.note[:500] or '—'}\n"
        f"زمان: {lead.created_at:%Y-%m-%d %H:%M}"
    )
    send_telegram_message(f"🎯 <b>سرنخ جدید</b>\n\n{body}")
    send_email("سرنخ جدید از ویجت پشتیبانی", body)


def notify_handoff_request(handoff):
    question = (handoff.question or "—")[:500]
    body = (
        f"درخواست پشتیبانی انسانی جدید\n"
        f"کانال انتخابی: {handoff.get_channel_display()}\n"
        f"آخرین سؤال: {question}\n"
        f"زمان: {handoff.created_at:%Y-%m-%d %H:%M}"
    )
    send_telegram_message(f"🙋 <b>درخواست پشتیبانی انسانی</b>\n\n{body}")
    send_email("درخواست پشتیبانی انسانی جدید", body)
