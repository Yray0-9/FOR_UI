from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from safebooks.models import AdminAccount, BookkeeperAccount
from safebooks.views import SESSION_ADMIN_ID_KEY, SESSION_BOOKKEEPER_ID_KEY


class AdminApprovalsApiTests(TestCase):
    def _create_admin(self, suffix: str) -> AdminAccount:
        return AdminAccount.objects.create(
            full_name=f"Admin {suffix}",
            email=f"admin_{suffix}@example.com",
            password_hash="not-used-in-test",
            is_active=True,
        )

    def _login_admin(self, account: AdminAccount) -> None:
        session = self.client.session
        session[SESSION_ADMIN_ID_KEY] = account.id
        session.save()

    def _create_bookkeeper(self, suffix: str, status: str) -> BookkeeperAccount:
        return BookkeeperAccount.objects.create(
            full_name=f"Bookkeeper {suffix}",
            username=f"bookkeeper_{suffix}",
            email=f"bookkeeper_{suffix}@example.com",
            password_hash="not-used-in-test",
            status=status,
        )

    def _login_bookkeeper(self, account: BookkeeperAccount) -> None:
        session = self.client.session
        session[SESSION_BOOKKEEPER_ID_KEY] = account.id
        session.save()

    def test_admin_approvals_requires_admin_authentication(self):
        response = self.client.get(
            reverse("api_admin_approvals"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Admin authentication required.")

    def test_admin_approvals_blocks_bookkeeper_session(self):
        bookkeeper = self._create_bookkeeper("bk", BookkeeperAccount.STATUS_APPROVED)
        self._login_bookkeeper(bookkeeper)

        response = self.client.get(
            reverse("api_admin_approvals"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Admin access required.")

    def test_admin_approvals_list_returns_counts_and_rows(self):
        admin = self._create_admin("list")
        self._login_admin(admin)

        pending = self._create_bookkeeper("pending", BookkeeperAccount.STATUS_PENDING)
        approved = self._create_bookkeeper("approved", BookkeeperAccount.STATUS_APPROVED)
        rejected = self._create_bookkeeper("rejected", BookkeeperAccount.STATUS_REJECTED)
        self._create_bookkeeper("suspended", BookkeeperAccount.STATUS_SUSPENDED)

        response = self.client.get(
            reverse("api_admin_approvals"),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok"))

        counts = payload.get("counts", {})
        self.assertEqual(counts.get("pending"), 1)
        self.assertEqual(counts.get("approved"), 1)
        self.assertEqual(counts.get("rejected"), 1)
        self.assertEqual(payload.get("total_count"), 3)

        approvals = payload.get("approvals", [])
        approval_ids = {row.get("id") for row in approvals}
        self.assertEqual(approval_ids, {pending.id, approved.id, rejected.id})

    def test_admin_approvals_can_approve_pending(self):
        admin = self._create_admin("approve")
        self._login_admin(admin)
        pending = self._create_bookkeeper("pending-approve", BookkeeperAccount.STATUS_PENDING)

        response = self.client.post(
            reverse("api_admin_approvals_approve", args=[pending.id]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok"))

        pending.refresh_from_db()
        self.assertEqual(pending.status, BookkeeperAccount.STATUS_APPROVED)
        self.assertIsNotNone(pending.approved_at)
        self.assertEqual(pending.approved_by_admin_id, admin.id)
        self.assertEqual(pending.rejection_reason, "")

    def test_admin_approvals_can_approve_rejected(self):
        admin = self._create_admin("reapprove")
        self._login_admin(admin)
        rejected = self._create_bookkeeper("rejected-approve", BookkeeperAccount.STATUS_REJECTED)
        rejected.rejected_at = timezone.now()
        rejected.rejection_reason = "Incomplete details"
        rejected.save(update_fields=["rejected_at", "rejection_reason"])

        response = self.client.post(
            reverse("api_admin_approvals_approve", args=[rejected.id]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        rejected.refresh_from_db()
        self.assertEqual(rejected.status, BookkeeperAccount.STATUS_APPROVED)
        self.assertIsNone(rejected.rejected_at)
        self.assertEqual(rejected.rejection_reason, "")

    def test_admin_approvals_can_reject_pending_with_reason(self):
        admin = self._create_admin("reject")
        self._login_admin(admin)
        pending = self._create_bookkeeper("pending-reject", BookkeeperAccount.STATUS_PENDING)

        response = self.client.post(
            reverse("api_admin_approvals_reject", args=[pending.id]),
            data={"rejection_reason": "Missing requirements"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("ok"))

        pending.refresh_from_db()
        self.assertEqual(pending.status, BookkeeperAccount.STATUS_REJECTED)
        self.assertIsNotNone(pending.rejected_at)
        self.assertEqual(pending.rejection_reason, "Missing requirements")
        self.assertIsNone(pending.approved_at)
        self.assertIsNone(pending.approved_by_admin_id)

    def test_admin_approvals_reject_requires_pending(self):
        admin = self._create_admin("reject-guard")
        self._login_admin(admin)
        approved = self._create_bookkeeper("approved-reject", BookkeeperAccount.STATUS_APPROVED)

        response = self.client.post(
            reverse("api_admin_approvals_reject", args=[approved.id]),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload.get("ok"))
        self.assertEqual(payload.get("message"), "Rejection is only available for pending accounts.")
