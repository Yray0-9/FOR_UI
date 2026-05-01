from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q

from safebooks.models import BookkeeperAccount
from safebooks.validators.password_validator import missing_password_requirements


AUTH_FAILURE_MESSAGE = "Invalid credentials."


def _looks_like_supported_hash(password_hash: str) -> bool:
    normalized_hash = str(password_hash or "")
    return normalized_hash.startswith((
        "pbkdf2_",
        "argon2$",
        "bcrypt$",
        "bcrypt_sha256$",
        "scrypt$",
    ))


def register_user(data: dict) -> dict:
    full_name = str(data.get("full_name", "")).strip()
    email = str(data.get("email", "")).strip()
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))
    confirm_password = str(data.get("confirm_password", ""))

    errors: list[str] = []

    if not full_name:
        errors.append("Full name is required.")
    if not email:
        errors.append("Email is required.")
    if not username:
        errors.append("Username is required.")
    if not password:
        errors.append("Password is required.")
    if password and password != confirm_password:
        errors.append("Passwords do not match.")

    password_requirement_errors = missing_password_requirements(password)
    if password and password_requirement_errors:
        errors.append("Password does not meet requirements.")

    if errors:
        return {
            "ok": False,
            "message": errors[0],
            "errors": errors,
            "password_requirements": password_requirement_errors,
        }

    if BookkeeperAccount.objects.filter(email__iexact=email).exists():
        return {
            "ok": False,
            "message": "Email already exists.",
            "errors": ["Email already exists."],
        }

    if BookkeeperAccount.objects.filter(username__iexact=username).exists():
        return {
            "ok": False,
            "message": "Username already exists.",
            "errors": ["Username already exists."],
        }

    account = BookkeeperAccount.objects.create(
        full_name=full_name,
        email=email,
        username=username,
        password_hash=make_password(password),
    )

    return {
        "ok": True,
        "message": "Account created successfully.",
        "user": {
            "id": account.id,
            "full_name": account.full_name,
            "email": account.email,
            "username": account.username,
        },
    }


def login_user(data: dict) -> dict:
    identifier = str(data.get("identifier", "")).strip()
    password = str(data.get("password", ""))

    if not identifier or not password:
        return {
            "ok": False,
            "message": "Email or username and password are required.",
            "errors": ["Email or username and password are required."],
        }

    account = BookkeeperAccount.objects.filter(
        Q(email__iexact=identifier) | Q(username__iexact=identifier)
    ).first()

    if account is None:
        return {
            "ok": False,
            "message": AUTH_FAILURE_MESSAGE,
            "errors": [AUTH_FAILURE_MESSAGE],
        }

    stored_password_hash = str(account.password_hash or "")
    is_authenticated = check_password(password, stored_password_hash)

    # Backward compatibility for early records that stored raw passwords.
    if not is_authenticated and stored_password_hash and not _looks_like_supported_hash(stored_password_hash):
        if password == stored_password_hash:
            is_authenticated = True
            account.password_hash = make_password(password)
            account.save(update_fields=["password_hash"])

    if not is_authenticated:
        return {
            "ok": False,
            "message": AUTH_FAILURE_MESSAGE,
            "errors": [AUTH_FAILURE_MESSAGE],
        }

    return {
        "ok": True,
        "message": "Login successful.",
        "user": {
            "id": account.id,
            "full_name": account.full_name,
            "email": account.email,
            "username": account.username,
        },
    }
