import json
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from safebooks.models import (
    BookkeeperAccount,
    Client,
    FinancialRecord,
    FinancialRecordLine,
    Period,
)
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class FinancialRecordsApiTests(TestCase):
    def _create_bookkeeper(self, suffix: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Bookkeeper {suffix}",
            username=f"fin_{suffix}",
            email=f"fin_{suffix}@example.com",
            password_hash="not-used-in-test",
        )

    def _login_as(self, account: BookkeeperAccount) -> None:
        session = self.client.session
        session[SESSION_BOOKKEEPER_ID_KEY] = account.id
        session.save()

    def _create_client(self, *, bookkeeper: BookkeeperAccount, suffix: str) -> Client:
        return Client.objects.create(
            bookkeeper=bookkeeper,
            client_name=f"Client {suffix}",
            tin_number=f"TIN-FIN-{suffix}",
            trade_name=f"Trade {suffix}",
            location="Panabo City",
            permit_number=f"PERMIT-FIN-{suffix}",
            email=f"client-fin-{suffix}@example.com",
            risk_level=Client.RISK_MEDIUM,
        )

    def _create_record(
        self,
        *,
        bookkeeper: BookkeeperAccount,
        client: Client,
        year: int,
        month: int,
        day: int,
        amount: Decimal,
        type_code: str = "1701",
    ) -> FinancialRecord:
        period, _ = Period.objects.get_or_create(client=client, year=year, month=month)
        record = FinancialRecord.objects.create(
            bookkeeper=bookkeeper,
            client=client,
            period=period,
            entry_date=date(year, month, day),
            notes="Existing record",
            total_amount=amount,
        )
        FinancialRecordLine.objects.create(
            record=record,
            type_code=type_code,
            description="Line item",
            amount=amount,
            sort_order=1,
        )
        return record

    def _build_create_payload(self) -> dict:
        return {
            "month": 4,
            "year": 2026,
            "date": "2026-04-15",
            "frequency": "quarterly",
            "notes": "Created via test",
            "line_items": [
                {
                    "type_code": "Sales",
                    "description": "Primary sale",
                    "amount": "1000.00",
                },
                {
                    "type_code": "1701",
                    "description": "Tax",
                    "amount": "120.00",
                },
            ],
        }

    def test_financial_records_api_requires_authentication(self):
        owner = self._create_bookkeeper("auth-owner")
        client = self._create_client(bookkeeper=owner, suffix="auth-client")

        clients_response = self.client.get(
            reverse("api_financial_record_clients"),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(clients_response.status_code, 401)
        self.assertFalse(clients_response.json().get("ok"))

        records_response = self.client.get(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(records_response.status_code, 401)
        self.assertFalse(records_response.json().get("ok"))

        create_response = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            data=json.dumps(self._build_create_payload()),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 401)
        self.assertFalse(create_response.json().get("ok"))

    def test_financial_record_clients_list_is_scoped_and_includes_activity_metadata(self):
        owner = self._create_bookkeeper("owner-clients")
        other = self._create_bookkeeper("other-clients")

        owner_active = self._create_client(bookkeeper=owner, suffix="owner-active")
        owner_none = self._create_client(bookkeeper=owner, suffix="owner-none")
        other_active = self._create_client(bookkeeper=other, suffix="other-active")

        self._create_record(
            bookkeeper=owner,
            client=owner_active,
            year=2026,
            month=4,
            day=11,
            amount=Decimal("500.00"),
        )
        self._create_record(
            bookkeeper=other,
            client=other_active,
            year=2026,
            month=4,
            day=12,
            amount=Decimal("900.00"),
        )

        self._login_as(owner)
        response = self.client.get(reverse("api_financial_record_clients"), HTTP_ACCEPT="application/json")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok"))

        rows_by_id = {row["id"]: row for row in payload.get("clients", [])}
        self.assertEqual(set(rows_by_id), {owner_active.id, owner_none.id})

        self.assertEqual(rows_by_id[owner_active.id]["activity_state"], "active")
        self.assertEqual(rows_by_id[owner_active.id]["financial_record_count"], 1)
        self.assertEqual(rows_by_id[owner_none.id]["activity_state"], "none")
        self.assertEqual(rows_by_id[owner_none.id]["financial_record_count"], 0)

    def test_financial_records_api_enforces_client_ownership_isolation(self):
        owner = self._create_bookkeeper("owner-isolation")
        other = self._create_bookkeeper("other-isolation")

        other_client = self._create_client(bookkeeper=other, suffix="other-client")
        other_record = self._create_record(
            bookkeeper=other,
            client=other_client,
            year=2026,
            month=4,
            day=14,
            amount=Decimal("750.00"),
        )

        self._login_as(owner)

        list_response = self.client.get(
            reverse("api_financial_records", kwargs={"client_id": other_client.id}),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(list_response.status_code, 404)
        self.assertEqual(list_response.json().get("message"), "Client not found.")

        create_response = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": other_client.id}),
            data=json.dumps(self._build_create_payload()),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 404)
        self.assertEqual(create_response.json().get("message"), "Client not found.")

        update_response = self.client.put(
            reverse(
                "api_financial_record_detail",
                kwargs={"client_id": other_client.id, "record_id": other_record.id},
            ),
            data=json.dumps(self._build_create_payload()),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(update_response.json().get("message"), "Client not found.")

        delete_response = self.client.delete(
            reverse(
                "api_financial_record_detail",
                kwargs={"client_id": other_client.id, "record_id": other_record.id},
            ),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(delete_response.status_code, 404)
        self.assertEqual(delete_response.json().get("message"), "Client not found.")

    def test_financial_records_crud_success_with_line_items_and_period_cleanup(self):
        owner = self._create_bookkeeper("owner-crud")
        client = self._create_client(bookkeeper=owner, suffix="crud")
        self._login_as(owner)

        create_response = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            data=json.dumps(self._build_create_payload()),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        create_payload = create_response.json()
        self.assertTrue(create_payload.get("ok"))
        self.assertEqual(create_payload.get("message"), "Financial entry added successfully.")
        self.assertEqual(create_payload["record"]["total_amount"], "1120.00")
        self.assertEqual(create_payload["record"]["line_items_count"], 2)
        self.assertEqual(create_payload["record"]["frequency"], "quarterly")

        record_id = create_payload["record"]["id"]

        list_response = self.client.get(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            {"month": 4, "year": 2026},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertTrue(list_payload.get("ok"))
        self.assertEqual(len(list_payload.get("records", [])), 1)
        self.assertEqual(list_payload["summary"]["total_amount"], "1120.00")

        update_payload = {
            "month": 4,
            "year": 2026,
            "date": "2026-04-18",
            "frequency": "annually",
            "notes": "Updated via test",
            "line_items": [
                {
                    "type_code": "Sales",
                    "description": "Updated sale",
                    "amount": "900.00",
                },
                {
                    "type_code": "Expenses",
                    "description": "Updated expense",
                    "amount": "100.00",
                },
            ],
        }
        update_response = self.client.put(
            reverse(
                "api_financial_record_detail",
                kwargs={"client_id": client.id, "record_id": record_id},
            ),
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        update_json = update_response.json()
        self.assertTrue(update_json.get("ok"))
        self.assertEqual(update_json.get("message"), "Financial entry updated successfully.")
        self.assertEqual(update_json["record"]["total_amount"], "1000.00")
        self.assertEqual(update_json["record"]["frequency"], "annually")

        delete_response = self.client.delete(
            reverse(
                "api_financial_record_detail",
                kwargs={"client_id": client.id, "record_id": record_id},
            ),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(delete_response.status_code, 200)
        delete_payload = delete_response.json()
        self.assertTrue(delete_payload.get("ok"))
        self.assertEqual(delete_payload.get("message"), "Financial entry deleted successfully.")

        self.assertEqual(FinancialRecord.objects.filter(client=client).count(), 0)
        self.assertEqual(Period.objects.filter(client=client, year=2026, month=4).count(), 0)

    def test_financial_records_line_item_validation_errors(self):
        owner = self._create_bookkeeper("owner-validation")
        client = self._create_client(bookkeeper=owner, suffix="validation")
        self._login_as(owner)

        negative_amount_payload = self._build_create_payload()
        negative_amount_payload["line_items"] = [
            {
                "type_code": "Sales",
                "description": "Negative test",
                "amount": "-1",
            }
        ]
        response_negative = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            data=json.dumps(negative_amount_payload),
            content_type="application/json",
        )
        self.assertEqual(response_negative.status_code, 400)
        self.assertEqual(
            response_negative.json().get("message"),
            "Line item #1: Amount cannot be negative.",
        )

        missing_items_payload = self._build_create_payload()
        missing_items_payload["line_items"] = []
        response_missing = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            data=json.dumps(missing_items_payload),
            content_type="application/json",
        )
        self.assertEqual(response_missing.status_code, 400)
        self.assertEqual(
            response_missing.json().get("message"),
            "At least one line item is required.",
        )

    def test_financial_records_period_and_date_validation_edges(self):
        owner = self._create_bookkeeper("owner-period")
        client = self._create_client(bookkeeper=owner, suffix="period")
        self._login_as(owner)

        invalid_month_response = self.client.get(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            {"month": 13, "year": 2026},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(invalid_month_response.status_code, 400)
        self.assertEqual(invalid_month_response.json().get("message"), "Invalid period month.")

        invalid_year_response = self.client.get(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            {"month": 4, "year": 1999},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(invalid_year_response.status_code, 400)
        self.assertEqual(
            invalid_year_response.json().get("message"),
            "Period year must be between 2000 and 2100.",
        )

        date_mismatch_payload = self._build_create_payload()
        date_mismatch_payload["month"] = 4
        date_mismatch_payload["year"] = 2026
        date_mismatch_payload["date"] = "2026-05-01"

        mismatch_response = self.client.post(
            reverse("api_financial_records", kwargs={"client_id": client.id}),
            data=json.dumps(date_mismatch_payload),
            content_type="application/json",
        )
        self.assertEqual(mismatch_response.status_code, 201)
        payload = mismatch_response.json()
        self.assertTrue(payload.get("ok"))

        record_id = payload.get("record", {}).get("id")
        self.assertTrue(record_id)

        record = FinancialRecord.objects.get(id=record_id)
        self.assertEqual(record.entry_date.isoformat(), "2026-05-01")
        self.assertEqual(record.period.month, 5)
        self.assertEqual(record.period.year, 2026)
