from django.db import migrations, models


def enable_client_details_lock_for_existing_accounts(apps, schema_editor):
    BookkeeperAccount = apps.get_model("safebooks", "BookkeeperAccount")
    BookkeeperAccount.objects.update(client_details_password_required=True)


class Migration(migrations.Migration):

    dependencies = [
        ("safebooks", "0024_bookkeeper_client_details_password_required"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookkeeperaccount",
            name="client_details_password_required",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            enable_client_details_lock_for_existing_accounts,
            migrations.RunPython.noop,
        ),
    ]
