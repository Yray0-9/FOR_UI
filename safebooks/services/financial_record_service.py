from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Max

from safebooks.models import Client, FinancialRecord, FinancialRecordLine, Period


MONTH_NUMBER_TO_NAME = dict(Period.MONTH_CHOICES)
MONTH_NAME_TO_NUMBER = {label.lower(): number for number, label in Period.MONTH_CHOICES}


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
        return date.fromisoformat(cleaned_value), None
    except ValueError:
        return None, "Entry date must use YYYY-MM-DD format."


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

        if not type_code:
            errors.append(f"Line item #{index} type/code is required.")
        if not description:
            errors.append(f"Line item #{index} description is required.")
        if amount_error:
            errors.append(f"Line item #{index}: {amount_error}")

        if type_code and description and amount is not None:
            cleaned_line_items.append(
                {
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


def _validate_entry_date_in_period(entry_date, month, year):
    if entry_date.month != month or entry_date.year != year:
        return "Entry date must be within the selected period month and year."
    return None


def _serialize_client(client: Client) -> dict:
    return {
        "id": client.id,
        "client_name": client.client_name,
        "tin_number": client.tin_number,
        "trade_name": client.trade_name,
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

    return {
        "id": record.id,
        "date": record.entry_date.isoformat() if record.entry_date else "",
        "notes": record.notes or "",
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
    clients = (
        Client.objects.filter(bookkeeper=bookkeeper)
        .annotate(
            last_activity=Max("financial_records__entry_date"),
            financial_record_count=Count("financial_records", distinct=True),
        )
        .order_by("client_name", "id")
    )

    payload = []
    for client in clients:
        last_activity = client.last_activity.isoformat() if client.last_activity else ""
        payload.append(
            {
                "id": client.id,
                "client_name": client.client_name,
                "tin_number": client.tin_number,
                "trade_name": client.trade_name,
                "last_activity": last_activity,
                "activity_state": "active" if last_activity else "none",
                "financial_record_count": client.financial_record_count,
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

    return {
        "ok": True,
        "client": _serialize_client(client),
        "period": {
            "month": month,
            "month_label": MONTH_NUMBER_TO_NAME.get(month, str(month)),
            "year": year,
        },
        "records": [_serialize_record(record) for record in records],
        "summary": _build_summary(records),
    }


def create_record_for_client_period(bookkeeper, client_id: int, data: dict) -> dict:
    client, error_response = _resolve_client_for_bookkeeper(bookkeeper, client_id)
    if error_response:
        return error_response

    month, month_error = _normalize_month(data.get("month"))
    if month_error:
        return {
            "ok": False,
            "message": month_error,
            "errors": [month_error],
        }

    year, year_error = _normalize_year(data.get("year"))
    if year_error:
        return {
            "ok": False,
            "message": year_error,
            "errors": [year_error],
        }

    entry_date, entry_date_error = _normalize_entry_date(data.get("date"))
    if entry_date_error:
        return {
            "ok": False,
            "message": entry_date_error,
            "errors": [entry_date_error],
        }

    period_date_error = _validate_entry_date_in_period(entry_date, month, year)
    if period_date_error:
        return {
            "ok": False,
            "message": period_date_error,
            "errors": [period_date_error],
        }

    notes = _normalize_text(data.get("notes"))
    line_items, line_item_errors = _normalize_line_items(data.get("line_items"))
    if line_item_errors:
        return {
            "ok": False,
            "message": line_item_errors[0],
            "errors": line_item_errors,
        }

    with transaction.atomic():
        period, _ = Period.objects.get_or_create(client=client, month=month, year=year)

        record = FinancialRecord.objects.create(
            bookkeeper=bookkeeper,
            client=client,
            period=period,
            entry_date=entry_date,
            notes=notes,
            total_amount=_sum_line_item_amounts(line_items),
        )

        FinancialRecordLine.objects.bulk_create(
            [
                FinancialRecordLine(
                    record=record,
                    type_code=line_item["type_code"],
                    description=line_item["description"],
                    amount=line_item["amount"],
                    sort_order=line_item["sort_order"],
                )
                for line_item in line_items
            ]
        )

    refreshed_record = FinancialRecord.objects.filter(id=record.id).prefetch_related("line_items").first()

    return {
        "ok": True,
        "message": "Financial entry added successfully.",
        "record": _serialize_record(refreshed_record),
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

    month, month_error = _normalize_month(data.get("month", record.period.month))
    if month_error:
        return {
            "ok": False,
            "message": month_error,
            "errors": [month_error],
        }

    year, year_error = _normalize_year(data.get("year", record.period.year))
    if year_error:
        return {
            "ok": False,
            "message": year_error,
            "errors": [year_error],
        }

    entry_date_value = data.get("date", record.entry_date.isoformat())
    entry_date, entry_date_error = _normalize_entry_date(entry_date_value)
    if entry_date_error:
        return {
            "ok": False,
            "message": entry_date_error,
            "errors": [entry_date_error],
        }

    period_date_error = _validate_entry_date_in_period(entry_date, month, year)
    if period_date_error:
        return {
            "ok": False,
            "message": period_date_error,
            "errors": [period_date_error],
        }

    notes = _normalize_text(data.get("notes", record.notes))

    if "line_items" in data:
        line_items, line_item_errors = _normalize_line_items(data.get("line_items"))
        if line_item_errors:
            return {
                "ok": False,
                "message": line_item_errors[0],
                "errors": line_item_errors,
            }
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
        record.notes = notes
        record.total_amount = _sum_line_item_amounts(line_items)
        record.save(update_fields=["period", "entry_date", "notes", "total_amount", "updated_at"])

        if "line_items" in data:
            record.line_items.all().delete()
            FinancialRecordLine.objects.bulk_create(
                [
                    FinancialRecordLine(
                        record=record,
                        type_code=line_item["type_code"],
                        description=line_item["description"],
                        amount=line_item["amount"],
                        sort_order=line_item["sort_order"],
                    )
                    for line_item in line_items
                ]
            )

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
