import re

import pyotp
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from safebooks.validators.password_validator import missing_password_requirements


TWO_FACTOR_ISSUER = "SafeBooks"
_CODE_CLEANUP_RE = re.compile(r"\D+")


def _normalize_text(value) -> str:
    return str(value or "").strip()


def _normalize_code(value) -> str:
    return _CODE_CLEANUP_RE.sub("", str(value or ""))


def _normalize_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    if cleaned in {"true", "1", "yes", "on"}:
        return True
    if cleaned in {"false", "0", "no", "off"}:
        return False
    return None


def _looks_like_supported_hash(password_hash: str) -> bool:
    normalized_hash = str(password_hash or "")
    return normalized_hash.startswith((
        "pbkdf2_",
        "argon2$",
        "bcrypt$",
        "bcrypt_sha256$",
        "scrypt$",
    ))


def _verify_current_password(account, current_password: str) -> bool:
    stored_password_hash = str(account.password_hash or "")
    if check_password(current_password, stored_password_hash):
        return True

    # Backward compatibility for early records that stored raw passwords.
    if stored_password_hash and not _looks_like_supported_hash(stored_password_hash):
        if current_password == stored_password_hash:
            account.password_hash = make_password(current_password)
            account.save(update_fields=["password_hash"])
            return True

    return False


