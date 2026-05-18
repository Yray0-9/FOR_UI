from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0004_admin_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="email_verified",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="email_verification_code_hash",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="email_verification_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="email_verification_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
