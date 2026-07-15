from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date

from safebooks.models import AdminAuditLog


ACTION_LABELS = {
    AdminAuditLog.ACTION_BOOKKEEPER_APPROVED: "Approved bookkeeper",
    AdminAuditLog.ACTION_BOOKKEEPER_REJECTED: "Rejected bookkeeper",
    AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATED: "Deactivated bookkeeper",
    AdminAuditLog.ACTION_BOOKKEEPER_REACTIVATED: "Reactivated bookkeeper",
    AdminAuditLog.ACTION_BOOKKEEPER_DELETED: "Deleted bookkeeper",
    AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATION_REQUESTED: "Requested deactivation",
    AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATION_DECLINED: "Declined deactivation request",
    AdminAuditLog.ACTION_ADMIN_PROFILE_UPDATED: "Updated admin profile",
    AdminAuditLog.ACTION_ADMIN_PASSWORD_CHANGED: "Changed admin password",
    AdminAuditLog.ACTION_ADMIN_LOGIN: "Signed in",
    AdminAuditLog.ACTION_ADMIN_LOGOUT: "Signed out",
    AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_ENABLED: "Enabled admin 2FA",
    AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_DISABLED: "Disabled admin 2FA",
    AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_RECOVERY_CODES_REGENERATED: "Replaced admin recovery codes",
}

ACTION_GROUPS = {
    "approvals": {
        AdminAuditLog.ACTION_BOOKKEEPER_APPROVED,
        AdminAuditLog.ACTION_BOOKKEEPER_REJECTED,
    },
    "access": {
        AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATED,
        AdminAuditLog.ACTION_BOOKKEEPER_REACTIVATED,
        AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATION_REQUESTED,
        AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATION_DECLINED,
    },
    "danger": {
        AdminAuditLog.ACTION_BOOKKEEPER_DELETED,
    },
    "security": {
        AdminAuditLog.ACTION_ADMIN_PROFILE_UPDATED,
        AdminAuditLog.ACTION_ADMIN_PASSWORD_CHANGED,
        AdminAuditLog.ACTION_ADMIN_LOGIN,
        AdminAuditLog.ACTION_ADMIN_LOGOUT,
        AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_ENABLED,
        AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_DISABLED,
        AdminAuditLog.ACTION_ADMIN_TWO_FACTOR_RECOVERY_CODES_REGENERATED,
    },
}

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def _normalize_value(value: str) -> str:
    return str(value or "").strip().lower()


def _serialize_audit_log(log: AdminAuditLog) -> dict:
    metadata = log.metadata if isinstance(log.metadata, dict) else {}
    email_delivery = metadata.get("email_delivery")
    if not isinstance(email_delivery, dict):
        email_delivery = {}
    admin = log.admin
    target_name = (
        str(metadata.get("bookkeeper_name") or "").strip()
        or str(metadata.get("target_name") or "").strip()
        or "-"
    )
    target_email = (
        str(metadata.get("bookkeeper_email") or "").strip()
        or str(metadata.get("target_email") or "").strip()
        or ""
    )

    return {
        "id": log.id,
        "action_type": log.action_type,
        "action_label": ACTION_LABELS.get(log.action_type, log.action_type.replace(".", " ").title()),
        "admin_name": admin.full_name if admin else "System",
        "admin_email": admin.email if admin else "",
        "target_model": log.target_model,
        "target_id": log.target_id,
        "target_name": target_name,
        "target_email": target_email,
        "message": log.message,
        "created_at": log.created_at.isoformat() if log.created_at else "",
        "metadata": {
            "status": metadata.get("status", ""),
            "client_count": metadata.get("client_count", ""),
            "decision_note": (
                metadata.get("decision_note")
                or metadata.get("rejection_reason")
                or metadata.get("admin_note")
                or metadata.get("reason")
                or ""
            ),
            "email_delivery": {
                "status": email_delivery.get("status", ""),
                "reason": email_delivery.get("reason", ""),
                "attempted_at": email_delivery.get("attempted_at", ""),
                "retry_count": email_delivery.get("retry_count", 0),
            },
        },
    }


