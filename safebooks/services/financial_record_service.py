from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Max, OuterRef, Subquery
from django.utils import timezone

from safebooks.models import Client, FinancialRecord, FinancialRecordLine, Period


MONTH_NUMBER_TO_NAME = dict(Period.MONTH_CHOICES)
MONTH_NAME_TO_NUMBER = {label.lower(): number for number, label in Period.MONTH_CHOICES}
ALLOWED_FREQUENCIES = {
    FinancialRecord.FREQUENCY_MONTHLY,
    FinancialRecord.FREQUENCY_QUARTERLY,
    FinancialRecord.FREQUENCY_ANNUALLY,
}


def _normalize_text(value) -> str:
    return str(value or "").strip()


def _normalize_month(value):
    if value in (None, ""):
        return date.today().month, None

    if isinstance(value, int):
        month = value
    else:
        cleaned_value = _normalize_text(value)
        if not cleaned_value:
            return date.today().month, None

        if cleaned_value.isdigit():
            month = int(cleaned_value)
        else:
            month = MONTH_NAME_TO_NUMBER.get(cleaned_value.lower())

    if month not in MONTH_NUMBER_TO_NAME:
        return None, "Invalid period month."

    return month, None


def _normalize_year(value):
    if value in (None, ""):
        return date.today().year, None

    cleaned_value = _normalize_text(value)
    if not cleaned_value.isdigit():
        return None, "Invalid period year."

    year = int(cleaned_value)
    if year < 2000 or year > 2100:
        return None, "Period year must be between 2000 and 2100."

    return year, None


def _normalize_entry_date(value):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, "Entry date is required."

    try:
        entry_date = date.fromisoformat(cleaned_value)
    except ValueError:
        return None, "Entry date must use YYYY-MM-DD format."

    if entry_date.year < 2000 or entry_date.year > 2100:
        return None, "Entry date year must be between 2000 and 2100."

    return entry_date, None


def _normalize_frequency(value):
    cleaned_value = _normalize_text(value).lower()
    if not cleaned_value:
        return FinancialRecord.FREQUENCY_MONTHLY, None

    if cleaned_value not in ALLOWED_FREQUENCIES:
        return None, "Frequency must be Monthly, Quarterly, or Annually."

    return cleaned_value, None


def _normalize_required_date(value, label: str):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, f"{label} is required."

    try:
        parsed_date = date.fromisoformat(cleaned_value)
    except ValueError:
        return None, f"{label} must use YYYY-MM-DD format."

    if parsed_date.year < 2000 or parsed_date.year > 2100:
        return None, f"{label} year must be between 2000 and 2100."

    return parsed_date, None


def _normalize_optional_date(value, label: str):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, None

    try:
        parsed_date = date.fromisoformat(cleaned_value)
    except ValueError:
        return None, f"{label} must use YYYY-MM-DD format."

    if parsed_date.year < 2000 or parsed_date.year > 2100:
        return None, f"{label} year must be between 2000 and 2100."

    return parsed_date, None


def _normalize_amount(value):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, "Amount is required."

    try:
        amount = Decimal(cleaned_value)
    except (InvalidOperation, TypeError):
        return None, "Amount must be a valid number."

    if amount < 0:
        return None, "Amount cannot be negative."

    return amount.quantize(Decimal("0.01")), None


def _normalize_line_items(line_items):
    if not isinstance(line_items, list) or not line_items:
        return [], ["At least one line item is required."]

    cleaned_line_items = []
    errors = []

    for index, line_item in enumerate(line_items, start=1):
        if not isinstance(line_item, dict):
            errors.append(f"Line item #{index} is invalid.")
            continue

        type_code = _normalize_text(line_item.get("type_code"))
        description = _normalize_text(line_item.get("description"))
        amount, amount_error = _normalize_amount(line_item.get("amount"))
        client_line_id = _normalize_text(line_item.get("client_line_id") or line_item.get("line_id"))

        if not type_code:
            errors.append(f"Line item #{index} type/code is required.")
        if not description:
            errors.append(f"Line item #{index} description is required.")
        if amount_error:
            errors.append(f"Line item #{index}: {amount_error}")
        if type_code and description and amount is not None:
            cleaned_line_items.append(
                {
                    "client_line_id": client_line_id,
                    "type_code": type_code,
                    "description": description,
                    "amount": amount,
                    "sort_order": index,
                }
            )

    return cleaned_line_items, errors