def change_bookkeeper_password(bookkeeper, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    current_password = str(payload.get("current_password", ""))
    new_password = str(payload.get("new_password", ""))
    confirm_password = str(payload.get("confirm_password", ""))

    errors: list[str] = []

    if not current_password:
        errors.append("Current password is required.")
    if not new_password:
        errors.append("New password is required.")
    if new_password and confirm_password and new_password != confirm_password:
        errors.append("New passwords do not match.")
    if new_password and current_password and new_password == current_password:
        errors.append("New password must be different from the current password.")

    password_requirement_errors = missing_password_requirements(new_password)
    if new_password and password_requirement_errors:
        errors.append("Password does not meet requirements.")

    if errors:
        return {
            "ok": False,
            "message": errors[0],
            "errors": errors,
            "password_requirements": password_requirement_errors,
        }

    if not _verify_current_password(bookkeeper, current_password):
        return {
            "ok": False,
            "message": "Current password is incorrect.",
            "errors": ["Current password is incorrect."],
        }

    bookkeeper.password_hash = make_password(new_password)
    bookkeeper.save(update_fields=["password_hash"])

    return {
        "ok": True,
        "message": "Password updated successfully.",
    }


def update_login_alerts_preference(bookkeeper, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    enabled_value = _normalize_bool(payload.get("enabled"))
    if enabled_value is None:
        return {
            "ok": False,
            "message": "Login alerts setting is required.",
            "errors": ["Login alerts setting is required."],
        }

    bookkeeper.login_alerts_enabled = enabled_value
    bookkeeper.save(update_fields=["login_alerts_enabled"])

    return {
        "ok": True,
        "message": "Login alerts preference updated.",
        "login_alerts_enabled": enabled_value,
    }


def _build_totp_secret() -> str:
    return pyotp.random_base32()


def _build_provisioning_uri(secret: str, account_label: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account_label, issuer_name=TWO_FACTOR_ISSUER)


def _is_two_factor_code_valid(secret: str, code: str) -> bool:
    if not secret:
        return False
    normalized_code = _normalize_code(code)
    if len(normalized_code) < 6:
        return False

    return pyotp.TOTP(secret).verify(normalized_code, valid_window=1)


def create_two_factor_setup(bookkeeper, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    current_password = str(payload.get("current_password", ""))
    if not current_password:
        return {
            "ok": False,
            "message": "Current password is required.",
            "errors": ["Current password is required."],
        }

    if not _verify_current_password(bookkeeper, current_password):
        return {
            "ok": False,
            "message": "Current password is incorrect.",
            "errors": ["Current password is incorrect."],
        }

    secret = _build_totp_secret()
    bookkeeper.two_factor_secret = secret
    bookkeeper.two_factor_enabled = False
    bookkeeper.two_factor_confirmed_at = None
    bookkeeper.save(update_fields=["two_factor_secret", "two_factor_enabled", "two_factor_confirmed_at"])

    account_label = _normalize_text(bookkeeper.email) or _normalize_text(bookkeeper.username) or "SafeBooks"
    provisioning_uri = _build_provisioning_uri(secret, account_label)

    return {
        "ok": True,
        "message": "Two-factor setup key generated.",
        "secret": secret,
        "otpauth_uri": provisioning_uri,
    }


def enable_two_factor(bookkeeper, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    current_password = str(payload.get("current_password", ""))
    code = payload.get("code") or payload.get("token") or payload.get("otp")

    if not current_password:
        return {
            "ok": False,
            "message": "Current password is required.",
            "errors": ["Current password is required."],
        }

    if not _verify_current_password(bookkeeper, current_password):
        return {
            "ok": False,
            "message": "Current password is incorrect.",
            "errors": ["Current password is incorrect."],
        }

    if not bookkeeper.two_factor_secret:
        return {
            "ok": False,
            "message": "Generate a setup key before enabling two-factor authentication.",
            "errors": ["Two-factor setup key is missing."],
        }

    if not code:
        return {
            "ok": False,
            "message": "Authenticator code is required.",
            "errors": ["Authenticator code is required."],
        }

    if not _is_two_factor_code_valid(bookkeeper.two_factor_secret, str(code)):
        return {
            "ok": False,
            "message": "Invalid authenticator code.",
            "errors": ["Invalid authenticator code."],
        }

    bookkeeper.two_factor_enabled = True
    bookkeeper.two_factor_confirmed_at = timezone.now()
    bookkeeper.save(update_fields=["two_factor_enabled", "two_factor_confirmed_at"])

    return {
        "ok": True,
        "message": "Two-factor authentication enabled.",
    }


def disable_two_factor(bookkeeper, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    current_password = str(payload.get("current_password", ""))
    code = payload.get("code") or payload.get("token") or payload.get("otp")

    if not current_password:
        return {
            "ok": False,
            "message": "Current password is required.",
            "errors": ["Current password is required."],
        }

    if not _verify_current_password(bookkeeper, current_password):
        return {
            "ok": False,
            "message": "Current password is incorrect.",
            "errors": ["Current password is incorrect."],
        }

    if bookkeeper.two_factor_enabled:
        if not code:
            return {
                "ok": False,
                "message": "Authenticator code is required to disable two-factor authentication.",
                "errors": ["Authenticator code is required."],
            }
        if not _is_two_factor_code_valid(bookkeeper.two_factor_secret, str(code)):
            return {
                "ok": False,
                "message": "Invalid authenticator code.",
                "errors": ["Invalid authenticator code."],
            }

    bookkeeper.two_factor_enabled = False
    bookkeeper.two_factor_secret = ""
    bookkeeper.two_factor_confirmed_at = None
    bookkeeper.save(update_fields=["two_factor_enabled", "two_factor_secret", "two_factor_confirmed_at"])

    return {
        "ok": True,
        "message": "Two-factor authentication disabled.",
    }


def verify_two_factor_login(bookkeeper, code: str) -> dict:
    if not bookkeeper.two_factor_enabled or not bookkeeper.two_factor_secret:
        return {
            "ok": False,
            "message": "Two-factor authentication is not enabled.",
            "errors": ["Two-factor authentication is not enabled."],
        }

    if not code:
        return {
            "ok": False,
            "message": "Authenticator code is required.",
            "errors": ["Authenticator code is required."],
        }

    if not _is_two_factor_code_valid(bookkeeper.two_factor_secret, str(code)):
        return {
            "ok": False,
            "message": "Invalid authenticator code.",
            "errors": ["Invalid authenticator code."],
        }

    return {
        "ok": True,
        "message": "Two-factor verification successful.",
    }
