from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from safebooks.models import BookkeeperAccount, Client, FinancialRecord, FinancialRecordLine, Period
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class AnalyticsSummaryApiTests(TestCase):
    def _create_bookkeeper(self, suffix: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Bookkeeper {suffix}",
            username=f"analytics_{suffix}",
            email=f"analytics_{suffix}@example.com",
            password_hash="not-used-in-test",
        )

    def _login_as(self, account: BookkeeperAccount) -> None:
        session = self.client.session
        session[SESSION_BOOKKEEPER_ID_KEY] = account.id
        session.save()

    def _build_tin(self, token: str) -> str:
        digits = "".join(char for char in str(token or "") if char.isdigit())
        if digits:
            seed = int(digits)
        else:
            seed = sum(ord(char) for char in str(token or ""))
        return f"{seed:012d}"

    def _create_client(self, *, bookkeeper: BookkeeperAccount, suffix: str, risk: str) -> Client:
        return Client.objects.create(
            bookkeeper=bookkeeper,
            client_name=f"Client {suffix}",
            tin_number=self._build_tin(f"an-{suffix}"),
            trade_name=f"Trade {suffix}",
            location="Panabo",
            permit_number=f"PERMIT-AN-{suffix}",
            email=f"client-analytics-{suffix}@example.com",
            risk_level=risk,
        )

    def _create_record_with_lines(
        self,
        *,
        bookkeeper: BookkeeperAccount,
        client: Client,
        entry_date: date,
        lines: list[tuple[str, str, Decimal]],
    ) -> FinancialRecord:
        period, _ = Period.objects.get_or_create(
            client=client,
            year=entry_date.year,
            month=entry_date.month,
        )

        record = FinancialRecord.objects.create(
            bookkeeper=bookkeeper,
            client=client,
            period=period,
            entry_date=entry_date,
            notes="Analytics test",
            total_amount=sum((amount for _, _, amount in lines), Decimal("0.00")),
        )

        for index, (type_code, description, amount) in enumerate(lines, start=1):
            FinancialRecordLine.objects.create(
                record=record,
                type_code=type_code,
                description=description,
                amount=amount,
                sort_order=index,
            )

        return record

    def test_analytics_summary_requires_authentication(self):
        response = self.client.get(
            reverse("api_analytics_summary"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Authentication required.")

    def test_analytics_summary_all_clients_returns_expected_values(self):
        today = timezone.localdate()
        previous_year = today.year if today.month > 1 else today.year - 1
        previous_month = today.month - 1 if today.month > 1 else 12

        owner = self._create_bookkeeper("owner-all")
        self._login_as(owner)

        client_a = self._create_client(bookkeeper=owner, suffix="A", risk=Client.RISK_LOW)
        client_b = self._create_client(bookkeeper=owner, suffix="B", risk=Client.RISK_HIGH)

        self._create_record_with_lines(
            bookkeeper=owner,
            client=client_a,
            entry_date=today,
            lines=[
                ("Sales", "Sales collection", Decimal("1000.00")),
                ("Expenses", "Office expense", Decimal("300.00")),
                ("1701", "Income tax", Decimal("100.00")),
            ],
        )
        self._create_record_with_lines(
            bookkeeper=owner,
            client=client_b,
            entry_date=date(previous_year, previous_month, 1),
            lines=[
                ("Sales", "Service income", Decimal("500.00")),
                ("Expenses", "Transport expense", Decimal("200.00")),
                ("2550M", "VAT", Decimal("50.00")),
            ],
        )

        response = self.client.get(reverse("api_analytics_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload.get("ok"))
        self.assertTrue(payload.get("scope", {}).get("is_all"))
        self.assertEqual(payload.get("scope", {}).get("client_id"), None)

        self.assertEqual(payload["summary"]["total_sales"], 1500.0)
        self.assertEqual(payload["summary"]["total_expenses"], 500.0)
        self.assertEqual(payload["summary"]["total_tax"], 150.0)
        self.assertEqual(payload["summary"]["net_value"], 0.0)

        self.assertEqual(payload["risk_insight"]["level"], Client.RISK_HIGH)
        self.assertTrue(payload["has_data"])
        self.assertEqual(len(payload.get("monthly_trend", [])), 6)

        comparison = payload.get("comparison", [])
        self.assertEqual(len(comparison), 2)
        self.assertEqual(comparison[0]["client_id"], client_a.id)
        self.assertEqual(comparison[0]["risk_level_label"], "Low")
        self.assertEqual(comparison[0]["total_sales"], 1000.0)

        available_clients = payload.get("available_clients", [])
        available_client_ids = {row["id"] for row in available_clients}
        self.assertEqual(available_client_ids, {client_a.id, client_b.id})
        available_client_tins = {row["tin_number"] for row in available_clients}
        self.assertEqual(available_client_tins, {client_a.tin_number, client_b.tin_number})
        available_client_trades = {row["trade_name"] for row in available_clients}
        self.assertEqual(available_client_trades, {client_a.trade_name, client_b.trade_name})

    def test_analytics_summary_client_scope_and_ownership_isolation(self):
        today = timezone.localdate()

        owner = self._create_bookkeeper("owner-scope")
        other = self._create_bookkeeper("other-scope")

        owner_client = self._create_client(bookkeeper=owner, suffix="owner", risk=Client.RISK_MEDIUM)
        other_client = self._create_client(bookkeeper=other, suffix="other", risk=Client.RISK_HIGH)

        self._create_record_with_lines(
            bookkeeper=owner,
            client=owner_client,
            entry_date=today,
            lines=[
                ("Sales", "Sales income", Decimal("700.00")),
                ("Expenses", "Operations expense", Decimal("250.00")),
                ("1701", "Tax", Decimal("70.00")),
            ],
        )
        self._create_record_with_lines(
            bookkeeper=other,
            client=other_client,
            entry_date=today,
            lines=[
                ("Sales", "Other sales", Decimal("900.00")),
                ("Expenses", "Other expense", Decimal("200.00")),
                ("1701", "Other tax", Decimal("90.00")),
            ],
        )

        self._login_as(owner)

        response = self.client.get(
            reverse("api_analytics_summary"),
            {"client_id": owner_client.id},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertFalse(payload["scope"]["is_all"])
        self.assertEqual(payload["scope"]["client_id"], owner_client.id)
        self.assertEqual(payload["scope"]["client_tin"], owner_client.tin_number)
        self.assertEqual(payload["scope"]["client_trade_name"], owner_client.trade_name)
        self.assertEqual(payload["summary"]["total_sales"], 700.0)
        self.assertEqual(payload["summary"]["total_expenses"], 250.0)
        self.assertEqual(payload["summary"]["total_tax"], 70.0)
        self.assertEqual(payload["summary"]["net_value"], 0.0)

        forbidden_response = self.client.get(
            reverse("api_analytics_summary"),
            {"client_id": other_client.id},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(forbidden_response.status_code, 404)
        forbidden_payload = forbidden_response.json()
        self.assertFalse(forbidden_payload.get("ok"))
        self.assertEqual(forbidden_payload.get("message"), "Client not found.")

    def test_analytics_summary_client_with_no_records_returns_empty_payload(self):
        owner = self._create_bookkeeper("owner-empty")
        empty_client = self._create_client(bookkeeper=owner, suffix="empty", risk=Client.RISK_HIGH)

        self._login_as(owner)
        response = self.client.get(
            reverse("api_analytics_summary"),
            {"client_id": empty_client.id},
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertFalse(payload["scope"]["is_all"])
        self.assertEqual(payload["scope"]["client_id"], empty_client.id)
        self.assertEqual(payload["scope"]["client_tin"], empty_client.tin_number)
        self.assertEqual(payload["scope"]["client_trade_name"], empty_client.trade_name)
        self.assertFalse(payload["has_data"])
        self.assertEqual(payload["summary"]["total_sales"], 0.0)
        self.assertEqual(payload["summary"]["total_expenses"], 0.0)
        self.assertEqual(payload["summary"]["total_tax"], 0.0)
        self.assertEqual(payload["summary"]["net_value"], 0.0)
        self.assertEqual(payload["comparison"], [])
        self.assertEqual(payload["forecast"]["sparkline"], [])
        self.assertEqual(len(payload.get("monthly_trend", [])), 6)

    def test_analytics_summary_includes_historical_totals_and_numeric_tax_codes(self):
        today = timezone.localdate()
        history_year = today.year if today.month > 8 else today.year - 1
        history_month = today.month - 8 if today.month > 8 else today.month + 4

        owner = self._create_bookkeeper("owner-history")
        self._login_as(owner)

        client = self._create_client(bookkeeper=owner, suffix="history", risk=Client.RISK_MEDIUM)

        # Older record should still contribute to totals, even if it is outside the 6-month trend window.
        self._create_record_with_lines(
            bookkeeper=owner,
            client=client,
            entry_date=date(history_year, history_month, 1),
            lines=[
                ("Sales", "Legacy sale", Decimal("100.00")),
                ("1701Q", "Quarterly return", Decimal("40.00")),
            ],
        )
        self._create_record_with_lines(
            bookkeeper=owner,
            client=client,
            entry_date=today,
            lines=[
                ("Sales", "Current sale", Decimal("60.00")),
                ("Expenses", "Current expense", Decimal("10.00")),
            ],
        )

        response = self.client.get(reverse("api_analytics_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["summary"]["total_sales"], 160.0)
        self.assertEqual(payload["summary"]["total_tax"], 40.0)
        self.assertEqual(payload["summary"]["net_value"], 0.0)

        monthly_trend = payload.get("monthly_trend", [])
        trend_sales_sum = sum(float(row.get("sales", 0.0)) for row in monthly_trend)
        trend_tax_sum = sum(float(row.get("tax", 0.0)) for row in monthly_trend)
        self.assertEqual(trend_sales_sum, 60.0)
        self.assertEqual(trend_tax_sum, 0.0)

    def test_analytics_summary_exposes_tin_for_disambiguation_and_scope(self):
        today = timezone.localdate()

        owner = self._create_bookkeeper("owner-tin")
        self._login_as(owner)

        same_tin_a = self._build_tin("same-001")
        same_tin_b = self._build_tin("same-002")

        client_a = Client.objects.create(
            bookkeeper=owner,
            client_name="Same Name Client",
            tin_number=same_tin_a,
            trade_name="Trade A",
            location="Panabo",
            permit_number="PERMIT-SAME-001",
            email="same-a@example.com",
            risk_level=Client.RISK_LOW,
        )
        client_b = Client.objects.create(
            bookkeeper=owner,
            client_name="Same Name Client",
            tin_number=same_tin_b,
            trade_name="Trade B",
            location="Panabo",
            permit_number="PERMIT-SAME-002",
            email="same-b@example.com",
            risk_level=Client.RISK_MEDIUM,
        )

        self._create_record_with_lines(
            bookkeeper=owner,
            client=client_a,
            entry_date=today,
            lines=[("Sales", "Client A sale", Decimal("150.00"))],
        )
        self._create_record_with_lines(
            bookkeeper=owner,
            client=client_b,
            entry_date=today,
            lines=[("Sales", "Client B sale", Decimal("250.00"))],
        )

        all_clients_response = self.client.get(reverse("api_analytics_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(all_clients_response.status_code, 200)
        all_clients_payload = all_clients_response.json()

        available_clients = all_clients_payload.get("available_clients", [])
        same_name_rows = [
            row
            for row in available_clients
            if row.get("client_name") == "Same Name Client"
        ]
        self.assertEqual(len(same_name_rows), 2)
        self.assertEqual(
            {row.get("tin_number") for row in same_name_rows},
            {same_tin_a, same_tin_b},
        )

        scoped_response = self.client.get(
            reverse("api_analytics_summary"),
            {"client_id": client_b.id},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(scoped_response.status_code, 200)
        scoped_payload = scoped_response.json()

        self.assertEqual(scoped_payload["scope"]["client_id"], client_b.id)
        self.assertEqual(scoped_payload["scope"]["client_tin"], same_tin_b)
