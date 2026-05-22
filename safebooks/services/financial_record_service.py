from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Max

from safebooks.models import Client, FinancialRecord, FinancialRecordLine, Period


MONTH_NUMBER_TO_NAME = dict(Period.MONTH_CHOICES)
MONTH_NAME_TO_NUMBER = {label.lower(): number for number, label in Period.MONTH_CHOICES}
CALC_OPERATIONS = {
    FinancialRecordLine.CALC_ADD,
    FinancialRecordLine.CALC_SUBTRACT,
    FinancialRecordLine.CALC_MULTIPLY,
    FinancialRecordLine.CALC_DIVIDE,
    FinancialRecordLine.CALC_PERCENT,
}
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


def _normalize_calc_operation(value):
    cleaned_value = _normalize_text(value).lower()
    if not cleaned_value:
        return "", None

    if cleaned_value not in CALC_OPERATIONS:
        return None, "Invalid calculation operation."

    return cleaned_value, None


def _normalize_calc_percent(value):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, None

    try:
        percent = Decimal(cleaned_value)
    except (InvalidOperation, TypeError):
        return None, "Percent must be a valid number."

    if percent < 0:
        return None, "Percent cannot be negative."

    return percent.quantize(Decimal("0.01")), None


def _normalize_calc_original_amount(value):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, None

    amount, amount_error = _normalize_amount(cleaned_value)
    if amount_error:
        return None, f"Original amount: {amount_error}"

    return amount, None


def _normalize_calc_applied(value) -> bool:
    if isinstance(value, bool):
        return value

    cleaned_value = _normalize_text(value).lower()
    return cleaned_value in {"1", "true", "yes", "applied"}