def _sum_line_item_amounts(line_items):
    total_amount = Decimal("0.00")
    for line_item in line_items:
        total_amount += line_item["amount"]
    return total_amount.quantize(Decimal("0.01"))


def _resolve_period_from_entry_date(entry_date):
    return entry_date.month, entry_date.year


def _serialize_client(client: Client) -> dict:
    return {
        "id": client.id,
        "client_name": client.client_name,
        "tin_number": client.tin_number,
        "trade_name": client.trade_name,
        "location": client.location,
        "permit_number": client.permit_number,
        "birthday": client.birthday.isoformat() if client.birthday else "",
        "email": client.email,
        "email_password": client.email_password,
        "orus_account": client.orus_account,
        "orus_password": client.orus_password,
        "custom_fields": client.custom_fields or [],
        "forecast_growth_percent": float((client.forecast_growth_percent or Decimal("0.00")).quantize(Decimal("0.01"))),
    }


def _serialize_line_item(line_item: FinancialRecordLine) -> dict:
    return {
        "id": line_item.id,
        "type_code": line_item.type_code,
        "description": line_item.description,
        "amount": str(line_item.amount),
    }


def _serialize_record(record: FinancialRecord) -> dict:
    line_items = list(record.line_items.all().order_by("sort_order", "id"))

    deadline_completed = False
    if record.deadline_date:
        deadline_completed = FinancialRecord.objects.filter(
            client=record.client,
            entry_date__gte=date(record.deadline_date.year, record.deadline_date.month, 1),
        ).exists()

    return {
        "id": record.id,
        "date": record.entry_date.isoformat() if record.entry_date else "",
        "frequency": record.frequency or FinancialRecord.FREQUENCY_MONTHLY,
        "notes": record.notes or "",
        "deadline_date": record.deadline_date.isoformat() if record.deadline_date else "",
        "deadline_completed": deadline_completed,
        "total_amount": str(record.total_amount or Decimal("0.00")),
        "line_items_count": len(line_items),
        "line_items": [_serialize_line_item(line_item) for line_item in line_items],
    }


def _build_summary(records):
    total_amount = Decimal("0.00")
    line_item_count = 0
    breakdown_map: dict[str, Decimal] = {}

    for record in records:
        total_amount += record.total_amount or Decimal("0.00")

        for line_item in record.line_items.all().order_by("sort_order", "id"):
            line_item_count += 1
            key = line_item.type_code or "Uncategorized"
            breakdown_map[key] = breakdown_map.get(key, Decimal("0.00")) + (line_item.amount or Decimal("0.00"))

    breakdown = [
        {
            "type_code": type_code,
            "total_amount": str(amount.quantize(Decimal("0.01"))),
        }
        for type_code, amount in breakdown_map.items()
    ]
    breakdown.sort(key=lambda item: Decimal(item["total_amount"]), reverse=True)

    return {
        "total_amount": str(total_amount.quantize(Decimal("0.01"))),
        "entry_count": len(records),
        "line_item_count": line_item_count,
        "breakdown": breakdown,
    }


def _resolve_client_for_bookkeeper(bookkeeper, client_id):
    client = Client.objects.filter(id=client_id, bookkeeper=bookkeeper).first()
    if client is None:
        return None, {
            "ok": False,
            "message": "Client not found.",
            "errors": ["Client not found."],
        }
    return client, None


