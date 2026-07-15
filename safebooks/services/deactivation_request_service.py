from django.db import transaction

from safebooks.models import AdminAuditLog, BookkeeperAccount, BookkeeperAuditLog, BookkeeperDeactivationRequest
from safebooks.services.security_service import _verify_current_password


def _normalize_text(value) -> str:
    return str(value or "").strip()


def _serialize_request(request_obj: BookkeeperDeactivationRequest | None) -> dict | None:
    if request_obj is None:
        return None

    return {
        "id": request_obj.id,
        "bookkeeper_id": request_obj.bookkeeper_id,
        "reason": request_obj.reason,
        "status": request_obj.status,
        "requested_at": request_obj.requested_at.isoformat() if request_obj.requested_at else "",
        "reviewed_at": request_obj.reviewed_at.isoformat() if request_obj.reviewed_at else "",
        "admin_note": request_obj.admin_note,
    }


def get_pending_deactivation_request(bookkeeper: BookkeeperAccount) -> BookkeeperDeactivationRequest | None:
    return (
        BookkeeperDeactivationRequest.objects
        .filter(bookkeeper=bookkeeper, status=BookkeeperDeactivationRequest.STATUS_PENDING)
        .order_by("-requested_at", "-id")
        .first()
    )


def get_deactivation_request_status(bookkeeper: BookkeeperAccount) -> dict:
    pending_request = get_pending_deactivation_request(bookkeeper)
    latest_request = (
        BookkeeperDeactivationRequest.objects
        .filter(bookkeeper=bookkeeper)
        .order_by("-requested_at", "-id")
        .first()
    )
    return {
        "ok": True,
        "pending_request": _serialize_request(pending_request),
        "latest_request": _serialize_request(latest_request),
    }


def request_bookkeeper_deactivation(bookkeeper: BookkeeperAccount, payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Invalid request payload.",
            "errors": ["Invalid request payload."],
        }

    if bookkeeper.status != BookkeeperAccount.STATUS_APPROVED:
        return {
            "ok": False,
            "message": "Only active approved accounts can request deactivation.",
            "errors": ["Only active approved accounts can request deactivation."],
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

    existing_request = get_pending_deactivation_request(bookkeeper)
    if existing_request is not None:
        return {
            "ok": True,
            "message": "A deactivation request is already waiting for admin review.",
            "request": _serialize_request(existing_request),
        }

    reason = _normalize_text(payload.get("reason"))[:255]

    with transaction.atomic():
        request_obj = BookkeeperDeactivationRequest.objects.create(
            bookkeeper=bookkeeper,
            reason=reason,
        )
        AdminAuditLog.objects.create(
            admin=None,
            action_type=AdminAuditLog.ACTION_BOOKKEEPER_DEACTIVATION_REQUESTED,
            target_model="BookkeeperAccount",
            target_id=bookkeeper.id,
            message=f"{bookkeeper.full_name} requested account deactivation.",
            metadata={
                "bookkeeper_id": bookkeeper.id,
                "bookkeeper_name": bookkeeper.full_name,
                "bookkeeper_email": bookkeeper.email,
                "request_id": request_obj.id,
                "reason": reason,
                "status": request_obj.status,
            },
        )
        BookkeeperAuditLog.objects.create(
            bookkeeper=bookkeeper,
            action_type=BookkeeperAuditLog.ACTION_DEACTIVATION_REQUESTED,
            target_model="BookkeeperAccount",
            target_id=bookkeeper.id,
            message="Requested account deactivation for admin review.",
            metadata={"request_id": request_obj.id},
        )

    return {
        "ok": True,
        "message": "Deactivation request submitted. An admin will review it before access changes.",
        "request": _serialize_request(request_obj),
    }
