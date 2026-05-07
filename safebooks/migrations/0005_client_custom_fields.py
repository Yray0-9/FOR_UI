from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0004_admin_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="custom_fields",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
