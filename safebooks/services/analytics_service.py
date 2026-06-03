from collections import defaultdict
from datetime import date
from decimal import Decimal
import re

from django.db.models import Q
from django.utils import timezone

from safebooks.models import Client, FinancialRecord, FinancialRecordLine


TAX_TYPE_CODES = {
    "1701",
    "1701a",
    "1702",
    "2550m",
    "2550q",
    "2551m",
    "2551q",
    "0619e",
    "0619f",
    "1601c",
    "1601eq",
    "1701q",
    "2370",
}

TAX_ANNUAL_FORM_CODES = {
    "1701",
    "1701a",
    "1702",
}

TAX_QUARTERLY_FORM_CODES = {
    "1701q",
    "1702q",
    "2550q",
    "2551q",
    "1601eq",
}

TAX_MONTHLY_FORM_CODES = {
    "0619e",
    "0619f",
    "1601c",
    "2550m",
    "2551m",
}

TAX_CODE_PATTERN = re.compile(r"^\d{4}[a-z]{0,2}$", re.IGNORECASE)

TAX_KEYWORDS = (
    "tax",
    "vat",
    "withholding",
    "wht",
    "percentage tax",
    "income tax",
)

EXPENSE_KEYWORDS = (
    "expense",
    "expenses",
    "cost",
    "fee",
    "professional fee",
    "rent",
    "utility",
    "utilities",
    "salary",
    "payroll",
    "supplies",
    "fuel",
    "transport",
    "allowance",
    "purchase",
    "materials",
)

SALES_KEYWORDS = (
    "sale",
    "sales",
    "revenue",
    "income",
    "service",
    "collection",
)


def _normalize_search_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())


