from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0013_workspace_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="workspacedefaults",
            name="default_report_range_from",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="workspacedefaults",
            name="default_report_range_to",
            field=models.DateField(blank=True, null=True),
        ),
    ]
