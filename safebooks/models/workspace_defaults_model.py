from django.db import models

from .client_model import Client
from .user_model import BookkeeperAccount


class WorkspaceDefaults(models.Model):
    SCOPE_ALL = "all"
    SCOPE_LAST = "last"
    SCOPE_CHOICES = [
        (SCOPE_ALL, "All clients"),
        (SCOPE_LAST, "Last used client"),
    ]

    REPORT_TYPE_FINANCIAL = "financial_summary"
    REPORT_TYPE_COMPLIANCE = "compliance_snapshot"
    REPORT_TYPE_RISK = "client_risk_overview"
    REPORT_TYPE_CHOICES = [
        (REPORT_TYPE_FINANCIAL, "Financial Summary"),
        (REPORT_TYPE_COMPLIANCE, "Compliance Snapshot"),
        (REPORT_TYPE_RISK, "Client Risk Overview"),
    ]

    REPORT_RANGE_YTD = "ytd"
    REPORT_RANGE_30 = "30"
    REPORT_RANGE_90 = "90"
    REPORT_RANGE_CUSTOM = "custom"
    REPORT_RANGE_CHOICES = [
        (REPORT_RANGE_YTD, "Year-to-date"),
        (REPORT_RANGE_30, "Last 30 days"),
        (REPORT_RANGE_90, "Last 90 days"),
        (REPORT_RANGE_CUSTOM, "Custom"),
    ]

    bookkeeper = models.OneToOneField(
        BookkeeperAccount,
        on_delete=models.CASCADE,
        related_name="workspace_defaults",
    )
    default_client_scope = models.CharField(
        max_length=12,
        choices=SCOPE_CHOICES,
        default=SCOPE_ALL,
    )
    default_report_type = models.CharField(
        max_length=32,
        choices=REPORT_TYPE_CHOICES,
        default=REPORT_TYPE_FINANCIAL,
    )
    default_report_range = models.CharField(
        max_length=12,
        choices=REPORT_RANGE_CHOICES,
        default=REPORT_RANGE_YTD,
    )
    last_client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workspace_last_used_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workspace_defaults"
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return f"Workspace defaults for {self.bookkeeper_id}"