def _calculate_line_result(line_item, target_amount: Decimal | None):
    operation = line_item.get("calc_operation")
    applied = line_item.get("calc_applied")
    if not applied or not operation:
        return None, None

    base_amount = line_item.get("amount")
    if base_amount is None:
        return None, None

    if operation == FinancialRecordLine.CALC_PERCENT:
        percent = line_item.get("calc_percent")
        if percent is None:
            return None, "Percent is required for percentage calculations."
        base_for_percent = line_item.get("calc_original_amount") or base_amount
        result = base_for_percent * (percent / Decimal("100"))
        return result.quantize(Decimal("0.01")), None

    if target_amount is None:
        return None, "Target line item is required for calculations."

    if operation == FinancialRecordLine.CALC_ADD:
        return (base_amount + target_amount).quantize(Decimal("0.01")), None
    if operation == FinancialRecordLine.CALC_SUBTRACT:
        return (base_amount - target_amount).quantize(Decimal("0.01")), None
    if operation == FinancialRecordLine.CALC_MULTIPLY:
        return (base_amount * target_amount).quantize(Decimal("0.01")), None
    if operation == FinancialRecordLine.CALC_DIVIDE:
        if target_amount == 0:
            return None, "Division by zero is not allowed."
        return (base_amount / target_amount).quantize(Decimal("0.01")), None

    return None, "Invalid calculation operation."


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
        calc_operation, calc_operation_error = _normalize_calc_operation(line_item.get("calc_operation"))
        calc_target_id = _normalize_text(line_item.get("calc_target_id"))
        calc_percent, calc_percent_error = _normalize_calc_percent(line_item.get("calc_percent"))
        calc_original_amount, calc_original_error = _normalize_calc_original_amount(line_item.get("calc_original_amount"))
        calc_applied = _normalize_calc_applied(line_item.get("calc_applied"))

        if not type_code:
            errors.append(f"Line item #{index} type/code is required.")
        if not description:
            errors.append(f"Line item #{index} description is required.")
        if amount_error:
            errors.append(f"Line item #{index}: {amount_error}")
        if calc_operation_error:
            errors.append(f"Line item #{index}: {calc_operation_error}")
        if calc_percent_error:
            errors.append(f"Line item #{index}: {calc_percent_error}")
        if calc_original_error:
            errors.append(f"Line item #{index}: {calc_original_error}")

        if type_code and description and amount is not None:
            cleaned_line_items.append(
                {
                    "client_line_id": client_line_id,
                    "type_code": type_code,
                    "description": description,
                    "amount": amount,
                    "calc_operation": calc_operation,
                    "calc_target_id": calc_target_id,
                    "calc_percent": calc_percent,
                    "calc_original_amount": calc_original_amount,
                    "calc_applied": calc_applied,
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
    }


def _serialize_line_item(line_item: FinancialRecordLine) -> dict:
    return {
        "id": line_item.id,
        "type_code": line_item.type_code,
        "description": line_item.description,
        "amount": str(line_item.amount),
        "calc_operation": line_item.calc_operation or "",
        "calc_target_id": line_item.calc_target_id,
        "calc_percent": str(line_item.calc_percent) if line_item.calc_percent is not None else "",
        "calc_result": str(line_item.calc_result) if line_item.calc_result is not None else "",
        "calc_original_amount": str(line_item.calc_original_amount) if line_item.calc_original_amount is not None else "",
        "calc_applied": bool(line_item.calc_applied),
    }


def _serialize_record(record: FinancialRecord) -> dict:
    line_items = list(record.line_items.all().order_by("sort_order", "id"))

    return {
        "id": record.id,
        "date": record.entry_date.isoformat() if record.entry_date else "",
        "frequency": record.frequency or FinancialRecord.FREQUENCY_MONTHLY,
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

    has_any_records = FinancialRecord.objects.filter(
        bookkeeper=bookkeeper,
        client=client,
    ).exists()

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
            "month_label": MONTH_NUMBER_TO_NAME.get(month, str(month)),
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

    notes = _normalize_text(data.get("notes"))
    line_items, line_item_errors = _normalize_line_items(data.get("line_items"))
    if line_item_errors:
        return {
            "ok": False,
            "message": line_item_errors[0],
            "errors": line_item_errors,
        }

    line_item_map = {}
    for line_item in line_items:
        line_id = line_item.get("client_line_id") or f"line-{line_item['sort_order']}"
        line_item["client_line_id"] = line_id
        line_item_map[line_id] = line_item

    calc_errors = []
    for line_item in line_items:
        operation = line_item.get("calc_operation")
        target_id = line_item.get("calc_target_id")
        target_item = line_item_map.get(target_id) if target_id else None
        target_amount = target_item.get("amount") if target_item else None
        result, calc_error = _calculate_line_result(line_item, target_amount)
        if calc_error:
            calc_errors.append(calc_error)
        line_item["calc_result"] = result

        if operation == FinancialRecordLine.CALC_PERCENT and line_item.get("calc_applied") and result is not None:
            if line_item.get("calc_original_amount") is None:
                line_item["calc_original_amount"] = line_item.get("amount")
            line_item["amount"] = result

    if calc_errors:
        return {
            "ok": False,
            "message": calc_errors[0],
            "errors": calc_errors,
        }

    with transaction.atomic():
        period, _ = Period.objects.get_or_create(client=client, month=month, year=year)

        record = FinancialRecord.objects.create(
            bookkeeper=bookkeeper,
            client=client,
            period=period,
            entry_date=entry_date,
            frequency=frequency,
            notes=notes,
            total_amount=_sum_line_item_amounts(line_items),
        )

        created_line_items = {}
        for line_item in line_items:
            created_line = FinancialRecordLine.objects.create(
                record=record,
                type_code=line_item["type_code"],
                description=line_item["description"],
                amount=line_item["amount"],
                sort_order=line_item["sort_order"],
                calc_operation=line_item.get("calc_operation") or "",
                calc_percent=line_item.get("calc_percent"),
                calc_result=line_item.get("calc_result"),
                calc_original_amount=line_item.get("calc_original_amount"),
                calc_applied=bool(line_item.get("calc_applied")),
            )
            created_line_items[line_item["client_line_id"]] = created_line

        for line_item in line_items:
            target_id = line_item.get("calc_target_id")
            operation = line_item.get("calc_operation")
            if not target_id or operation == FinancialRecordLine.CALC_PERCENT:
                continue

            source_line = created_line_items.get(line_item["client_line_id"])
            target_line = created_line_items.get(target_id)
            if source_line and target_line:
                source_line.calc_target = target_line
                source_line.save(update_fields=["calc_target"])

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

        line_item_map = {}
        for line_item in line_items:
            line_id = line_item.get("client_line_id") or f"line-{line_item['sort_order']}"
            line_item["client_line_id"] = line_id
            line_item_map[line_id] = line_item

        calc_errors = []
        for line_item in line_items:
            target_id = line_item.get("calc_target_id")
            target_item = line_item_map.get(target_id) if target_id else None
            target_amount = target_item.get("amount") if target_item else None
            result, calc_error = _calculate_line_result(line_item, target_amount)
            if calc_error:
                calc_errors.append(calc_error)
            line_item["calc_result"] = result

            if line_item.get("calc_operation") == FinancialRecordLine.CALC_PERCENT and line_item.get("calc_applied") and result is not None:
                if line_item.get("calc_original_amount") is None:
                    line_item["calc_original_amount"] = line_item.get("amount")
                line_item["amount"] = result

        if calc_errors:
            return {
                "ok": False,
                "message": calc_errors[0],
                "errors": calc_errors,
            }
    else:
        line_items = [
            {
                "type_code": line_item.type_code,
                "description": line_item.description,
                "amount": line_item.amount,
                "calc_operation": line_item.calc_operation,
                "calc_target_id": line_item.calc_target_id,
                "calc_percent": line_item.calc_percent,
                "calc_result": line_item.calc_result,
                "calc_original_amount": line_item.calc_original_amount,
                "calc_applied": line_item.calc_applied,
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
        record.total_amount = _sum_line_item_amounts(line_items)
        record.save(update_fields=["period", "entry_date", "frequency", "notes", "total_amount", "updated_at"])

        if "line_items" in data:
            record.line_items.all().delete()
            created_line_items = {}
            for line_item in line_items:
                created_line = FinancialRecordLine.objects.create(
                    record=record,
                    type_code=line_item["type_code"],
                    description=line_item["description"],
                    amount=line_item["amount"],
                    sort_order=line_item["sort_order"],
                    calc_operation=line_item.get("calc_operation") or "",
                    calc_percent=line_item.get("calc_percent"),
                    calc_result=line_item.get("calc_result"),
                    calc_original_amount=line_item.get("calc_original_amount"),
                    calc_applied=bool(line_item.get("calc_applied")),
                )
                created_line_items[line_item["client_line_id"]] = created_line

            for line_item in line_items:
                target_id = line_item.get("calc_target_id")
                operation = line_item.get("calc_operation")
                if not target_id or operation == FinancialRecordLine.CALC_PERCENT:
                    continue

                source_line = created_line_items.get(line_item["client_line_id"])
                target_line = created_line_items.get(target_id)
                if source_line and target_line:
                    source_line.calc_target = target_line
                    source_line.save(update_fields=["calc_target"])

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