def list_financial_clients_for_bookkeeper(bookkeeper) -> dict:
    latest_record_for_client = (
        FinancialRecord.objects.filter(
            bookkeeper=bookkeeper,
            client_id=OuterRef("pk"),
        )
        .order_by("-entry_date", "-id")
    )

    clients = (
        Client.objects.filter(bookkeeper=bookkeeper)
        .exclude(remarks=Client.REMARK_CLOSED)
        .annotate(
            last_activity=Max("financial_records__entry_date"),
            latest_record_updated_at=Max("financial_records__updated_at"),
            financial_record_count=Count("financial_records", distinct=True),
            last_deadline_date=Subquery(latest_record_for_client.values("deadline_date")[:1]),
        )
        .order_by("-created_at", "-id")
    )

    payload = []
    today = timezone.localdate()
    for client in clients:
        last_activity = client.last_activity.isoformat() if client.last_activity else ""
        activity_candidates = [
            value
            for value in (
                client.latest_record_updated_at,
                client.updated_at,
                client.created_at,
            )
            if value
        ]
        recent_activity_at = max(activity_candidates) if activity_candidates else None
        
        deadline_date = client.last_deadline_date.isoformat() if client.last_deadline_date else ""
        days_remaining = None
        deadline_completed = False
        if client.last_deadline_date:
            days_remaining = (client.last_deadline_date - today).days
            deadline_completed = FinancialRecord.objects.filter(
                client=client,
                entry_date__gte=date(client.last_deadline_date.year, client.last_deadline_date.month, 1),
            ).exists()

        payload.append(
            {
                "id": client.id,
                "client_name": client.client_name,
                "tin_number": client.tin_number,
                "trade_name": client.trade_name,
                "last_activity": last_activity,
                "latest_record_updated_at": client.latest_record_updated_at.isoformat() if client.latest_record_updated_at else "",
                "recent_activity_at": recent_activity_at.isoformat() if recent_activity_at else "",
                "activity_state": "active" if last_activity else "none",
                "financial_record_count": client.financial_record_count,
                "deadline_date": deadline_date,
                "days_remaining": days_remaining,
                "deadline_completed": deadline_completed,
            }
        )

    return {
        "ok": True,
        "clients": payload,
    }


def list_records_for_client_period(bookkeeper, client_id: int, month_value=None, year_value=None) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    is_all = str(month_value).strip().lower() == "all"

    if is_all:
        records = list(
            FinancialRecord.objects.filter(
                bookkeeper=bookkeeper,
                client=client,
            )
            .prefetch_related("line_items")
            .order_by("-entry_date", "-id")
        )
        month = "all"
        year = "all"
    else:
        month, month_error = _normalize_month(month_value)
        if month_error:
            return {
                "ok": False,
                "message": month_error,
                "errors": [month_error],
            }

        year, year_error = _normalize_year(year_value)
        if year_error:
            return {
                "ok": False,
                "message": year_error,
                "errors": [year_error],
            }

        period = Period.objects.filter(client=client, month=month, year=year).first()
        if period is None:
            records = []
        else:
            records = list(
                FinancialRecord.objects.filter(
                    bookkeeper=bookkeeper,
                    client=client,
                    period=period,
                )
                .prefetch_related("line_items")
                .order_by("-entry_date", "-id")
            )

    has_any_records = FinancialRecord.objects.filter(
        bookkeeper=bookkeeper,
        client=client,
    ).exists()

    if is_all:
        prior_frequencies = []
    else:
        period_start = date(year, month, 1)
        prior_frequencies = list(
            FinancialRecord.objects.filter(
                bookkeeper=bookkeeper,
                client=client,
                entry_date__lt=period_start,
            )
            .values_list("frequency", flat=True)
            .distinct()
        )

    return {
        "ok": True,
        "client": _serialize_client(client),
        "period": {
            "month": month,
            "month_label": "All Periods" if is_all else MONTH_NUMBER_TO_NAME.get(month, str(month)),
            "year": year,
        },
        "records": [_serialize_record(record) for record in records],
        "summary": _build_summary(records),
        "has_any_records": has_any_records,
        "prior_frequencies": prior_frequencies,
    }


def get_last_record_for_client_period(
    bookkeeper,
    client_id: int,
    month_value=None,
    year_value=None,
    frequency_value=None,
) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    month, month_error = _normalize_month(month_value)
    if month_error:
        return {
            "ok": False,
            "message": month_error,
            "errors": [month_error],
        }

    year, year_error = _normalize_year(year_value)
    if year_error:
        return {
            "ok": False,
            "message": year_error,
            "errors": [year_error],
        }

    frequency, frequency_error = _normalize_frequency(frequency_value)
    if frequency_error:
        return {
            "ok": False,
            "message": frequency_error,
            "errors": [frequency_error],
        }

    period_start = date(year, month, 1)
    record = (
        FinancialRecord.objects.filter(
            bookkeeper=bookkeeper,
            client=client,
            entry_date__lt=period_start,
            frequency=frequency,
        )
        .prefetch_related("line_items")
        .order_by("-entry_date", "-id")
        .first()
    )

    if record is None or record.entry_date is None:
        message = "No previous entry found for this frequency."
        return {
            "ok": False,
            "message": message,
            "errors": [message],
            "no_record": True,
        }

    source_month = record.entry_date.month
    source_year = record.entry_date.year
    return {
        "ok": True,
        "client": _serialize_client(client),
        "source_period": {
            "month": source_month,
            "month_label": MONTH_NUMBER_TO_NAME.get(source_month, str(source_month)),
            "year": source_year,
        },
        "record": _serialize_record(record),
    }


