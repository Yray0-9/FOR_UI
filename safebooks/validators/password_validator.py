import re


def password_requirement_status(password: str) -> dict[str, bool]:
    current_password = password or ""
    return {
        "length": len(current_password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", current_password)),
        "lowercase": bool(re.search(r"[a-z]", current_password)),
        "number": bool(re.search(r"\d", current_password)),
        "symbol": bool(re.search(r"[^A-Za-z0-9]", current_password)),
    }


def missing_password_requirements(password: str) -> list[str]:
    status = password_requirement_status(password)
    missing_rules: list[str] = []

    if not status["length"]:
        missing_rules.append("At least 8 characters")
    if not status["uppercase"]:
        missing_rules.append("At least one uppercase letter")
    if not status["lowercase"]:
        missing_rules.append("At least one lowercase letter")
    if not status["number"]:
        missing_rules.append("At least one number")
    if not status["symbol"]:
        missing_rules.append("At least one symbol")

    return missing_rules
