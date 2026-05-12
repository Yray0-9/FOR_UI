from django.db import models

from .financial_record_model import FinancialRecord


class FinancialRecordLine(models.Model):
    CALC_ADD = "add"
    CALC_SUBTRACT = "subtract"
    CALC_MULTIPLY = "multiply"
    CALC_DIVIDE = "divide"
    CALC_PERCENT = "percent"

    CALC_OPERATION_CHOICES = [
        (CALC_ADD, "Add"),
        (CALC_SUBTRACT, "Subtract"),
        (CALC_MULTIPLY, "Multiply"),
        (CALC_DIVIDE, "Divide"),
        (CALC_PERCENT, "Percent"),
    ]

    record = models.ForeignKey(
        FinancialRecord,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    calc_target = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="calc_sources",
    )
    type_code = models.CharField(max_length=80)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    calc_operation = models.CharField(max_length=12, choices=CALC_OPERATION_CHOICES, blank=True, default="")
    calc_percent = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    calc_result = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    calc_original_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    calc_applied = models.BooleanField(default=False)
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