def list_transactions_for_client_range(bookkeeper, client_id: int, date_from_value, date_to_value) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    date_from, date_from_error = _normalize_required_date(date_from_value, "Date From")
    if date_from_error:
        return {
            "ok": False,
            "message": date_from_error,
            "errors": [date_from_error],
        }

    date_to, date_to_error = _normalize_required_date(date_to_value, "Date To")
    if date_to_error:
        return {
            "ok": False,
            "message": date_to_error,
            "errors": [date_to_error],
        }

    if date_from > date_to:
        message = "Date From cannot be later than Date To."
        return {
            "ok": False,
            "message": message,
            "errors": [message],
        }

    records = list(
        FinancialRecord.objects.filter(
            bookkeeper=bookkeeper,
            client=client,
            entry_date__gte=date_from,
            entry_date__lte=date_to,
        )
        .prefetch_related("line_items")
        .order_by("entry_date", "id")
    )

    rows = []
    total_amount = Decimal("0.00")
    line_item_count = 0

    for record in records:
        record_notes = record.notes or ""
        record_date = record.entry_date.isoformat() if record.entry_date else ""
        line_items = record.line_items.all().order_by("sort_order", "id")
        for line_item in line_items:
            amount_value = line_item.amount or Decimal("0.00")
            total_amount += amount_value
            line_item_count += 1

            rows.append(
                {
                    "entry_date": record_date,
                    "type_code": line_item.type_code,
                    "description": line_item.description,
                    "amount": str(amount_value.quantize(Decimal("0.01"))),
                    "notes": record_notes,
                }
            )

    return {
        "ok": True,
        "client": _serialize_client(client),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "summary": {
            "entry_count": len(records),
            "line_item_count": line_item_count,
            "total_amount": str(total_amount.quantize(Decimal("0.01"))),
        },
        "rows": rows,
    }


def create_record_for_client_period(bookkeeper, client_id: int, data: dict) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    entry_date, entry_date_error = _normalize_entry_date(data.get("date"))
    if entry_date_error:
        return {
            "ok": False,
            "message": entry_date_error,
            "errors": [entry_date_error],
        }

    month, year = _resolve_period_from_entry_date(entry_date)

    frequency, frequency_error = _normalize_frequency(data.get("frequency"))
    if frequency_error:
        return {
            "ok": False,
            "message": frequency_error,
            "errors": [frequency_error],
        }

    deadline_date, deadline_date_error = _normalize_optional_date(data.get("deadline_date"), "Deadline Date")
    if deadline_date_error:
        return {
            "ok": False,
            "message": deadline_date_error,
            "errors": [deadline_date_error],
        }

    notes = _normalize_text(data.get("notes"))
    line_items, line_item_errors = _normalize_line_items(data.get("line_items"))
    if line_item_errors:
        return {
            "ok": False,
            "message": line_item_errors[0],
            "errors": line_item_errors,
        }

    for line_item in line_items:
        line_id = line_item.get("client_line_id") or f"line-{line_item['sort_order']}"
        line_item["client_line_id"] = line_id

    with transaction.atomic():
        period, _ = Period.objects.get_or_create(client=client, month=month, year=year)

        record = FinancialRecord.objects.create(
            bookkeeper=bookkeeper,
            client=client,
            period=period,
            entry_date=entry_date,
            frequency=frequency,
            notes=notes,
            deadline_date=deadline_date,
            total_amount=_sum_line_item_amounts(line_items),
        )

        for line_item in line_items:
            FinancialRecordLine.objects.create(
                record=record,
                type_code=line_item["type_code"],
                description=line_item["description"],
                amount=line_item["amount"],
                sort_order=line_item["sort_order"],
            )

    from safebooks.services.client_service import check_and_promote_new_client
    check_and_promote_new_client(client)

    refreshed_record = FinancialRecord.objects.filter(id=record.id).prefetch_related("line_items").first()
    from safebooks.services.client_notification_service import send_financial_record_created_email
    email_notification = send_financial_record_created_email(refreshed_record)

    return {
        "ok": True,
        "message": "Financial entry added successfully.",
        "record": _serialize_record(refreshed_record),
        "client_email_notification": email_notification,
    }


