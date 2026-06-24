from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0023_client_forecast_growth_percent"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="client_details_password_required",
            field=models.BooleanField(default=True),
        ),
    ]
