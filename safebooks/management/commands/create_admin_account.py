import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from safebooks.models import AdminAccount
from safebooks.validators.password_validator import missing_password_requirements


class Command(BaseCommand):
    help = "Create a SafeBooks admin account."

    def add_arguments(self, parser):
        parser.add_argument("--email", dest="email")
        parser.add_argument("--full-name", dest="full_name")
        parser.add_argument("--password", dest="password")
        parser.add_argument(
            "--inactive",
            action="store_true",
            help="Create the admin account as inactive.",
        )

    def handle(self, *args, **options):
        email = str(options.get("email") or "").strip()
        full_name = str(options.get("full_name") or "").strip()
        password = str(options.get("password") or "")

        if not email:
            email = input("Admin email: ").strip()
        if not full_name:
            full_name = input("Admin full name: ").strip()
        if not password:
            password = getpass.getpass("Admin password: ")
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                raise CommandError("Passwords do not match.")

        if not email:
            raise CommandError("Email is required.")
        if not full_name:
            raise CommandError("Full name is required.")
        if not password:
            raise CommandError("Password is required.")

        requirement_errors = missing_password_requirements(password)
        if requirement_errors:
            raise CommandError(
                "Password does not meet requirements: " + ", ".join(requirement_errors)
            )

        if AdminAccount.objects.filter(email__iexact=email).exists():
            raise CommandError("Admin account already exists with that email.")

        admin = AdminAccount.objects.create(
            full_name=full_name,
            email=email,
            password_hash=make_password(password),
            is_active=not options.get("inactive", False),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Admin account created: {admin.full_name} <{admin.email}>"
            )
        )
