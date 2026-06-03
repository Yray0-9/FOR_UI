from django.db import models

from .client_model import Client
from .period_model import Period
from .user_model import BookkeeperAccount


class FinancialRecord(models.Model):
    FREQUENCY_MONTHLY = "monthly"
    FREQUENCY_QUARTERLY = "quarterly"
    FREQUENCY_ANNUALLY = "annually"
    FREQUENCY_CHOICES = [
        (FREQUENCY_MONTHLY, "Monthly"),
        (FREQUENCY_QUARTERLY, "Quarterly"),
        (FREQUENCY_ANNUALLY, "Annually"),
    ]

    bookkeeper = models.ForeignKey(
        BookkeeperAccount,
        on_delete=models.CASCADE,
        related_name="financial_records",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="financial_records",
    )
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name="financial_records",
    )
    entry_date = models.DateField()
    frequency = models.CharField(max_length=16, choices=FREQUENCY_CHOICES, default=FREQUENCY_MONTHLY)
    notes = models.TextField(blank=True, default="")
    deadline_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_records"
        ordering = ["-entry_date", "-id"]
        indexes = [
            models.Index(fields=["bookkeeper"]),
            models.Index(fields=["client"]),
            models.Index(fields=["period"]),
            models.Index(fields=["entry_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.client_name} - {self.entry_date}"
