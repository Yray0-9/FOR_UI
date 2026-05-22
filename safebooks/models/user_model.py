from django.db import models

from .admin_model import AdminAccount


class BookkeeperAccount(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_SUSPENDED = "suspended"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_SUSPENDED, "Suspended"),
    ]

    full_name = models.CharField(max_length=120)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    location = models.CharField(max_length=180, blank=True, default="")
    email_verified = models.BooleanField(default=True)
    login_alerts_enabled = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=255)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=64, blank=True, default="")
    two_factor_confirmed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by_admin = models.ForeignKey(
        AdminAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_bookkeepers",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True, default="")
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookkeeper_accounts"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"