def _normalize_type_code_label(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_type_code_key(value: str) -> str:
    return _normalize_type_code_label(value).lower()


NORMALIZED_TAX_KEYWORDS = tuple(_normalize_search_text(keyword) for keyword in TAX_KEYWORDS)
NORMALIZED_EXPENSE_KEYWORDS = tuple(_normalize_search_text(keyword) for keyword in EXPENSE_KEYWORDS)
NORMALIZED_SALES_KEYWORDS = tuple(_normalize_search_text(keyword) for keyword in SALES_KEYWORDS)



def _contains_keyword(normalized_text: str, normalized_keyword: str) -> bool:
    if not normalized_keyword:
        return False
    return f" {normalized_keyword} " in f" {normalized_text} "

REMARK_TO_LABEL = {
    Client.REMARK_NEW: "New",
    Client.REMARK_ACTIVE: "Active",
    Client.REMARK_SEPARATED: "Separated",
    Client.REMARK_CLOSED: "Closed",
}

REMARK_TO_TITLE = {
    Client.REMARK_NEW: "New Client",
    Client.REMARK_ACTIVE: "Active Client",
    Client.REMARK_SEPARATED: "Separated Client",
    Client.REMARK_CLOSED: "Closed Client",
}

REMARK_TO_DESCRIPTION = {
    Client.REMARK_NEW: "This client is newly registered and is in their first bookkeeping month.",
    Client.REMARK_ACTIVE: "This client actively pays and files their compliance regularly.",
    Client.REMARK_SEPARATED: "This client did not file/pay compliance for the year and is separated for the new bookkeeping year.",
    Client.REMARK_CLOSED: "This client has closed their business.",
}

ALL_CLIENTS_REMARK_DESCRIPTIONS = {
    Client.REMARK_NEW: "Most clients are newly registered in their onboarding phase.",
    Client.REMARK_ACTIVE: "Most clients actively pay and file their compliance regularly.",
    Client.REMARK_SEPARATED: "Multiple clients are separated due to missing filing activity for the year.",
    Client.REMARK_CLOSED: "Some clients have closed their business.",
}

MONTH_SHORT_NAMES = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

FREQUENCY_LABELS = {
    FinancialRecord.FREQUENCY_MONTHLY: "Monthly",
    FinancialRecord.FREQUENCY_QUARTERLY: "Quarterly",
    FinancialRecord.FREQUENCY_ANNUALLY: "Annually",
}

FREQUENCY_INTERVALS = {
    FinancialRecord.FREQUENCY_MONTHLY: 1,
    FinancialRecord.FREQUENCY_QUARTERLY: 3,
    FinancialRecord.FREQUENCY_ANNUALLY: 12,
}

FORECAST_CATEGORIES = ("sales", "expenses", "tax")
FORECAST_LIMITED_DATA_MESSAGE = "Groups with fewer than 2 records use a one-point Linear Regression baseline until more history is available."
FORECAST_MIXED_FREQUENCY = "mixed"


def _to_money_number(value: Decimal) -> float:
    return float((value or Decimal("0.00")).quantize(Decimal("0.01")))


def _format_percent(value: Decimal) -> str:
    normalized = (value or Decimal("0.00")).quantize(Decimal("0.01"))
    percent_text = f"{normalized:.2f}"
    return percent_text.rstrip("0").rstrip(".")


def _empty_bucket() -> dict:
    return {
        "sales": Decimal("0.00"),
        "expenses": Decimal("0.00"),
        "tax": Decimal("0.00"),
    }


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    absolute_month = (year * 12) + (month - 1) + offset
    shifted_year = absolute_month // 12
    shifted_month = (absolute_month % 12) + 1
    return shifted_year, shifted_month


def _recent_month_slots(reference_date: date, count: int = 6) -> list[tuple[int, int, str]]:
    slots: list[tuple[int, int, str]] = []
    starting_offset = -(count - 1)

    for index in range(count):
        year, month = _shift_month(reference_date.year, reference_date.month, starting_offset + index)
        slots.append((year, month, MONTH_SHORT_NAMES.get(month, str(month))))

    return slots


def _classify_line_item(type_code: str, description: str) -> str:
    normalized_type_code = str(type_code or "").strip().lower()
    searchable_text = _normalize_search_text(f"{type_code or ''} {description or ''}")

    if normalized_type_code.startswith("bir form"):
        return "tax"
    if normalized_type_code in TAX_TYPE_CODES:
        return "tax"
    if TAX_CODE_PATTERN.match(normalized_type_code):
        return "tax"
    if any(_contains_keyword(searchable_text, keyword) for keyword in NORMALIZED_TAX_KEYWORDS):
        return "tax"
    if any(_contains_keyword(searchable_text, keyword) for keyword in NORMALIZED_EXPENSE_KEYWORDS):
        return "expenses"
    if any(_contains_keyword(searchable_text, keyword) for keyword in NORMALIZED_SALES_KEYWORDS):
        return "sales"

    return "sales"


def _contains_tax_form_code(raw_text: str, form_code: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(form_code.lower())}(?:v\d+)?(?![a-z0-9])"
    return re.search(pattern, raw_text) is not None


def _extract_tax_form_code(type_code: str, description: str) -> str:
    raw_text = f"{type_code or ''} {description or ''}".lower()
    form_codes = (
        TAX_QUARTERLY_FORM_CODES
        | TAX_MONTHLY_FORM_CODES
        | TAX_ANNUAL_FORM_CODES
    )

    for form_code in sorted(form_codes, key=len, reverse=True):
        if _contains_tax_form_code(raw_text, form_code):
            return form_code

    return ""


def _infer_tax_line_frequency(type_code: str, description: str) -> str | None:
    raw_text = f"{type_code or ''} {description or ''}".lower()
    searchable_text = _normalize_search_text(raw_text)

    if any(_contains_keyword(searchable_text, keyword) for keyword in ("annual", "annually", "yearly")):
        return FinancialRecord.FREQUENCY_ANNUALLY
    if any(_contains_keyword(searchable_text, keyword) for keyword in ("quarterly", "quarter")):
        return FinancialRecord.FREQUENCY_QUARTERLY
    if any(_contains_keyword(searchable_text, keyword) for keyword in ("monthly", "month")):
        return FinancialRecord.FREQUENCY_MONTHLY

    if any(_contains_tax_form_code(raw_text, form_code) for form_code in TAX_QUARTERLY_FORM_CODES):
        return FinancialRecord.FREQUENCY_QUARTERLY
    if any(_contains_tax_form_code(raw_text, form_code) for form_code in TAX_MONTHLY_FORM_CODES):
        return FinancialRecord.FREQUENCY_MONTHLY
    if any(_contains_tax_form_code(raw_text, form_code) for form_code in TAX_ANNUAL_FORM_CODES):
        return FinancialRecord.FREQUENCY_ANNUALLY

    return None


def _resolve_line_forecast_frequency(line: FinancialRecordLine, category: str) -> str:
    if category == "tax":
        inferred_frequency = _infer_tax_line_frequency(line.type_code, line.description)
        if inferred_frequency:
            return inferred_frequency

    return _normalize_frequency(line.record.frequency)


def _forecast_group_key(line: FinancialRecordLine, category: str) -> str:
    if category == "tax":
        form_code = _extract_tax_form_code(line.type_code, line.description)
        if form_code:
            return f"{category}:{form_code}"

    type_key = _normalize_type_code_key(line.type_code)
    return f"{category}:{type_key}" if type_key else category


def _resolve_all_clients_remarks(clients: list[Client]) -> str:
    remark_counts = {
        Client.REMARK_NEW: 0,
        Client.REMARK_ACTIVE: 0,
        Client.REMARK_SEPARATED: 0,
    }

    for client in clients:
        if client.remarks == Client.REMARK_CLOSED:
            continue
        level = client.remarks if client.remarks in remark_counts else Client.REMARK_NEW
        remark_counts[level] += 1

    if remark_counts[Client.REMARK_SEPARATED] > 0:
        return Client.REMARK_SEPARATED
    if remark_counts[Client.REMARK_ACTIVE] > 0:
        return Client.REMARK_ACTIVE
    return Client.REMARK_NEW


def _build_remarks_insight(scope_client: Client | None, all_clients: list[Client]) -> dict:
    if scope_client is not None:
        level = scope_client.remarks if scope_client.remarks in REMARK_TO_TITLE else Client.REMARK_NEW
        return {
            "level": level,
            "title": REMARK_TO_TITLE[level],
            "description": REMARK_TO_DESCRIPTION[level],
        }

    level = _resolve_all_clients_remarks(all_clients)
    return {
        "level": level,
        "title": REMARK_TO_TITLE[level],
        "description": ALL_CLIENTS_REMARK_DESCRIPTIONS[level],
    }


def _build_forecast_from_monthly_net(monthly_net_values: list[Decimal]) -> dict:
    if not monthly_net_values:
        return {
            "trend": "Stable",
            "description": "Forecast is unavailable until enough historical entries exist.",
            "sparkline": [],
        }

    if len(monthly_net_values) < 4:
        trend = "Stable"
    else:
        midpoint = len(monthly_net_values) // 2
        older_half = monthly_net_values[:midpoint]
        newer_half = monthly_net_values[midpoint:]

        older_average = sum(older_half, Decimal("0.00")) / Decimal(len(older_half) or 1)
        newer_average = sum(newer_half, Decimal("0.00")) / Decimal(len(newer_half) or 1)

        baseline = abs(older_average) if older_average != 0 else Decimal("1.00")
        change_ratio = (newer_average - older_average) / baseline

        if change_ratio > Decimal("0.08"):
            trend = "Increasing"
        elif change_ratio < Decimal("-0.08"):
            trend = "Decreasing"
        else:
            trend = "Stable"

    description_by_trend = {
        "Increasing": "Recent movement suggests a positive upward pattern.",
        "Decreasing": "Recent movement suggests a weakening pattern that needs attention.",
        "Stable": "Recent movement suggests a stable financial pattern.",
    }

    min_net_value = min(monthly_net_values)
    if min_net_value < 0:
        sparkline_values = [value - min_net_value for value in monthly_net_values]
    else:
        sparkline_values = list(monthly_net_values)

    return {
        "trend": trend,
        "description": description_by_trend[trend],
        "sparkline": [_to_money_number(value) for value in sparkline_values],
    }


def _weighted_average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0.00")

    weights = [Decimal(index + 1) for index in range(len(values))]
    weight_total = sum(weights, Decimal("0.00"))
    if weight_total == 0:
        return Decimal("0.00")

    weighted_sum = sum(
        (value or Decimal("0.00")) * weight
        for value, weight in zip(values, weights)
    )

    return weighted_sum / weight_total





def _linear_regression_line(y_series: list[Decimal]) -> tuple[Decimal, Decimal, Decimal]:
    """
    Given a list of Decimal values representing a historical series,
    compute the linear regression slope (m) and intercept (c) for indices x = 1, 2, ..., n.
    Returns: (m, c, denominator)
    """
    n = len(y_series)
    if n == 0:
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
    if n == 1:
        return Decimal("0.00"), y_series[0], Decimal("1.00")

    sum_x = Decimal(str(sum(range(1, n + 1))))
    sum_y = sum(y_series, Decimal("0.00"))
    sum_xx = Decimal(str(sum(x * x for x in range(1, n + 1))))
    sum_xy = sum(Decimal(str(x)) * y for x, y in zip(range(1, n + 1), y_series))

    denominator = Decimal(str(n)) * sum_xx - sum_x * sum_x
    if denominator == 0:
        return Decimal("0.00"), y_series[-1], Decimal("0.00")

    m = (Decimal(str(n)) * sum_xy - sum_x * sum_y) / denominator
    c = (sum_y - m * sum_x) / Decimal(str(n))
    return m, c, denominator


def _frequency_interval_months(frequency: str) -> int:
    return FREQUENCY_INTERVALS.get(frequency, 1)


def _frequency_label(frequency: str) -> str:
    return FREQUENCY_LABELS.get(frequency, "Monthly")


def _format_period_label(year: int, month: int, frequency: str) -> str:
    month_label = MONTH_SHORT_NAMES.get(month, str(month))
    if frequency == FinancialRecord.FREQUENCY_QUARTERLY:
        quarter = ((month - 1) // 3) + 1
        return f"{month_label} {year} (Q{quarter})"
    if frequency == FinancialRecord.FREQUENCY_ANNUALLY:
        return f"{month_label} {year} (Annual)"
    return f"{month_label} {year}"


def _build_period_slots(
    reference_year: int,
    reference_month: int,
    frequency: str,
    count: int = 6,
) -> list[tuple[int, int, str]]:
    interval = _frequency_interval_months(frequency)
    slots: list[tuple[int, int, str]] = []
    starting_offset = -(count - 1) * interval

    for index in range(count):
        year, month = _shift_month(reference_year, reference_month, starting_offset + (index * interval))
        slots.append((year, month, _format_period_label(year, month, frequency)))

    return slots


def _build_monthly_projection_slots(
    reference_year: int,
    reference_month: int,
    count: int,
) -> list[tuple[int, int, str]]:
    slots: list[tuple[int, int, str]] = []
    horizon = max(int(count or 0), 1)

    for step in range(1, horizon + 1):
        year, month = _shift_month(reference_year, reference_month, step)
        slots.append((year, month, _format_period_label(year, month, FinancialRecord.FREQUENCY_MONTHLY)))

    return slots


def _period_key_for_line(line: FinancialRecordLine) -> tuple[int, int]:
    record = line.record
    if record.period_id:
        return record.period.year, record.period.month
    return record.entry_date.year, record.entry_date.month


def _month_distance(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> int:
    return ((end_year - start_year) * 12) + (end_month - start_month)


def _normalize_frequency(value: str) -> str:
    return value if value in FREQUENCY_INTERVALS else FinancialRecord.FREQUENCY_MONTHLY


def _build_group_forecast_model(
    *,
    client_id: int,
    category: str,
    frequency: str,
    group_key: str,
    period_totals: dict[tuple[int, int], Decimal],
) -> dict | None:
    period_keys = sorted(period_totals)
    if not period_keys:
        return None

    values = [period_totals[period_key] for period_key in period_keys]
    data_points = len(values)
    last_year, last_month = period_keys[-1]
    normalized_frequency = _normalize_frequency(frequency)
    slope, intercept, denominator = _linear_regression_line(values)

    model = {
        "client_id": client_id,
        "category": category,
        "group_key": group_key,
        "frequency": normalized_frequency,
        "interval": _frequency_interval_months(normalized_frequency),
        "last_year": last_year,
        "last_month": last_month,
        "data_points": data_points,
        "uses_limited_data": data_points < 2 or denominator == 0,
        "slope": slope,
        "intercept": intercept,
    }

    return model


def _project_group_value(
    model: dict,
    target_year: int,
    target_month: int,
) -> tuple[bool, Decimal | None, bool]:
    months_after_latest = _month_distance(
        model["last_year"],
        model["last_month"],
        target_year,
        target_month,
    )
    interval = model["interval"]

    if months_after_latest <= 0 or months_after_latest % interval != 0:
        return False, None, False

    step_count = months_after_latest // interval
    x_value = Decimal(str(model["data_points"] + step_count))
    value = (model["slope"] * x_value) + model["intercept"]
    if value < 0:
        return True, None, True

    return True, value, False


def _money_or_none(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return _to_money_number(value.quantize(Decimal("0.01")))


def _resolve_forecast_context(bookkeeper, scope_client: Client | None, reference_date) -> tuple[str, int, int, int]:
    """Returns (frequency, reference_year, reference_month, period_count).
    period_count spans from the earliest record to the latest so the
    regression line uses every available data point.
    """
    record_query = FinancialRecord.objects.filter(bookkeeper=bookkeeper)
    if scope_client is not None:
        record_query = record_query.filter(client=scope_client)

    latest_record = (
        record_query
        .select_related("period")
        .order_by("-entry_date", "-id")
        .first()
    )

    earliest_record = (
        record_query
        .select_related("period")
        .order_by("entry_date", "id")
        .first()
    )

    if scope_client is None:
        frequency = FinancialRecord.FREQUENCY_MONTHLY
    else:
        frequency = latest_record.frequency if latest_record else FinancialRecord.FREQUENCY_MONTHLY

    if latest_record and latest_record.period_id:
        reference_year = latest_record.period.year
        reference_month = latest_record.period.month
    elif latest_record:
        reference_year = latest_record.entry_date.year
        reference_month = latest_record.entry_date.month
    else:
        reference_year = reference_date.year
        reference_month = reference_date.month

    # Calculate how many periods span from earliest to latest
    if earliest_record and latest_record:
        if earliest_record.period_id:
            early_y, early_m = earliest_record.period.year, earliest_record.period.month
        else:
            early_y, early_m = earliest_record.entry_date.year, earliest_record.entry_date.month
        interval = _frequency_interval_months(frequency)
        total_months = (reference_year - early_y) * 12 + (reference_month - early_m)
        period_count = max((total_months // interval) + 1, 6)
    else:
        period_count = 6

    return frequency, reference_year, reference_month, period_count


def _build_predictive_forecast(
    *,
    lines: list[FinancialRecordLine],
    forecast_horizon: int = 3,
    reference_date: date | None = None,
) -> dict:
    safe_horizon = max(int(forecast_horizon or 3), 1)
    fallback_reference_date = reference_date or timezone.localdate()

    grouped_totals: dict[tuple[int, str, str, str], dict[tuple[int, int], Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal("0.00"))
    )
    actual_totals_by_period: dict[tuple[int, int], dict[str, Decimal]] = defaultdict(_empty_bucket)
    latest_period_key: tuple[int, int] | None = None

    for line in lines:
        record = line.record
        if not record:
            continue

        period_key = _period_key_for_line(line)
        if latest_period_key is None or period_key > latest_period_key:
            latest_period_key = period_key
        amount = line.amount or Decimal("0.00")
        category = _classify_line_item(line.type_code, line.description)
        frequency = _resolve_line_forecast_frequency(line, category)
        group_key = _forecast_group_key(line, category)

        grouped_totals[(record.client_id, category, frequency, group_key)][period_key] += amount
        actual_totals_by_period[period_key][category] += amount

    if latest_period_key is None:
        reference_year = fallback_reference_date.year
        reference_month = fallback_reference_date.month
        next_year, next_month = _shift_month(reference_year, reference_month, 1)
        return {
            "has_forecast": False,
            "frequency": FinancialRecord.FREQUENCY_MONTHLY,
            "frequency_label": _frequency_label(FinancialRecord.FREQUENCY_MONTHLY),
            "period_count": 0,
            "data_points": 0,
            "next_period_label": _format_period_label(next_year, next_month, FinancialRecord.FREQUENCY_MONTHLY),
            "message": "Forecast is unavailable until enough historical entries exist.",
            "sparkline": [],
        }

    reference_year, reference_month = latest_period_key
    projection_slots = _build_monthly_projection_slots(reference_year, reference_month, safe_horizon)

    models_by_category: dict[str, list[dict]] = {category: [] for category in FORECAST_CATEGORIES}
    frequencies = set()
    limited_data_used = False

    for (client_id, category, frequency, group_key), period_totals in grouped_totals.items():
        model = _build_group_forecast_model(
            client_id=client_id,
            category=category,
            frequency=frequency,
            group_key=group_key,
            period_totals=period_totals,
        )
        if model is None:
            continue

        models_by_category[category].append(model)
        frequencies.add(frequency)
        limited_data_used = limited_data_used or model["uses_limited_data"]

    future_projections: list[dict] = []
    for target_year, target_month, target_label in projection_slots:
        category_totals: dict[str, Decimal] = {}
        category_applicability: dict[str, bool] = {}
        category_has_values: dict[str, bool] = {}
        category_limited_data: dict[str, bool] = {}
        category_unreliable: dict[str, bool] = {}

        for category in FORECAST_CATEGORIES:
            projected_total = Decimal("0.00")
            is_applicable = False
            has_value = False
            uses_limited_data = False
            has_unreliable_projection = False

            for model in models_by_category[category]:
                is_scheduled, projected_value, is_unreliable = _project_group_value(
                    model,
                    target_year,
                    target_month,
                )
                if not is_scheduled:
                    continue

                is_applicable = True
                uses_limited_data = uses_limited_data or model["uses_limited_data"]
                has_unreliable_projection = has_unreliable_projection or is_unreliable
                if projected_value is None:
                    continue

                has_value = True
                projected_total += projected_value

            category_totals[category] = projected_total
            category_applicability[category] = is_applicable
            category_has_values[category] = has_value
            category_limited_data[category] = uses_limited_data
            category_unreliable[category] = has_unreliable_projection

        net_has_value = category_has_values["sales"]
        net_unreliable = False
        projected_net = category_totals["sales"] - category_totals["expenses"]

        future_projections.append({
            "period_label": target_label,
            "expected_sales": _money_or_none(category_totals["sales"] if category_has_values["sales"] else None),
            "expected_expenses": _money_or_none(category_totals["expenses"] if category_has_values["expenses"] else None),
            "expected_tax": _money_or_none(category_totals["tax"] if category_has_values["tax"] else None),
            "expected_sales_applicable": category_applicability["sales"],
            "expected_expenses_applicable": category_applicability["expenses"],
            "expected_tax_applicable": category_applicability["tax"],
            "sales_method": "Linear Regression" if category_applicability["sales"] else "Not scheduled",
            "expenses_method": "Linear Regression" if category_applicability["expenses"] else "Not scheduled",
            "tax_method": "Linear Regression" if category_applicability["tax"] else "Not scheduled",
            "sales_limited_data": category_limited_data["sales"],
            "expenses_limited_data": category_limited_data["expenses"],
            "tax_limited_data": category_limited_data["tax"],
            "sales_unreliable": category_unreliable["sales"],
            "expenses_unreliable": category_unreliable["expenses"],
            "tax_unreliable": category_unreliable["tax"],
            "expected_net_applicable": net_has_value,
            "expected_net_unreliable": net_unreliable,
            "expected_net": _money_or_none(projected_net if net_has_value else None),
        })

    first_projection = future_projections[0] if future_projections else {}
    frequency_value = next(iter(frequencies)) if len(frequencies) == 1 else FORECAST_MIXED_FREQUENCY
    frequency_label = _frequency_label(frequency_value) if len(frequencies) == 1 else "Mixed Schedule"
    data_points = max(
        (model["data_points"] for category_models in models_by_category.values() for model in category_models),
        default=0,
    )
    basis = (
        "Forecast calculated using separate transaction-aware and frequency-aware Linear Regression models for each client, category, and frequency."
    )
    if limited_data_used:
        basis = f"{basis} {FORECAST_LIMITED_DATA_MESSAGE}"

    sparkline_values = []
    for period_key in sorted(actual_totals_by_period)[-6:]:
        totals = actual_totals_by_period[period_key]
        sparkline_values.append(totals["sales"] - totals["expenses"])
    sparkline_values.extend(
        Decimal(str(row.get("expected_net") or 0))
        for row in future_projections
    )

    return {
        "has_forecast": True,
        "frequency": frequency_value,
        "frequency_label": frequency_label,
        "period_count": data_points,
        "data_points": data_points,
        "next_period_label": first_projection.get("period_label", ""),
        "expected_sales": first_projection.get("expected_sales"),
        "expected_expenses": first_projection.get("expected_expenses"),
        "expected_tax": first_projection.get("expected_tax"),
        "expected_sales_applicable": first_projection.get("expected_sales_applicable", False),
        "expected_expenses_applicable": first_projection.get("expected_expenses_applicable", False),
        "expected_tax_applicable": first_projection.get("expected_tax_applicable", False),
        "sales_method": first_projection.get("sales_method", "Not scheduled"),
        "expenses_method": first_projection.get("expenses_method", "Not scheduled"),
        "tax_method": first_projection.get("tax_method", "Not scheduled"),
        "sales_limited_data": first_projection.get("sales_limited_data", False),
        "expenses_limited_data": first_projection.get("expenses_limited_data", False),
        "tax_limited_data": first_projection.get("tax_limited_data", False),
        "sales_unreliable": first_projection.get("sales_unreliable", False),
        "expenses_unreliable": first_projection.get("expenses_unreliable", False),
        "tax_unreliable": first_projection.get("tax_unreliable", False),
        "expected_net_applicable": first_projection.get("expected_net_applicable", False),
        "expected_net_unreliable": first_projection.get("expected_net_unreliable", False),
        "expected_net": first_projection.get("expected_net"),
        "basis": basis,
        "future_projections": future_projections,
        "sparkline": [_to_money_number(value) for value in sparkline_values],
    }


def get_analytics_summary_for_bookkeeper(
    bookkeeper,
    client_id: int | None = None,
    year_filter: str | None = None,
    horizon: int = 3,
) -> dict:
    all_clients = list(
        Client.objects.filter(bookkeeper=bookkeeper)
        .order_by("client_name", "id")
    )

    available_clients = [
        {
            "id": client.id,
            "client_name": client.client_name,
            "tin_number": client.tin_number,
            "trade_name": client.trade_name,
        }
        for client in all_clients
    ]

    scope_client = None
    if client_id is not None:
        scope_client = next((client for client in all_clients if client.id == client_id), None)
        if scope_client is None:
            return {
                "ok": False,
                "message": "Client not found.",
                "errors": ["Client not found."],
            }

    today = timezone.localdate()
    month_slots = _recent_month_slots(today, count=6)
    slot_keys = [(year, month) for year, month, _ in month_slots]

    month_filter = Q()
    for year, month, _ in month_slots:
        month_filter |= Q(record__period__year=year, record__period__month=month)

    base_lines_query = FinancialRecordLine.objects.filter(
        record__bookkeeper=bookkeeper,
    )
    if scope_client is not None:
        base_lines_query = base_lines_query.filter(record__client=scope_client)
        
    if year_filter and year_filter.isdigit():
        base_lines_query = base_lines_query.filter(record__period__year=int(year_filter))

    all_lines = list(
        base_lines_query
        .select_related("record", "record__client", "record__period")
    )

    recent_lines = list(
        base_lines_query
        .filter(month_filter)
        .select_related("record", "record__client", "record__period")
    )

    monthly_totals = {key: _empty_bucket() for key in slot_keys}
    monthly_type_totals = {key: defaultdict(lambda: Decimal("0.00")) for key in slot_keys}
    monthly_net_totals = {key: Decimal("0.00") for key in slot_keys}
    grand_totals = _empty_bucket()
    total_net_value = Decimal("0.00")
    client_sales_totals: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    type_label_map: dict[str, str] = {}
    type_category_map: dict[str, str] = {}

    for line in all_lines:
        amount = line.amount or Decimal("0.00")
        category = _classify_line_item(line.type_code, line.description)
        grand_totals[category] += amount

        if category == "sales":
            client_sales_totals[line.record.client_id] += amount

    for line in recent_lines:
        amount = line.amount or Decimal("0.00")
        category = _classify_line_item(line.type_code, line.description)
        month_key = (line.record.period.year, line.record.period.month)

        if month_key in monthly_totals:
            monthly_totals[month_key][category] += amount

            type_label = _normalize_type_code_label(line.type_code)
            if type_label:
                type_key = _normalize_type_code_key(line.type_code)
                monthly_type_totals[month_key][type_key] += amount
                if type_key not in type_label_map:
                    type_label_map[type_key] = type_label
                if type_key not in type_category_map:
                    type_category_map[type_key] = category



    for month_key, totals in monthly_totals.items():
        monthly_net_totals[month_key] = totals["sales"] - totals["expenses"]

    total_net_value = grand_totals["sales"] - grand_totals["expenses"]

    category_priority = {
        "sales": 1,
        "expenses": 2,
        "tax": 3,
    }
    type_pairs = sorted(
        type_label_map.items(),
        key=lambda item: (
            category_priority.get(type_category_map.get(item[0], "sales"), 1),
            item[1].lower()
        )
    )
    type_columns = [label for _, label in type_pairs]

    monthly_trend = []
    monthly_net_values: list[Decimal] = []
    for year, month, month_label in month_slots:
        totals = monthly_totals[(year, month)]
        net_value = monthly_net_totals[(year, month)]
        monthly_net_values.append(net_value)

        type_breakdown = {
            label: _to_money_number(monthly_type_totals[(year, month)].get(type_key, Decimal("0.00")))
            for type_key, label in type_pairs
        }

        monthly_trend.append(
            {
                "year": year,
                "month": month,
                "month_label": month_label,
                "sales": _to_money_number(totals["sales"]),
                "expenses": _to_money_number(totals["expenses"]),
                "tax": _to_money_number(totals["tax"]),
                "net_value": _to_money_number(net_value),
                "type_breakdown": type_breakdown,
            }
        )

    summary = {
        "total_sales": _to_money_number(grand_totals["sales"]),
        "total_expenses": _to_money_number(grand_totals["expenses"]),
        "total_tax": _to_money_number(grand_totals["tax"]),
        "net_value": _to_money_number(total_net_value),
    }

    comparison = []
    if scope_client is None:
        for client in all_clients:
            total_sales = client_sales_totals.get(client.id, Decimal("0.00"))
            if total_sales <= 0:
                continue

            level = client.remarks if client.remarks in REMARK_TO_LABEL else Client.REMARK_NEW
            comparison.append(
                {
                    "client_id": client.id,
                    "client_name": client.client_name,
                    "total_sales": _to_money_number(total_sales),
                    "remarks": level,
                    "remarks_label": REMARK_TO_LABEL[level],
                }
            )

        comparison.sort(key=lambda item: item["total_sales"], reverse=True)

    has_data = any(value > 0 for value in summary.values())

    remarks_insight = _build_remarks_insight(scope_client, all_clients)
    forecast = _build_forecast_from_monthly_net(monthly_net_values if has_data else [])
    predictive_forecast = _build_predictive_forecast(
        lines=all_lines,
        forecast_horizon=horizon,
        reference_date=today,
    )

    return {
        "ok": True,
        "scope": {
            "is_all": scope_client is None,
            "client_id": scope_client.id if scope_client is not None else None,
            "client_name": scope_client.client_name if scope_client is not None else "All Clients",
            "client_tin": scope_client.tin_number if scope_client is not None else "",
            "client_trade_name": scope_client.trade_name if scope_client is not None else "",
        },
        "available_clients": available_clients,
        "type_columns": type_columns,
        "has_data": has_data,
        "summary": summary,
        "monthly_trend": monthly_trend,
        "remarks_insight": remarks_insight,
        "forecast": forecast,
        "predictive_forecast": predictive_forecast,
        "comparison": comparison,
    }
