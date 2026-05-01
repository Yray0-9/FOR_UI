from django.db import models

from .user_model import BookkeeperAccount


class Client(models.Model):
    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"

    RISK_LEVEL_CHOICES = [
        (RISK_LOW, "Low"),
        (RISK_MEDIUM, "Medium"),
        (RISK_HIGH, "High"),
    ]

    bookkeeper = models.ForeignKey(
        BookkeeperAccount,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    client_name = models.CharField(max_length=160)
    tin_number = models.CharField(max_length=40, unique=True)
    trade_name = models.CharField(max_length=180, blank=True, default="")
    location = models.CharField(max_length=180)
    permit_number = models.CharField(max_length=80)
    birthday = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True, default="")
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default=RISK_MEDIUM,
    )
    date_registered = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients"
        ordering = ["client_name", "id"]
        indexes = [
            models.Index(fields=["bookkeeper"]),
            models.Index(fields=["client_name"]),
            models.Index(fields=["risk_level"]),
        ]

    def __str__(self) -> str:
        return f"{self.client_name} ({self.tin_number})"
