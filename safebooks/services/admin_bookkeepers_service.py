from django.db.models import Count, Q
from django.db.models.functions import Lower

from safebooks.models import BookkeeperAccount


STATUS_FILTER_MAP = {
    "approved": BookkeeperAccount.STATUS_APPROVED,
    "deactivated": BookkeeperAccount.STATUS_SUSPENDED,
    "inactive": BookkeeperAccount.STATUS_REJECTED,
}

SORT_OPTIONS = {"recent", "alpha", "clients"}
CLIENT_FILTERS = {"0-15", "16+"}


def _normalize_value(value: str) -> str:
    return str(value or "").strip().lower()


def _serialize_bookkeeper(account: BookkeeperAccount, client_count: int | None = None) -> dict:
    resolved_count = client_count if client_count is not None else account.clients.count()
    return {
        "id": account.id,
        "full_name": account.full_name,
        "email": account.email,
        "username": account.username,
        "status": account.status or BookkeeperAccount.STATUS_PENDING,
        "created_at": account.created_at.isoformat() if account.created_at else "",
        "last_login": account.last_login.isoformat() if account.last_login else "",
        "client_count": resolved_count,
    }


def list_admin_bookkeepers(admin_account, status: str | None, search: str | None, sort: str | None, clients: str | None) -> dict:
    status_value = _normalize_value(status)
    search_value = str(search or "").strip()
    sort_value = _normalize_value(sort) or "recent"
    clients_value = str(clients or "").strip()

    directory_queryset = BookkeeperAccount.objects.exclude(status=BookkeeperAccount.STATUS_PENDING)
    list_queryset = directory_queryset.annotate(client_count=Count("clients", distinct=True))

    if status_value in STATUS_FILTER_MAP:
        list_queryset = list_queryset.filter(status=STATUS_FILTER_MAP[status_value])

    if search_value:
        list_queryset = list_queryset.filter(
            Q(full_name__icontains=search_value)
            | Q(email__icontains=search_value)
            | Q(username__icontains=search_value)
        )

    if clients_value in CLIENT_FILTERS:
        if clients_value == "0-15":
            list_queryset = list_queryset.filter(client_count__lte=15)
        else:
            list_queryset = list_queryset.filter(client_count__gte=16)

    if sort_value == "alpha":
        list_queryset = list_queryset.order_by(Lower("full_name"), "id")
    elif sort_value == "clients":
        list_queryset = list_queryset.order_by("-client_count", Lower("full_name"), "id")
    else:
        list_queryset = list_queryset.order_by("-created_at", "-id")

    approved_count = directory_queryset.filter(status=BookkeeperAccount.STATUS_APPROVED).count()
    deactivated_count = directory_queryset.filter(status=BookkeeperAccount.STATUS_SUSPENDED).count()
    inactive_count = directory_queryset.filter(status=BookkeeperAccount.STATUS_REJECTED).count()
    total_count = approved_count + deactivated_count + inactive_count

    client_queryset = directory_queryset.annotate(client_count=Count("clients", distinct=True))
    client_zero_to_five = client_queryset.filter(client_count__lte=5).count()
    client_six_to_fifteen = client_queryset.filter(client_count__gte=6, client_count__lte=15).count()
    client_sixteen_plus = client_queryset.filter(client_count__gte=16).count()

    bookkeepers = [
        _serialize_bookkeeper(account, getattr(account, "client_count", 0))
        for account in list_queryset
    ]

    return {
        "ok": True,
        "counts": {
            "total": total_count,
            "active": approved_count,
            "deactivated": deactivated_count,
            "inactive": inactive_count,
        },
        "client_summary": {
            "zero_to_five": client_zero_to_five,
            "six_to_fifteen": client_six_to_fifteen,
            "sixteen_plus": client_sixteen_plus,
        },
        "bookkeepers": bookkeepers,
    }


def deactivate_bookkeeper(admin_account, bookkeeper_id: int) -> dict:
    account = BookkeeperAccount.objects.filter(id=bookkeeper_id).first()
    if account is None:
        return {"ok": False, "message": "Bookkeeper not found."}

    if account.status == BookkeeperAccount.STATUS_SUSPENDED:
        return {
            "ok": True,
            "message": "Account is already deactivated.",
            "bookkeeper": _serialize_bookkeeper(account),
        }

    if account.status != BookkeeperAccount.STATUS_APPROVED:
        return {"ok": False, "message": "Only approved accounts can be deactivated."}

    account.status = BookkeeperAccount.STATUS_SUSPENDED
    account.save(update_fields=["status"])

    return {
        "ok": True,
        "message": "Account deactivated.",
        "bookkeeper": _serialize_bookkeeper(account),
    }


def reactivate_bookkeeper(admin_account, bookkeeper_id: int) -> dict:
    account = BookkeeperAccount.objects.filter(id=bookkeeper_id).first()
    if account is None:
        return {"ok": False, "message": "Bookkeeper not found."}

    if account.status == BookkeeperAccount.STATUS_APPROVED:
        return {
            "ok": True,
            "message": "Account is already active.",
            "bookkeeper": _serialize_bookkeeper(account),
        }

    if account.status != BookkeeperAccount.STATUS_SUSPENDED:
        return {"ok": False, "message": "Only deactivated accounts can be reactivated."}

    account.status = BookkeeperAccount.STATUS_APPROVED
    account.save(update_fields=["status"])

    return {
        "ok": True,
        "message": "Account reactivated.",
        "bookkeeper": _serialize_bookkeeper(account),
    }


def delete_bookkeeper_account(admin_account, bookkeeper_id: int) -> dict:
    account = BookkeeperAccount.objects.filter(id=bookkeeper_id).first()
    if account is None:
        return {"ok": False, "message": "Bookkeeper not found."}

    account.delete()
    return {
        "ok": True,
        "message": "Bookkeeper deleted.",
        "bookkeeper_id": bookkeeper_id,
    }
