from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import Lower
from django.utils import timezone

from safebooks.models import BookkeeperAccount, BookkeeperDeactivationRequest


HIGH_LOAD_THRESHOLD = 150
REVIEW_LIST_LIMIT = 4


def _serialize_load_snapshot(account: BookkeeperAccount, client_count: int) -> dict:
    return {
        "id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "status": account.status or BookkeeperAccount.STATUS_PENDING,
        "client_count": client_count,
    }


def _serialize_review_account(account: BookkeeperAccount, client_count: int | None = None) -> dict:
    created_at = account.created_at
    waiting_days = 0
    if created_at:
        waiting_days = max((timezone.localdate() - timezone.localtime(created_at).date()).days, 0)

    return {
        "id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "status": account.status or BookkeeperAccount.STATUS_PENDING,
        "created_at": created_at.isoformat() if created_at else "",
        "last_login": account.last_login.isoformat() if account.last_login else "",
        "waiting_days": waiting_days,
        "client_count": client_count if client_count is not None else None,
    }


def _serialize_deactivation_request(request_obj: BookkeeperDeactivationRequest) -> dict:
    account = request_obj.bookkeeper
    requested_at = request_obj.requested_at
    waiting_days = 0
    if requested_at:
        waiting_days = max((timezone.localdate() - timezone.localtime(requested_at).date()).days, 0)

    return {
        "id": request_obj.id,
        "bookkeeper_id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "requested_at": requested_at.isoformat() if requested_at else "",
        "waiting_days": waiting_days,
        "client_count": getattr(request_obj, "client_count", 0),
    }


def get_admin_dashboard_summary(admin_account) -> dict:
    now = timezone.now()
    pending_cutoff = now - timedelta(days=1)
    week_cutoff = now - timedelta(days=7)

    pending_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_PENDING)
    approved_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_APPROVED)
    deactivated_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_SUSPENDED)
    rejected_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_REJECTED)

    total_bookkeepers = BookkeeperAccount.objects.count()
    pending_count = pending_qs.count()
    active_count = approved_qs.count()

    directory_qs = BookkeeperAccount.objects.exclude(status=BookkeeperAccount.STATUS_PENDING)
    load_queryset = directory_qs.annotate(client_count=Count("clients", distinct=True))
    active_load_queryset = approved_qs.annotate(client_count=Count("clients", distinct=True))
    high_load_count = active_load_queryset.filter(client_count__gte=HIGH_LOAD_THRESHOLD).count()

    load_snapshot = [
        _serialize_load_snapshot(account, account.client_count)
        for account in load_queryset.order_by("-client_count", Lower("full_name"), "id")[:5]
    ]

    approval_readiness = {
        "new": pending_qs.filter(created_at__gte=pending_cutoff).count(),
        "waiting": pending_qs.filter(created_at__lt=pending_cutoff, created_at__gte=week_cutoff).count(),
        "overdue": pending_qs.filter(created_at__lt=week_cutoff).count(),
    }

    pending_review = [
        _serialize_review_account(account)
        for account in pending_qs.order_by("created_at", "id")[:REVIEW_LIST_LIMIT]
    ]

    deactivation_request_qs = (
        BookkeeperDeactivationRequest.objects
        .filter(
            status=BookkeeperDeactivationRequest.STATUS_PENDING,
            bookkeeper__status=BookkeeperAccount.STATUS_APPROVED,
        )
        .select_related("bookkeeper")
        .annotate(client_count=Count("bookkeeper__clients", distinct=True))
    )
    deactivation_request_count = deactivation_request_qs.count()
    deactivation_requests = [
        _serialize_deactivation_request(request_obj)
        for request_obj in deactivation_request_qs.order_by("requested_at", "id")[:REVIEW_LIST_LIMIT]
    ]

    return {
        "ok": True,
        "kpis": {
            "total_bookkeepers": total_bookkeepers,
            "pending_approvals": pending_count,
            "active_accounts": active_count,
            "high_client_load": high_load_count,
            "high_load_threshold": HIGH_LOAD_THRESHOLD,
        },
        "status_overview": {
            "pending": pending_count,
            "approved": active_count,
            "deactivated": deactivated_qs.count(),
            "rejected": rejected_qs.count(),
        },
        "approval_readiness": approval_readiness,
        "load_snapshot": load_snapshot,
        "needs_review": {
            "pending_approvals": pending_review,
            "deactivation_requests": deactivation_requests,
            "total_attention": pending_count + deactivation_request_count,
        },
    }
