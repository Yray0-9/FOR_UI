from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0016_bookkeeper_login_alerts"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookkeeperaccount",
            name="location",
            field=models.CharField(max_length=180, blank=True, default=""),
        ),
    ]
