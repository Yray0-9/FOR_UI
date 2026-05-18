from django.db import migrations, models
import django.db.models.deletion


def backfill_bookkeeper_status(apps, schema_editor):
    BookkeeperAccount = apps.get_model("safebooks", "BookkeeperAccount")
    BookkeeperAccount.objects.all().update(status="approved")


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0004_admin_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                    ("suspended", "Suspended"),
                ],
                db_index=True,
                default="pending",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="approved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="approved_by_admin",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_bookkeepers",
                to="safebooks.adminaccount",
            ),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="rejected_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="rejection_reason",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="last_login",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_bookkeeper_status, migrations.RunPython.noop),
    ]
