from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0017_bookkeeper_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="email_password",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="client",
            name="orus_account",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="client",
            name="orus_password",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
