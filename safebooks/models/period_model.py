from django.db import models

from .client_model import Client


class Period(models.Model):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    MONTH_CHOICES = [
        (JANUARY, "January"),
        (FEBRUARY, "February"),
        (MARCH, "March"),
        (APRIL, "April"),
        (MAY, "May"),
        (JUNE, "June"),
        (JULY, "July"),
        (AUGUST, "August"),
        (SEPTEMBER, "September"),
        (OCTOBER, "October"),
        (NOVEMBER, "November"),
        (DECEMBER, "December"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="periods",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "periods"
        ordering = ["-year", "-month", "id"]
        unique_together = [("client", "year", "month")]
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["year", "month"]),
        ]

    def __str__(self) -> str:
        month_label = dict(self.MONTH_CHOICES).get(self.month, str(self.month))
        return f"{self.client.client_name} - {month_label} {self.year}"
