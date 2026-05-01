from decimal import Decimal

from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone

from safebooks.models import Client, FinancialRecord, Period


MONTH_NUMBER_TO_NAME = dict(Period.MONTH_CHOICES)


def _month_label(month_number: int) -> str:
    return MONTH_NUMBER_TO_NAME.get(month_number, str(month_number))


def _period_label(month_number: int, year_number: int) -> str:
    return f"{_month_label(month_number)} {year_number}"


def _serialize_recent_entry(record: FinancialRecord) -> dict:
    return {
        "client_id": record.client_id,
        "client_name": record.client.client_name,
        "tin_number": record.client.tin_number,
        "trade_name": record.client.trade_name,
        "entry_date": record.entry_date.isoformat() if record.entry_date else "",
        "period": _period_label(record.period.month, record.period.year),
        "total_amount": str(record.total_amount or Decimal("0.00")),
    }


def _build_client_activity_payload(client, current_period_label: str) -> dict:
    has_entries = (client.record_count or 0) > 0
    has_current_period_entries = (client.current_period_entries or 0) > 0

    if has_current_period_entries:
        status = "updated"
        compliance = "filed"
    elif has_entries:
        status = "needs-attention"
        compliance = "pending"
    else:
        status = "no-entries"
        compliance = "late"

    last_entry_date = client.last_entry_date.isoformat() if client.last_entry_date else ""

    if client.last_period_month and client.last_period_year:
        current_period = _period_label(client.last_period_month, client.last_period_year)
    else:
        current_period = current_period_label

    risk = client.risk_level or Client.RISK_MEDIUM
    if risk not in {Client.RISK_LOW, Client.RISK_MEDIUM, Client.RISK_HIGH}:
        risk = Client.RISK_MEDIUM

    return {
        "client_id": client.id,
        "client_name": client.client_name,
        "tin_number": client.tin_number,
        "trade_name": client.trade_name,
        "last_entry_date": last_entry_date,
        "current_period": current_period,
        "status": status,
        "risk": risk,
        "compliance": compliance,
    }


def _calculate_percentage(value: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((value / total) * 100)


def get_dashboard_summary_for_bookkeeper(bookkeeper) -> dict:
    today = timezone.localdate()
    current_year = today.year
    current_month = today.month
    current_period_label = _period_label(current_month, current_year)

    latest_record_for_client = (
        FinancialRecord.objects.filter(
            bookkeeper=bookkeeper,
            client_id=OuterRef("pk"),
        )
        .order_by("-entry_date", "-id")
    )

    clients = list(
        Client.objects.filter(bookkeeper=bookkeeper)
        .annotate(
            record_count=Count(
                "financial_records",
                filter=Q(financial_records__bookkeeper=bookkeeper),
                distinct=True,
            ),
            current_period_entries=Count(
                "financial_records",
                filter=Q(
                    financial_records__bookkeeper=bookkeeper,
                    financial_records__period__month=current_month,
                    financial_records__period__year=current_year,
                ),
                distinct=True,
            ),
            last_entry_date=Subquery(latest_record_for_client.values("entry_date")[:1]),
            last_period_month=Subquery(latest_record_for_client.values("period__month")[:1]),
            last_period_year=Subquery(latest_record_for_client.values("period__year")[:1]),
        )
        .order_by("-last_entry_date", "client_name", "id")
    )

    recent_client_activity = [
        _build_client_activity_payload(client, current_period_label)
        for client in clients
    ]

    recent_entries = list(
        FinancialRecord.objects.filter(bookkeeper=bookkeeper)
        .select_related("client", "period")
        .order_by("-entry_date", "-id")[:5]
    )

    recent_entries_payload = [_serialize_recent_entry(record) for record in recent_entries]

    total_clients = len(clients)
    total_entries_this_month = FinancialRecord.objects.filter(
        bookkeeper=bookkeeper,
        period__month=current_month,
        period__year=current_year,
    ).count()

    risk_low_count = sum(1 for client in clients if client.risk_level == Client.RISK_LOW)
    risk_medium_count = sum(1 for client in clients if client.risk_level == Client.RISK_MEDIUM)
    risk_high_count = sum(1 for client in clients if client.risk_level == Client.RISK_HIGH)

    filed_count = sum(1 for row in recent_client_activity if row["compliance"] == "filed")
    pending_count = sum(1 for row in recent_client_activity if row["compliance"] == "pending")
    late_count = sum(1 for row in recent_client_activity if row["compliance"] == "late")

    pending_compliance_count = pending_count + late_count

    return {
        "ok": True,
        "current_period_label": current_period_label,
        "metrics": {
            "total_clients": total_clients,
            "total_entries_this_month": total_entries_this_month,
            "pending_compliance": pending_compliance_count,
            "high_risk_clients": risk_high_count,
        },
        "risk_summary": {
            "low": risk_low_count,
            "medium": risk_medium_count,
            "high": risk_high_count,
        },
        "compliance_summary": {
            "filed": {
                "count": filed_count,
                "percentage": _calculate_percentage(filed_count, total_clients),
            },
            "pending": {
                "count": pending_count,
                "percentage": _calculate_percentage(pending_count, total_clients),
            },
            "late": {
                "count": late_count,
                "percentage": _calculate_percentage(late_count, total_clients),
            },
        },
        "recent_client_activity": recent_client_activity,
        "recent_entries": recent_entries_payload,
    }
