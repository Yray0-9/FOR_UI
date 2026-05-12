from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from safebooks.models import Client


RISK_LEVELS = {Client.RISK_LOW, Client.RISK_MEDIUM, Client.RISK_HIGH}


def _normalize_text(value) -> str:
    return str(value or "").strip()


def _normalize_optional_date(value):
    cleaned_value = _normalize_text(value)
    if not cleaned_value:
        return None, None

    try:
        return date.fromisoformat(cleaned_value), None
    except ValueError:
        return None, "Birthday must use YYYY-MM-DD format."


def _normalize_risk_level(value) -> str:
    cleaned_value = _normalize_text(value).lower()
    if cleaned_value in RISK_LEVELS:
        return cleaned_value
    return Client.RISK_MEDIUM


def _normalize_custom_fields(value):
    if value is None:
        return None, None

    if not isinstance(value, list):
        return None, "Custom fields must be a list."

    cleaned_fields = []
    for item in value:
        if not isinstance(item, dict):
            continue

        label = _normalize_text(item.get("label"))
        field_value = _normalize_text(item.get("value"))

        if not label and not field_value:
            continue

        cleaned_fields.append({
            "label": label or "Custom Field",
            "value": field_value,
        })

    return cleaned_fields, None


def _serialize_client(client: Client) -> dict:
    return {
        "id": client.id,
        "client_name": client.client_name,
        "tin_number": client.tin_number,
        "trade_name": client.trade_name,
        "location": client.location,
        "permit_number": client.permit_number,
        "birthday": client.birthday.isoformat() if client.birthday else "",
        "email": client.email,
        "custom_fields": client.custom_fields or [],
        "risk_level": client.risk_level,
        "date_registered": client.date_registered.isoformat() if client.date_registered else "",
        "created_at": client.created_at.isoformat() if client.created_at else "",
        "updated_at": client.updated_at.isoformat() if client.updated_at else "",
    }


def _build_clean_payload(data: dict):
    client_name = _normalize_text(data.get("client_name"))
    tin_number = _normalize_text(data.get("tin_number") or data.get("tin"))
    trade_name = _normalize_text(data.get("trade_name"))
    location = _normalize_text(data.get("location"))
    permit_number = _normalize_text(data.get("permit_number"))
    email = _normalize_text(data.get("email"))
    risk_level = _normalize_risk_level(data.get("risk_level") or data.get("risk"))

    custom_fields, custom_fields_error = _normalize_custom_fields(data.get("custom_fields"))

    birthday_value, birthday_error = _normalize_optional_date(data.get("birthday"))

    errors: list[str] = []

    if not client_name:
        errors.append("Client name is required.")
    if not tin_number:
        errors.append("TIN is required.")
    if not location:
        errors.append("Location is required.")
    if birthday_error:
        errors.append(birthday_error)

    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Email format is invalid.")

    if custom_fields_error:
        errors.append(custom_fields_error)

    return {
        "client_name": client_name,
        "tin_number": tin_number,
        "trade_name": trade_name,
        "location": location,
        "permit_number": permit_number,
        "birthday": birthday_value,
        "email": email,
        "custom_fields": custom_fields,
        "risk_level": risk_level,
    }, errors


def list_clients_for_bookkeeper(bookkeeper) -> dict:
    clients = Client.objects.filter(bookkeeper=bookkeeper).order_by("client_name", "id")
    return {
        "ok": True,
        "clients": [_serialize_client(client) for client in clients],
    }


def create_client_for_bookkeeper(bookkeeper, data: dict) -> dict:
    payload, errors = _build_clean_payload(data)

    if errors:
        return {
            "ok": False,
            "message": errors[0],
            "errors": errors,
        }

    if Client.objects.filter(tin_number__iexact=payload["tin_number"]).exists():
        return {
            "ok": False,
            "message": "TIN already exists.",
            "errors": ["TIN already exists."],
        }

    client = Client.objects.create(
        bookkeeper=bookkeeper,
        client_name=payload["client_name"],
        tin_number=payload["tin_number"],
        trade_name=payload["trade_name"],
        location=payload["location"],
        permit_number=payload["permit_number"],
        birthday=payload["birthday"],
        email=payload["email"],
        custom_fields=payload["custom_fields"] or [],
        risk_level=payload["risk_level"],
    )

    return {
        "ok": True,
        "message": "Client added successfully.",
        "client": _serialize_client(client),
    }


def update_client_for_bookkeeper(bookkeeper, client_id: int, data: dict) -> dict:
    client = Client.objects.filter(id=client_id, bookkeeper=bookkeeper).first()
    if client is None:
        return {
            "ok": False,
            "message": "Client not found.",
            "errors": ["Client not found."],
        }

    payload, errors = _build_clean_payload(data)

    if errors:
        return {
            "ok": False,
            "message": errors[0],
            "errors": errors,
        }

    if Client.objects.filter(tin_number__iexact=payload["tin_number"]).exclude(id=client.id).exists():
        return {
            "ok": False,
            "message": "TIN already exists.",
            "errors": ["TIN already exists."],
        }

    client.client_name = payload["client_name"]
    client.tin_number = payload["tin_number"]
    client.trade_name = payload["trade_name"]
    client.location = payload["location"]
    client.permit_number = payload["permit_number"]
    client.birthday = payload["birthday"]
    client.email = payload["email"]
    client.risk_level = payload["risk_level"]
    update_fields = [
        "client_name",
        "tin_number",
        "trade_name",
        "location",
        "permit_number",
        "birthday",
        "email",
        "risk_level",
        "updated_at",
    ]

    if payload["custom_fields"] is not None:
        client.custom_fields = payload["custom_fields"]
        update_fields.append("custom_fields")

    client.save(update_fields=update_fields)

    return {
        "ok": True,
        "message": "Client updated successfully.",
        "client": _serialize_client(client),
    }


def delete_client_for_bookkeeper(bookkeeper, client_id: int) -> dict:
    client = Client.objects.filter(id=client_id, bookkeeper=bookkeeper).first()
    if client is None:
        return {
            "ok": False,
            "message": "Client not found.",
            "errors": ["Client not found."],
        }

    deleted_client = {
        "id": client.id,
        "client_name": client.client_name,
    }
    client.delete()

    return {
        "ok": True,
        "message": "Client deleted successfully.",
        "client": deleted_client,
    }
