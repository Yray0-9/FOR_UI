import json

from django.test import TestCase
from django.urls import reverse

from safebooks.models import BookkeeperAccount, Client
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class ClientsApiTests(TestCase):
    def _create_bookkeeper(self, suffix: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Bookkeeper {suffix}",
            username=f"clients_{suffix}",
            email=f"clients_{suffix}@example.com",
            password_hash="not-used-in-test",
            status=BookkeeperAccount.STATUS_APPROVED,
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

    def _client_payload(self, suffix: str, tin: str | None = None) -> dict:
        return {
            "client_name": f"Client {suffix}",
            "tin_number": tin or self._build_tin(suffix),
            "trade_name": f"Trade {suffix}",
            "location": "Panabo City",
            "permit_number": f"PERMIT-{suffix}",
            "birthday": "1995-07-12",
            "email": f"client-{suffix}@example.com",
            "remarks": Client.REMARK_ACTIVE,
        }

    def test_clients_api_requires_authentication(self):
        get_response = self.client.get(reverse("api_clients"), HTTP_ACCEPT="application/json")
        self.assertEqual(get_response.status_code, 401)
        self.assertFalse(get_response.json().get("ok"))

        post_response = self.client.post(
            reverse("api_clients"),
            data=json.dumps(self._client_payload("unauth")),
            content_type="application/json",
        )
        self.assertEqual(post_response.status_code, 401)
        self.assertFalse(post_response.json().get("ok"))

    def test_clients_create_update_delete_success(self):
        owner = self._create_bookkeeper("owner-crud")
        self._login_as(owner)

        create_response = self.client.post(
            reverse("api_clients"),
            data=json.dumps(self._client_payload("crud")),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        create_payload = create_response.json()
        self.assertTrue(create_payload.get("ok"))
        self.assertEqual(create_payload.get("message"), "Client added successfully.")

        client_id = create_payload["client"]["id"]
        list_response = self.client.get(reverse("api_clients"), HTTP_ACCEPT="application/json")
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.json()
        self.assertTrue(list_payload.get("ok"))
        self.assertEqual(len(list_payload.get("clients", [])), 1)
        self.assertEqual(list_payload["clients"][0]["id"], client_id)

        update_data = self._client_payload("crud-updated", tin=self._build_tin("crud-updated"))
        update_data["remarks"] = Client.REMARK_CLOSED
        update_response = self.client.put(
            reverse("api_client_detail", kwargs={"client_id": client_id}),
            data=json.dumps(update_data),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        update_payload = update_response.json()
        self.assertTrue(update_payload.get("ok"))
        self.assertEqual(update_payload.get("message"), "Client updated successfully.")
        self.assertEqual(update_payload["client"]["remarks"], Client.REMARK_CLOSED)

        delete_response = self.client.delete(
            reverse("api_client_detail", kwargs={"client_id": client_id}),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(delete_response.status_code, 200)
        delete_payload = delete_response.json()
        self.assertTrue(delete_payload.get("ok"))
        self.assertEqual(delete_payload.get("message"), "Client closed successfully.")
        self.assertEqual(delete_payload["client"]["remarks"], Client.REMARK_CLOSED)

        final_list_response = self.client.get(reverse("api_clients"), HTTP_ACCEPT="application/json")
        self.assertEqual(final_list_response.status_code, 200)
        self.assertEqual(len(final_list_response.json().get("clients", [])), 1)
        self.assertEqual(final_list_response.json()["clients"][0]["remarks"], Client.REMARK_CLOSED)
        self.assertEqual(Client.objects.filter(bookkeeper=owner).count(), 1)

    def test_clients_api_enforces_ownership_isolation(self):
        owner = self._create_bookkeeper("owner-isolation")
        other = self._create_bookkeeper("other-isolation")

        owner_client = Client.objects.create(
            bookkeeper=owner,
            client_name="Owner Visible",
            tin_number=self._build_tin("owner-001"),
            trade_name="Owner Trade",
            location="Panabo",
            permit_number="PERMIT-OWNER-001",
            email="owner-visible@example.com",
            remarks=Client.REMARK_NEW,
        )
        other_client = Client.objects.create(
            bookkeeper=other,
            client_name="Other Hidden",
            tin_number=self._build_tin("other-002"),
            trade_name="Other Trade",
            location="Panabo",
            permit_number="PERMIT-OTHER-001",
            email="other-hidden@example.com",
            remarks=Client.REMARK_CLOSED,
        )

        self._login_as(owner)

        list_response = self.client.get(reverse("api_clients"), HTTP_ACCEPT="application/json")
        self.assertEqual(list_response.status_code, 200)
        listed_ids = {row["id"] for row in list_response.json().get("clients", [])}
        self.assertEqual(listed_ids, {owner_client.id})

        update_response = self.client.put(
            reverse("api_client_detail", kwargs={"client_id": other_client.id}),
            data=json.dumps(self._client_payload("forbidden-update", tin=self._build_tin("forbidden-update"))),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(update_response.json().get("message"), "Client not found.")

        delete_response = self.client.delete(
            reverse("api_client_detail", kwargs={"client_id": other_client.id}),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(delete_response.status_code, 404)
        self.assertEqual(delete_response.json().get("message"), "Client not found.")

    def test_clients_api_rejects_duplicate_tin(self):
        owner = self._create_bookkeeper("owner-dup")
        self._login_as(owner)

        duplicate_tin = self._build_tin("dup-001")

        first_create = self.client.post(
            reverse("api_clients"),
            data=json.dumps(self._client_payload("dup-first", tin=duplicate_tin)),
            content_type="application/json",
        )
        self.assertEqual(first_create.status_code, 201)

        duplicate_create = self.client.post(
            reverse("api_clients"),
            data=json.dumps(self._client_payload("dup-second", tin=duplicate_tin)),
            content_type="application/json",
        )
        self.assertEqual(duplicate_create.status_code, 409)
        duplicate_payload = duplicate_create.json()
        self.assertFalse(duplicate_payload.get("ok"))
        self.assertEqual(duplicate_payload.get("message"), "TIN already exists.")

    def test_clients_api_rejects_invalid_payload_fields(self):
        owner = self._create_bookkeeper("owner-invalid")
        self._login_as(owner)

        invalid_email_payload = self._client_payload("invalid-email")
        invalid_email_payload["email"] = "not-an-email"

        response = self.client.post(
            reverse("api_clients"),
            data=json.dumps(invalid_email_payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Email format is invalid.")

    def test_clients_api_rejects_invalid_json_payload(self):
        owner = self._create_bookkeeper("owner-json")
        self._login_as(owner)

        response = self.client.post(
            reverse("api_clients"),
            data="{invalid-json}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Invalid request payload.")
