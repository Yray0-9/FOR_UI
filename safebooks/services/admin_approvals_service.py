from django.db.models import Q
from django.utils import timezone

from safebooks.models import BookkeeperAccount


VALID_APPROVAL_STATUSES = {
    BookkeeperAccount.STATUS_PENDING,
    BookkeeperAccount.STATUS_APPROVED,
    BookkeeperAccount.STATUS_REJECTED,
}


def _normalize_status(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized


def _serialize_approval(account: BookkeeperAccount) -> dict:
    return {
        "id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "username": account.username,
        "status": account.status or BookkeeperAccount.STATUS_PENDING,
        "created_at": account.created_at.isoformat() if account.created_at else "",
        "approved_at": account.approved_at.isoformat() if account.approved_at else "",
        "rejected_at": account.rejected_at.isoformat() if account.rejected_at else "",
        "last_login": account.last_login.isoformat() if account.last_login else "",
    }


def list_admin_approvals(admin_account, status: str | None, search: str | None, sort: str | None) -> dict:
    status_value = _normalize_status(status)
    search_value = str(search or "").strip()
    sort_value = _normalize_status(sort) or "newest"

    queryset = BookkeeperAccount.objects.all()

    if status_value in VALID_APPROVAL_STATUSES:
        queryset = queryset.filter(status=status_value)
    else:
        queryset = queryset.filter(status__in=VALID_APPROVAL_STATUSES)

    if search_value:
        queryset = queryset.filter(
            Q(full_name__icontains=search_value)
            | Q(email__icontains=search_value)
            | Q(username__icontains=search_value)
        )

    if sort_value == "oldest":
        queryset = queryset.order_by("created_at", "id")
    elif sort_value == "status":
        queryset = queryset.order_by("status", "-created_at", "-id")
    else:
        queryset = queryset.order_by("-created_at", "-id")

    pending_count = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_PENDING).count()
    approved_count = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_APPROVED).count()
    rejected_count = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_REJECTED).count()
    today = timezone.localdate()
    approved_today = BookkeeperAccount.objects.filter(
        status=BookkeeperAccount.STATUS_APPROVED,
        approved_at__date=today,
    ).count()
    rejected_today = BookkeeperAccount.objects.filter(
        status=BookkeeperAccount.STATUS_REJECTED,
        rejected_at__date=today,
    ).count()

    approvals = [_serialize_approval(account) for account in queryset]

    return {
        "ok": True,
        "counts": {
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "approved_today": approved_today,
            "rejected_today": rejected_today,
        },
        "total_count": pending_count + approved_count + rejected_count,
        "approvals": approvals,
    }


def approve_bookkeeper(admin_account, bookkeeper_id: int) -> dict:
    account = BookkeeperAccount.objects.filter(id=bookkeeper_id).first()
    if account is None:
        return {
            "ok": False,
            "message": "Bookkeeper not found.",
        }

    if account.status == BookkeeperAccount.STATUS_APPROVED:
        return {
            "ok": True,
            "message": "Account already approved.",
            "approval": _serialize_approval(account),
        }

    if account.status not in {BookkeeperAccount.STATUS_PENDING, BookkeeperAccount.STATUS_REJECTED}:
        return {
            "ok": False,
            "message": "Approval action is not allowed for this account.",
        }

    account.status = BookkeeperAccount.STATUS_APPROVED
    account.approved_at = timezone.now()
    account.approved_by_admin = admin_account
    account.rejected_at = None
    account.rejection_reason = ""
    account.save(update_fields=[
        "status",
        "approved_at",
        "approved_by_admin",
        "rejected_at",
        "rejection_reason",
    ])

    return {
        "ok": True,
        "message": "Account approved.",
        "approval": _serialize_approval(account),
    }


def reject_bookkeeper(admin_account, bookkeeper_id: int, rejection_reason: str | None = None) -> dict:
    account = BookkeeperAccount.objects.filter(id=bookkeeper_id).first()
    if account is None:
        return {
            "ok": False,
            "message": "Bookkeeper not found.",
        }

    if account.status == BookkeeperAccount.STATUS_REJECTED:
        return {
            "ok": True,
            "message": "Account already rejected.",
            "approval": _serialize_approval(account),
        }

    if account.status != BookkeeperAccount.STATUS_PENDING:
        return {
            "ok": False,
            "message": "Rejection is only available for pending accounts.",
        }

    clean_reason = str(rejection_reason or "").strip()

    account.status = BookkeeperAccount.STATUS_REJECTED
    account.rejected_at = timezone.now()
    account.rejection_reason = clean_reason
    account.approved_at = None
    account.approved_by_admin = None
    account.save(update_fields=[
        "status",
        "rejected_at",
        "rejection_reason",
        "approved_at",
        "approved_by_admin",
    ])

    return {
        "ok": True,
        "message": "Account rejected.",
        "approval": _serialize_approval(account),
    }
