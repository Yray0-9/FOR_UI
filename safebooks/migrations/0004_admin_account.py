from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0003_period_financialrecord_financialrecordline_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password_hash", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "admin_accounts",
                "ordering": ["-created_at"],
            },
        ),
    ]
