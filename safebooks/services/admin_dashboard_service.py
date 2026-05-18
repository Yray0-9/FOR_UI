from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import Lower
from django.utils import timezone

from safebooks.models import BookkeeperAccount


HIGH_LOAD_THRESHOLD = 150


def _serialize_load_snapshot(account: BookkeeperAccount, client_count: int) -> dict:
    return {
        "id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "status": account.status or BookkeeperAccount.STATUS_PENDING,
        "client_count": client_count,
    }


def get_admin_dashboard_summary(admin_account) -> dict:
    now = timezone.now()
    pending_cutoff = now - timedelta(days=1)
    week_cutoff = now - timedelta(days=7)

    pending_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_PENDING)
    approved_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_APPROVED)
    deactivated_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_SUSPENDED)
    inactive_qs = BookkeeperAccount.objects.filter(status=BookkeeperAccount.STATUS_REJECTED)

    total_bookkeepers = approved_qs.count() + deactivated_qs.count() + inactive_qs.count()
    pending_count = pending_qs.count()
    active_count = approved_qs.count()

    directory_qs = BookkeeperAccount.objects.exclude(status=BookkeeperAccount.STATUS_PENDING)
    load_queryset = directory_qs.annotate(client_count=Count("clients", distinct=True))
    high_load_count = load_queryset.filter(client_count__gte=HIGH_LOAD_THRESHOLD).count()

    load_snapshot = [
        _serialize_load_snapshot(account, account.client_count)
        for account in load_queryset.order_by("-client_count", Lower("full_name"), "id")[:5]
    ]

    approval_readiness = {
        "new": pending_qs.filter(created_at__gte=pending_cutoff).count(),
        "waiting": pending_qs.filter(created_at__lt=pending_cutoff, created_at__gte=week_cutoff).count(),
        "overdue": pending_qs.filter(created_at__lt=week_cutoff).count(),
    }

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
            "inactive": inactive_qs.count(),
        },
        "approval_readiness": approval_readiness,
        "load_snapshot": load_snapshot,
    }
