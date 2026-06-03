from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("safebooks", "0018_client_credentials_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_target",
        ),
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_operation",
        ),
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_percent",
        ),
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_result",
        ),
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_original_amount",
        ),
        migrations.RemoveField(
            model_name="financialrecordline",
            name="calc_applied",
        ),
    ]
