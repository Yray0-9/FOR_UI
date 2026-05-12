from collections import defaultdict
from datetime import date
from decimal import Decimal
import re

from django.db.models import Q
from django.utils import timezone

from safebooks.models import Client, FinancialRecordLine


TAX_TYPE_CODES = {
    "1701",
    "1701a",
    "1702",
    "2550m",
    "2550q",
    "0619e",
    "0619f",
    "1601c",
    "1601eq",
    "1701q",
    "2370",
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

NET_VALUE_OPERATIONS = {
    FinancialRecordLine.CALC_ADD,
    FinancialRecordLine.CALC_SUBTRACT,
    FinancialRecordLine.CALC_MULTIPLY,
    FinancialRecordLine.CALC_DIVIDE,
}


def _contains_keyword(normalized_text: str, normalized_keyword: str) -> bool:
    if not normalized_keyword:
        return False
    return f" {normalized_keyword} " in f" {normalized_text} "

RISK_LEVEL_TO_LABEL = {
    Client.RISK_LOW: "Low",
    Client.RISK_MEDIUM: "Medium",
    Client.RISK_HIGH: "High",
}

RISK_LEVEL_TO_TITLE = {
    Client.RISK_LOW: "Low Risk",
    Client.RISK_MEDIUM: "Medium Risk",
    Client.RISK_HIGH: "High Risk",
}

RISK_LEVEL_TO_DESCRIPTION = {
    Client.RISK_LOW: "This client has consistent entries and complete submissions.",
    Client.RISK_MEDIUM: "This client has occasional missing entries and needs regular follow-up.",
    Client.RISK_HIGH: "This client has missing or inconsistent entries and needs immediate attention.",
}

ALL_CLIENTS_RISK_DESCRIPTIONS = {
    Client.RISK_LOW: "Most clients have consistent entries and complete submissions.",
    Client.RISK_MEDIUM: "Some clients still have delayed or incomplete entries that need follow-up.",
    Client.RISK_HIGH: "Multiple clients have missing or inconsistent entries requiring immediate review.",
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


def _to_money_number(value: Decimal) -> float:
    return float((value or Decimal("0.00")).quantize(Decimal("0.01")))


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


def _resolve_all_clients_risk_level(clients: list[Client]) -> str:
    risk_counts = {
        Client.RISK_LOW: 0,
        Client.RISK_MEDIUM: 0,
        Client.RISK_HIGH: 0,
    }

    for client in clients:
        level = client.risk_level if client.risk_level in risk_counts else Client.RISK_MEDIUM
        risk_counts[level] += 1

    if risk_counts[Client.RISK_HIGH] > 0:
        return Client.RISK_HIGH
    if risk_counts[Client.RISK_MEDIUM] > 0:
        return Client.RISK_MEDIUM
    return Client.RISK_LOW


def _build_risk_insight(scope_client: Client | None, all_clients: list[Client]) -> dict:
    if scope_client is not None:
        level = scope_client.risk_level if scope_client.risk_level in RISK_LEVEL_TO_TITLE else Client.RISK_MEDIUM
        return {
            "level": level,
            "title": RISK_LEVEL_TO_TITLE[level],
            "description": RISK_LEVEL_TO_DESCRIPTION[level],
        }

    level = _resolve_all_clients_risk_level(all_clients)
    return {
        "level": level,
        "title": RISK_LEVEL_TO_TITLE[level],
        "description": ALL_CLIENTS_RISK_DESCRIPTIONS[level],
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


def get_analytics_summary_for_bookkeeper(bookkeeper, client_id: int | None = None) -> dict:
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

    for line in all_lines:
        amount = line.amount or Decimal("0.00")
        category = _classify_line_item(line.type_code, line.description)
        grand_totals[category] += amount

        if line.calc_applied and line.calc_operation in NET_VALUE_OPERATIONS:
            total_net_value += line.calc_result or Decimal("0.00")

        if category == "sales":
            client_sales_totals[line.record.client_id] += amount

    for line in recent_lines:
        amount = line.amount or Decimal("0.00")
        category = _classify_line_item(line.type_code, line.description)
        month_key = (line.record.period.year, line.record.period.month)

        if month_key in monthly_totals:
            monthly_totals[month_key][category] += amount

            if line.calc_applied and line.calc_operation in NET_VALUE_OPERATIONS:
                monthly_net_totals[month_key] += line.calc_result or Decimal("0.00")

            type_label = _normalize_type_code_label(line.type_code)
            if type_label:
                type_key = _normalize_type_code_key(line.type_code)
                monthly_type_totals[month_key][type_key] += amount
                if type_key not in type_label_map:
                    type_label_map[type_key] = type_label

    type_pairs = sorted(type_label_map.items(), key=lambda item: item[1].lower())
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

            level = client.risk_level if client.risk_level in RISK_LEVEL_TO_LABEL else Client.RISK_MEDIUM
            comparison.append(
                {
                    "client_id": client.id,
                    "client_name": client.client_name,
                    "total_sales": _to_money_number(total_sales),
                    "risk_level": level,
                    "risk_level_label": RISK_LEVEL_TO_LABEL[level],
                }
            )

        comparison.sort(key=lambda item: item["total_sales"], reverse=True)

    has_data = any(value > 0 for value in summary.values())

    risk_insight = _build_risk_insight(scope_client, all_clients)
    forecast = _build_forecast_from_monthly_net(monthly_net_values if has_data else [])

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
        "risk_insight": risk_insight,
        "forecast": forecast,
        "comparison": comparison,
    }