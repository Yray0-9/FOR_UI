import json

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from safebooks.models import BookkeeperAccount, Client
from safebooks.views import SESSION_BOOKKEEPER_ID_KEY


class ClientDetailsAccessSecurityTests(TestCase):
    def _create_bookkeeper(self, *, lock_enabled=False) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name="Security Tester",
            username=f"security_tester_{int(lock_enabled)}",
            email=f"security_tester_{int(lock_enabled)}@example.com",
            password_hash=make_password("SafeBooks#123"),
            status=BookkeeperAccount.STATUS_APPROVED,
            client_details_password_required=lock_enabled,
        )

    def _login_as(self, account: BookkeeperAccount) -> None:
        session = self.client.session
        session[SESSION_BOOKKEEPER_ID_KEY] = account.id
        session.save()

    def _create_client(self, account: BookkeeperAccount) -> Client:
        return Client.objects.create(
            bookkeeper=account,
            client_name="Protected Client",
            tin_number="123456789000",
            trade_name="Protected Trade",
            location="Davao Del Norte",
            remarks=Client.REMARK_ACTIVE,
        )

    def test_client_details_open_when_lock_disabled(self):
        account = self._create_bookkeeper(lock_enabled=False)
        self._login_as(account)
        client = self._create_client(account)

        response = self.client.get(reverse("client_details", args=[client.id]))

        self.assertEqual(response.status_code, 200)

    def test_client_details_redirects_when_lock_enabled_without_confirmation(self):
        account = self._create_bookkeeper(lock_enabled=True)
        self._login_as(account)
        client = self._create_client(account)

        response = self.client.get(reverse("client_details", args=[client.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("clients"), response["Location"])
        self.assertIn("client_access_required=1", response["Location"])

    def test_client_details_confirmation_rejects_wrong_password(self):
        account = self._create_bookkeeper(lock_enabled=True)
        self._login_as(account)

        response = self.client.post(
            reverse("api_security_client_details_access_confirm"),
            data=json.dumps({"current_password": "WrongPassword#123"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get("ok"))

    def test_client_details_confirmation_allows_recent_access(self):
        account = self._create_bookkeeper(lock_enabled=True)
        self._login_as(account)
        client = self._create_client(account)

        confirm_response = self.client.post(
            reverse("api_security_client_details_access_confirm"),
            data=json.dumps({"current_password": "SafeBooks#123"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.assertTrue(confirm_response.json().get("ok"))

        detail_response = self.client.get(reverse("client_details", args=[client.id]))
        self.assertEqual(detail_response.status_code, 200)

    def test_preference_update_requires_password_and_can_disable_lock(self):
        account = self._create_bookkeeper(lock_enabled=True)
        self._login_as(account)
        client = self._create_client(account)

        response = self.client.post(
            reverse("api_security_client_details_access_preference"),
            data=json.dumps({"enabled": False, "current_password": "SafeBooks#123"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get("client_details_password_required"))

        detail_response = self.client.get(reverse("client_details", args=[client.id]))
        self.assertEqual(detail_response.status_code, 200)
