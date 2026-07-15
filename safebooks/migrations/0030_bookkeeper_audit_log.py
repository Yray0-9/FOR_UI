from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0029_bookkeeper_client_record_email_notifications"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookkeeperAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(db_index=True, max_length=80)),
                ("target_model", models.CharField(blank=True, default="", max_length=80)),
                ("target_id", models.PositiveIntegerField(blank=True, null=True)),
                ("message", models.CharField(max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("bookkeeper", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="safebooks.bookkeeperaccount")),
            ],
            options={
                "db_table": "bookkeeper_audit_logs",
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="bookkeeperauditlog",
            index=models.Index(fields=["bookkeeper", "-created_at"], name="bk_audit_owner_time_idx"),
        ),
        migrations.AddIndex(
            model_name="bookkeeperauditlog",
            index=models.Index(fields=["bookkeeper", "action_type"], name="bk_audit_owner_action_idx"),
        ),
        migrations.AddIndex(
            model_name="bookkeeperauditlog",
            index=models.Index(fields=["target_model", "target_id"], name="bk_audit_target_idx"),
        ),
    ]
