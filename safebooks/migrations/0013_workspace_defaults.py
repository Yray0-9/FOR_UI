from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0012_remove_email_verification_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkspaceDefaults",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "default_client_scope",
                    models.CharField(
                        choices=[("all", "All clients"), ("last", "Last used client")],
                        default="all",
                        max_length=12,
                    ),
                ),
                (
                    "default_report_type",
                    models.CharField(
                        choices=[
                            ("financial_summary", "Financial Summary"),
                            ("compliance_snapshot", "Compliance Snapshot"),
                            ("client_risk_overview", "Client Risk Overview"),
                        ],
                        default="financial_summary",
                        max_length=32,
                    ),
                ),
                (
                    "default_report_range",
                    models.CharField(
                        choices=[
                            ("ytd", "Year-to-date"),
                            ("30", "Last 30 days"),
                            ("90", "Last 90 days"),
                            ("custom", "Custom"),
                        ],
                        default="ytd",
                        max_length=12,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "bookkeeper",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workspace_defaults",
                        to="safebooks.bookkeeperaccount",
                    ),
                ),
                (
                    "last_client",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="workspace_last_used_by",
                        to="safebooks.client",
                    ),
                ),
            ],
            options={
                "db_table": "workspace_defaults",
                "ordering": ["-updated_at", "-id"],
            },
        ),
    ]
