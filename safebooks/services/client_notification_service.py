import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail

from safebooks.models import FinancialRecord, Period


logger = logging.getLogger(__name__)


def _format_money(value) -> str:
    amount = value if isinstance(value, Decimal) else Decimal(str(value or "0"))
    return f"PHP {amount.quantize(Decimal('0.01')):,.2f}"


def _format_frequency(value: str) -> str:
    labels = dict(FinancialRecord.FREQUENCY_CHOICES)
    return labels.get(value, str(value or "").title() or "Monthly")


def _period_label(record: FinancialRecord) -> str:
    period = getattr(record, "period", None)
    if period:
        month_name = dict(Period.MONTH_CHOICES).get(period.month, str(period.month))
        return f"{month_name} {period.year}"

    if record.entry_date:
        return record.entry_date.strftime("%B %Y")

    return "the selected period"


def send_financial_record_created_email(record: FinancialRecord) -> dict:
    if not getattr(settings, "SAFEBOOKS_CLIENT_RECORD_EMAILS_ENABLED", True):
        return {
            "sent": False,
            "skipped": True,
            "reason": "Client record email notifications are disabled.",
        }

    bookkeeper = record.bookkeeper
    if not getattr(bookkeeper, "client_record_email_notifications_enabled", True):
        return {
            "sent": False,
            "skipped": True,
            "reason": "Client email notifications are turned off in Settings.",
        }

    client = record.client
    recipient_email = str(getattr(client, "email", "") or "").strip()
    if not recipient_email:
        return {
            "sent": False,
            "skipped": True,
            "reason": "Client email is not provided.",
        }

    bookkeeper_name = (
        str(getattr(bookkeeper, "full_name", "") or "").strip()
        or str(getattr(bookkeeper, "username", "") or "").strip()
        or "your bookkeeper"
    )
    period_label = _period_label(record)
    frequency_label = _format_frequency(record.frequency)
    line_item_count = record.line_items.count()

    subject = f"SafeBooks record update for {period_label}"
    message = (
        f"Hello {client.client_name},\n\n"
        "This is a SafeBooks update for your financial records.\n\n"
        f"{bookkeeper_name} recorded a {frequency_label.lower()} financial entry for {period_label}.\n"
        f"Entry date: {record.entry_date.strftime('%B %d, %Y')}\n"
        f"Total recorded amount: {_format_money(record.total_amount)}\n"
        f"Line items recorded: {line_item_count}\n\n"
        "Please contact your bookkeeper if you need to review the details.\n\n"
        "SafeBooks"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            "Failed to send financial record notification email for record %s.",
            record.id,
            exc_info=True,
        )
        return {
            "sent": False,
            "skipped": False,
            "reason": "Email delivery failed.",
        }

    return {
        "sent": True,
        "skipped": False,
        "reason": "",
    }