def record_admin_auth_event(
    admin_account,
    action_type: str,
    *,
    authentication_method: str = "password",
) -> AdminAuditLog | None:
    if action_type not in {
        AdminAuditLog.ACTION_ADMIN_LOGIN,
        AdminAuditLog.ACTION_ADMIN_LOGOUT,
    }:
        return None

    action_word = "Signed in" if action_type == AdminAuditLog.ACTION_ADMIN_LOGIN else "Signed out"
    return AdminAuditLog.objects.create(
        admin=admin_account,
        action_type=action_type,
        target_model="AdminAccount",
        target_id=admin_account.id,
        message=f"{action_word} to the SafeBooks admin console.",
        metadata={
            "target_name": admin_account.full_name,
            "target_email": admin_account.email,
            "authentication_method": authentication_method,
        },
    )


def _apply_action_filter(queryset, action_filter: str):
    normalized = _normalize_value(action_filter)
    if not normalized or normalized == "all":
        return queryset

    if normalized in ACTION_GROUPS:
        return queryset.filter(action_type__in=ACTION_GROUPS[normalized])

    valid_actions = set(ACTION_LABELS)
    if normalized in valid_actions:
        return queryset.filter(action_type=normalized)

    return queryset


def _normalize_positive_int(value, default: int, maximum: int | None = None) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return default
    if normalized < 1:
        return default
    return min(normalized, maximum) if maximum else normalized


def list_admin_audit_logs(
    admin_account,
    action: str | None,
    search: str | None,
    sort: str | None,
    date_from: str | None = None,
    date_to: str | None = None,
    page=None,
    page_size=None,
) -> dict:
    search_value = str(search or "").strip()
    sort_value = _normalize_value(sort) or "newest"
    date_from_value = str(date_from or "").strip()
    date_to_value = str(date_to or "").strip()
    parsed_date_from = parse_date(date_from_value) if date_from_value else None
    parsed_date_to = parse_date(date_to_value) if date_to_value else None

    if date_from_value and parsed_date_from is None:
        return {"ok": False, "message": "Date from must be a valid date."}
    if date_to_value and parsed_date_to is None:
        return {"ok": False, "message": "Date to must be a valid date."}
    if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
        return {"ok": False, "message": "Date from cannot be after date to."}

    queryset = AdminAuditLog.objects.select_related("admin")
    queryset = _apply_action_filter(queryset, action or "")

    if search_value:
        queryset = queryset.filter(
            Q(message__icontains=search_value)
            | Q(action_type__icontains=search_value)
            | Q(target_model__icontains=search_value)
            | Q(admin__full_name__icontains=search_value)
            | Q(admin__email__icontains=search_value)
        )

    if parsed_date_from:
        queryset = queryset.filter(created_at__date__gte=parsed_date_from)
    if parsed_date_to:
        queryset = queryset.filter(created_at__date__lte=parsed_date_to)

    if sort_value == "oldest":
        queryset = queryset.order_by("created_at", "id")
    else:
        queryset = queryset.order_by("-created_at", "-id")

    resolved_page_size = _normalize_positive_int(page_size, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)
    paginator = Paginator(queryset, resolved_page_size)
    page_obj = paginator.get_page(_normalize_positive_int(page, 1))
    logs = list(page_obj.object_list)
    total_count = paginator.count

    return {
        "ok": True,
        "total_count": total_count,
        "shown_count": len(logs),
        "page": page_obj.number,
        "page_size": resolved_page_size,
        "total_pages": paginator.num_pages,
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "counts": {
            "all": AdminAuditLog.objects.count(),
            "approvals": AdminAuditLog.objects.filter(action_type__in=ACTION_GROUPS["approvals"]).count(),
            "access": AdminAuditLog.objects.filter(action_type__in=ACTION_GROUPS["access"]).count(),
            "danger": AdminAuditLog.objects.filter(action_type__in=ACTION_GROUPS["danger"]).count(),
            "security": AdminAuditLog.objects.filter(action_type__in=ACTION_GROUPS["security"]).count(),
        },
        "logs": [_serialize_audit_log(log) for log in logs],
    }
