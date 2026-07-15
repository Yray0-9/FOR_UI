from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0028_bookkeeper_deactivation_request"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="client_record_email_notifications_enabled",
            field=models.BooleanField(default=True),
        ),
    ]
