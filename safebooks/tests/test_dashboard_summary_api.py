from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from safebooks.models import BookkeeperAccount, Client, FinancialRecord, FinancialRecordLine, Period
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class DashboardSummaryApiTests(TestCase):
    def _create_bookkeeper(self, suffix: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Bookkeeper {suffix}",
            username=f"bookkeeper_{suffix}",
            email=f"bookkeeper_{suffix}@example.com",
            password_hash="not-used-in-test",
        )

    def _login_as(self, account: BookkeeperAccount) -> None:
        session = self.client.session
        session[SESSION_BOOKKEEPER_ID_KEY] = account.id
        session.save()

    def _create_client(self, *, bookkeeper: BookkeeperAccount, tin_suffix: str, risk: str) -> Client:
        return Client.objects.create(
            bookkeeper=bookkeeper,
            client_name=f"Client {tin_suffix}",
            tin_number=f"TIN-{tin_suffix}",
            trade_name=f"Trade {tin_suffix}",
            location="Panabo City",
            permit_number=f"PERMIT-{tin_suffix}",
            email=f"client-{tin_suffix}@example.com",
            risk_level=risk,
        )

    def _create_record(
        self,
        *,
        bookkeeper: BookkeeperAccount,
        client: Client,
        entry_date: date,
        amount: Decimal,
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
            notes="Test note",
            total_amount=amount,
        )
        FinancialRecordLine.objects.create(
            record=record,
            type_code="1701",
            description="Income Tax",
            amount=amount,
            sort_order=1,
        )
        return record

    def test_dashboard_summary_requires_authentication(self):
        response = self.client.get(
            reverse("api_dashboard_summary"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Authentication required.")

    def test_dashboard_summary_returns_expected_metrics_and_summaries(self):
        today = timezone.localdate()
        previous_year = today.year if today.month > 1 else today.year - 1
        previous_month = today.month - 1 if today.month > 1 else 12

        owner = self._create_bookkeeper("owner-metrics")
        self._login_as(owner)

        client_updated = self._create_client(
            bookkeeper=owner,
            tin_suffix="updated",
            risk=Client.RISK_LOW,
        )
        client_pending = self._create_client(
            bookkeeper=owner,
            tin_suffix="pending",
            risk=Client.RISK_MEDIUM,
        )
        client_late = self._create_client(
            bookkeeper=owner,
            tin_suffix="late",
            risk=Client.RISK_HIGH,
        )

        self._create_record(
            bookkeeper=owner,
            client=client_updated,
            entry_date=today,
            amount=Decimal("1200.00"),
        )
        self._create_record(
            bookkeeper=owner,
            client=client_pending,
            entry_date=date(previous_year, previous_month, 1),
            amount=Decimal("800.00"),
        )

        response = self.client.get(reverse("api_dashboard_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertTrue(payload.get("ok"))

        self.assertEqual(payload["metrics"]["total_clients"], 3)
        self.assertEqual(payload["metrics"]["total_entries_this_month"], 1)
        self.assertEqual(payload["metrics"]["pending_compliance"], 2)
        self.assertEqual(payload["metrics"]["high_risk_clients"], 1)

        self.assertEqual(payload["risk_summary"]["low"], 1)
        self.assertEqual(payload["risk_summary"]["medium"], 1)
        self.assertEqual(payload["risk_summary"]["high"], 1)

        self.assertEqual(payload["compliance_summary"]["filed"]["count"], 1)
        self.assertEqual(payload["compliance_summary"]["pending"]["count"], 1)
        self.assertEqual(payload["compliance_summary"]["late"]["count"], 1)
        self.assertEqual(payload["compliance_summary"]["filed"]["percentage"], 33)
        self.assertEqual(payload["compliance_summary"]["pending"]["percentage"], 33)
        self.assertEqual(payload["compliance_summary"]["late"]["percentage"], 33)

        activity_by_client_id = {
            row["client_id"]: row
            for row in payload.get("recent_client_activity", [])
        }
        self.assertEqual(activity_by_client_id[client_updated.id]["status"], "updated")
        self.assertEqual(activity_by_client_id[client_updated.id]["compliance"], "filed")
        self.assertEqual(activity_by_client_id[client_pending.id]["status"], "needs-attention")
        self.assertEqual(activity_by_client_id[client_pending.id]["compliance"], "pending")
        self.assertEqual(activity_by_client_id[client_late.id]["status"], "no-entries")
        self.assertEqual(activity_by_client_id[client_late.id]["compliance"], "late")

    def test_dashboard_summary_is_scoped_to_logged_in_bookkeeper(self):
        today = timezone.localdate()

        owner = self._create_bookkeeper("owner-scope")
        other = self._create_bookkeeper("other-scope")

        owner_client = self._create_client(
            bookkeeper=owner,
            tin_suffix="owner-visible",
            risk=Client.RISK_LOW,
        )
        other_client = self._create_client(
            bookkeeper=other,
            tin_suffix="other-hidden",
            risk=Client.RISK_HIGH,
        )

        self._create_record(
            bookkeeper=owner,
            client=owner_client,
            entry_date=today,
            amount=Decimal("300.00"),
        )
        self._create_record(
            bookkeeper=other,
            client=other_client,
            entry_date=today,
            amount=Decimal("999.00"),
        )

        self._login_as(owner)
        response = self.client.get(reverse("api_dashboard_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["metrics"]["total_clients"], 1)
        self.assertEqual(payload["metrics"]["total_entries_this_month"], 1)
        self.assertEqual(payload["metrics"]["high_risk_clients"], 0)

        activity_client_ids = {row["client_id"] for row in payload.get("recent_client_activity", [])}
        self.assertEqual(activity_client_ids, {owner_client.id})

        recent_entry_client_ids = {row["client_id"] for row in payload.get("recent_entries", [])}
        self.assertEqual(recent_entry_client_ids, {owner_client.id})

    def test_dashboard_summary_recent_entries_are_limited_and_sorted_desc(self):
        today = timezone.localdate()

        owner = self._create_bookkeeper("owner-recent")
        self._login_as(owner)
        client = self._create_client(
            bookkeeper=owner,
            tin_suffix="recent-client",
            risk=Client.RISK_MEDIUM,
        )

        for day in range(1, 8):
            self._create_record(
                bookkeeper=owner,
                client=client,
                entry_date=date(today.year, today.month, day),
                amount=Decimal("100.00") + Decimal(day),
            )

        response = self.client.get(reverse("api_dashboard_summary"), HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        recent_entries = payload.get("recent_entries", [])
        self.assertEqual(len(recent_entries), 5)

        recent_dates = [row["entry_date"] for row in recent_entries]
        expected_dates = [
            date(today.year, today.month, day).isoformat()
            for day in range(7, 2, -1)
        ]
        self.assertEqual(recent_dates, expected_dates)