def update_record_for_client_period(bookkeeper, client_id: int, record_id: int, data: dict) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    record = (
        FinancialRecord.objects.filter(id=record_id, bookkeeper=bookkeeper, client=client)
        .select_related("period")
        .prefetch_related("line_items")
        .first()
    )
    if record is None:
        return {
            "ok": False,
            "message": "Financial record not found.",
            "errors": ["Financial record not found."],
        }

    entry_date_value = data.get("date", record.entry_date.isoformat())
    entry_date, entry_date_error = _normalize_entry_date(entry_date_value)
    if entry_date_error:
        return {
            "ok": False,
            "message": entry_date_error,
            "errors": [entry_date_error],
        }

    month, year = _resolve_period_from_entry_date(entry_date)

    notes = _normalize_text(data.get("notes", record.notes))

    if "deadline_date" in data:
        deadline_date, deadline_date_error = _normalize_optional_date(data.get("deadline_date"), "Deadline Date")
        if deadline_date_error:
            return {
                "ok": False,
                "message": deadline_date_error,
                "errors": [deadline_date_error],
            }
    else:
        deadline_date = record.deadline_date

    if "frequency" in data:
        frequency, frequency_error = _normalize_frequency(data.get("frequency"))
        if frequency_error:
            return {
                "ok": False,
                "message": frequency_error,
                "errors": [frequency_error],
            }
    else:
        frequency = record.frequency or FinancialRecord.FREQUENCY_MONTHLY

    if "line_items" in data:
        line_items, line_item_errors = _normalize_line_items(data.get("line_items"))
        if line_item_errors:
            return {
                "ok": False,
                "message": line_item_errors[0],
                "errors": line_item_errors,
            }
        for line_item in line_items:
            line_id = line_item.get("client_line_id") or f"line-{line_item['sort_order']}"
            line_item["client_line_id"] = line_id
    else:
        line_items = [
            {
                "type_code": line_item.type_code,
                "description": line_item.description,
                "amount": line_item.amount,
                "sort_order": line_item.sort_order,
            }
            for line_item in record.line_items.all().order_by("sort_order", "id")
        ]

    with transaction.atomic():
        period, _ = Period.objects.get_or_create(client=client, month=month, year=year)

        record.period = period
        record.entry_date = entry_date
        record.frequency = frequency
        record.notes = notes
        record.deadline_date = deadline_date
        record.total_amount = _sum_line_item_amounts(line_items)
        record.save(update_fields=["period", "entry_date", "frequency", "notes", "deadline_date", "total_amount", "updated_at"])

        if "line_items" in data:
            record.line_items.all().delete()
            for line_item in line_items:
                FinancialRecordLine.objects.create(
                    record=record,
                    type_code=line_item["type_code"],
                    description=line_item["description"],
                    amount=line_item["amount"],
                    sort_order=line_item["sort_order"],
                )

    from safebooks.services.client_service import check_and_promote_new_client
    check_and_promote_new_client(client)

    refreshed_record = FinancialRecord.objects.filter(id=record.id).prefetch_related("line_items").first()

    return {
        "ok": True,
        "message": "Financial entry updated successfully.",
        "record": _serialize_record(refreshed_record),
    }


def delete_record_for_client(bookkeeper, client_id: int, record_id: int) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    record = FinancialRecord.objects.filter(id=record_id, bookkeeper=bookkeeper, client=client).first()
    if record is None:
        return {
            "ok": False,
            "message": "Financial record not found.",
            "errors": ["Financial record not found."],
        }

    period_id = record.period_id
    deleted_record = {
        "id": record.id,
        "date": record.entry_date.isoformat() if record.entry_date else "",
    }
    record.delete()

    if not FinancialRecord.objects.filter(period_id=period_id).exists():
        Period.objects.filter(id=period_id).delete()

    return {
        "ok": True,
        "message": "Financial entry deleted successfully.",
        "record": deleted_record,
    }
