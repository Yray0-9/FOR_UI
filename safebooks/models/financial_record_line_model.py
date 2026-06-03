from django.db import models

from .financial_record_model import FinancialRecord


class FinancialRecordLine(models.Model):
    record = models.ForeignKey(
        FinancialRecord,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    type_code = models.CharField(max_length=80)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financial_record_lines"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["record"]),
            models.Index(fields=["type_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.type_code} - {self.amount}"
