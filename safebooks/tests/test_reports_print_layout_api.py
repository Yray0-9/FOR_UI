from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from safebooks.models import BookkeeperAccount, Client, FinancialRecord, FinancialRecordLine, Period
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class ReportsPrintLayoutApiTests(TestCase):
    def _create_bookkeeper(self, suffix: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Reports Print {suffix}",
            username=f"reports_print_{suffix}",
            email=f"reports_print_{suffix}@example.com",
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

    def _create_client(self, *, bookkeeper: BookkeeperAccount, suffix: str) -> Client:
        return Client.objects.create(
            bookkeeper=bookkeeper,
            client_name=f"Client {suffix}",
            tin_number=self._build_tin(f"pr-{suffix}"),
            trade_name=f"Trade {suffix}",
            location="Davao City",
            permit_number=f"PERMIT-PR-{suffix}",
            email=f"client-print-{suffix}@example.com",
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
            notes="Print layout test",
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

    def test_reports_print_layout_requires_authentication(self):
        response = self.client.get(
            reverse("api_reports_print_layout"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Authentication required.")

    def test_reports_print_layout_returns_transactions_for_date_range(self):
        owner = self._create_bookkeeper("owner")
        self._login_as(owner)

        client = self._create_client(bookkeeper=owner, suffix="A")

        self._create_record_with_lines(
            bookkeeper=owner,
            client=client,
            entry_date=date(2026, 1, 15),
            lines=[
                ("Sales", "January sale", Decimal("100.00")),
                ("Expenses", "January expense", Decimal("50.00")),
            ],
        )
        self._create_record_with_lines(
            bookkeeper=owner,
            client=client,
            entry_date=date(2026, 2, 10),
            lines=[
                ("Sales", "February sale", Decimal("75.00")),
            ],
        )

        response = self.client.get(
            reverse("api_reports_print_layout"),
            {
                "client_id": client.id,
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
            },
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok"))

        summary = payload.get("summary", {})
        self.assertEqual(summary.get("entry_count"), 1)
        self.assertEqual(summary.get("line_item_count"), 2)
        self.assertEqual(summary.get("total_amount"), "150.00")

        rows = payload.get("rows", [])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["entry_date"], "2026-01-15")
        self.assertEqual(rows[0]["type_code"], "Sales")
        self.assertEqual(rows[0]["amount"], "100.00")
        self.assertEqual(rows[1]["type_code"], "Expenses")
        self.assertEqual(rows[1]["amount"], "50.00")
