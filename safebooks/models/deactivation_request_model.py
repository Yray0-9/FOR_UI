from django.db import models

from .admin_model import AdminAccount
from .user_model import BookkeeperAccount


class BookkeeperDeactivationRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    bookkeeper = models.ForeignKey(
        BookkeeperAccount,
        on_delete=models.CASCADE,
        related_name="deactivation_requests",
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by_admin = models.ForeignKey(
        AdminAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_deactivation_requests",
    )
    admin_note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "bookkeeper_deactivation_requests"
        ordering = ["-requested_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-requested_at"], name="bk_deact_status_idx"),
            models.Index(fields=["bookkeeper", "status"], name="bk_deact_account_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.bookkeeper.full_name} deactivation request ({self.status})"
