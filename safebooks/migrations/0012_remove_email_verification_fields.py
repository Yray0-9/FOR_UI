from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0011_merge_20260518_0511"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bookkeeperaccount",
            name="email_verification_code_hash",
        ),
        migrations.RemoveField(
            model_name="bookkeeperaccount",
            name="email_verification_expires_at",
        ),
        migrations.RemoveField(
            model_name="bookkeeperaccount",
            name="email_verification_sent_at",
        ),
    ]
