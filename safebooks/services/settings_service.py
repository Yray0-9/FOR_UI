from safebooks.models import Client
from safebooks.models.workspace_defaults_model import WorkspaceDefaults


DEFAULT_CLIENT_SCOPES = {
    WorkspaceDefaults.SCOPE_ALL,
    WorkspaceDefaults.SCOPE_LAST,
}
DEFAULT_REPORT_TYPES = {
    WorkspaceDefaults.REPORT_TYPE_FINANCIAL,
    WorkspaceDefaults.REPORT_TYPE_COMPLIANCE,
    WorkspaceDefaults.REPORT_TYPE_RISK,
}
DEFAULT_REPORT_RANGES = {
    WorkspaceDefaults.REPORT_RANGE_YTD,
    WorkspaceDefaults.REPORT_RANGE_30,
    WorkspaceDefaults.REPORT_RANGE_90,
    WorkspaceDefaults.REPORT_RANGE_CUSTOM,
}


def _normalize_text(value) -> str:
    return str(value or "").strip()


def _serialize_defaults(defaults: WorkspaceDefaults) -> dict:
    return {
        "default_client_scope": defaults.default_client_scope,
        "default_report_type": defaults.default_report_type,
        "default_report_range": defaults.default_report_range,
        "last_client_id": defaults.last_client_id,
    }


def get_workspace_defaults_for_bookkeeper(bookkeeper) -> dict:
    defaults, _ = WorkspaceDefaults.objects.get_or_create(bookkeeper=bookkeeper)
    return {
        "ok": True,
        "defaults": _serialize_defaults(defaults),
    }


def _normalize_last_client_id(value):
    if value in (None, "", "all", "null"):
        return None, None

    raw_value = _normalize_text(value)
    if not raw_value.isdigit():
        return None, "Last used client must be a valid id."

    client_id = int(raw_value)
    if client_id <= 0:
        return None, "Last used client must be a valid id."

    return client_id, None


def update_workspace_defaults_for_bookkeeper(bookkeeper, data: dict) -> dict:
    if not isinstance(data, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    defaults, _ = WorkspaceDefaults.objects.get_or_create(bookkeeper=bookkeeper)

    errors: list[str] = []
    update_fields: list[str] = []

    if "default_client_scope" in data:
        scope = _normalize_text(data.get("default_client_scope")).lower()
        if scope not in DEFAULT_CLIENT_SCOPES:
            errors.append("Default client scope is invalid.")
        else:
            defaults.default_client_scope = scope
            update_fields.append("default_client_scope")

    if "default_report_type" in data:
        report_type = _normalize_text(data.get("default_report_type"))
        if report_type not in DEFAULT_REPORT_TYPES:
            errors.append("Default report type is invalid.")
        else:
            defaults.default_report_type = report_type
            update_fields.append("default_report_type")

    if "default_report_range" in data:
        report_range = _normalize_text(data.get("default_report_range"))
        if report_range not in DEFAULT_REPORT_RANGES:
            errors.append("Default report date range is invalid.")
        else:
            defaults.default_report_range = report_range
            update_fields.append("default_report_range")

    if "last_client_id" in data:
        last_client_id, last_client_error = _normalize_last_client_id(data.get("last_client_id"))
        if last_client_error:
            errors.append(last_client_error)
        else:
            if last_client_id is None:
                defaults.last_client = None
                update_fields.append("last_client")
            else:
                client = Client.objects.filter(id=last_client_id, bookkeeper=bookkeeper).first()
                if client is None:
                    errors.append("Last used client was not found.")
                else:
                    defaults.last_client = client
                    update_fields.append("last_client")

    if errors:
        return {
            "ok": False,
            "message": errors[0],
            "errors": errors,
        }

    if update_fields:
        update_fields.append("updated_at")
        defaults.save(update_fields=update_fields)

    return {
        "ok": True,
        "message": "Workspace defaults updated.",
        "defaults": _serialize_defaults(defaults),
    }
