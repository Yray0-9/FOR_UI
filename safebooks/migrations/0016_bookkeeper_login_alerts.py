from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0015_bookkeeper_two_factor_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="login_alerts_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
