import json
from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from safebooks.models import AdminAccount, BookkeeperAccount
from safebooks.services.auth_service import (
    login_user_or_admin,
    register_user,
    send_email_verification_code,
    verify_email_code,
)
from safebooks.services.client_service import (
    create_client_for_bookkeeper,
    delete_client_for_bookkeeper,
    list_clients_for_bookkeeper,
    update_client_for_bookkeeper,
)
from safebooks.services.financial_record_service import (
    create_record_for_client_period,
    delete_record_for_client,
    list_financial_clients_for_bookkeeper,
    list_records_for_client_period,
    list_transactions_for_client_range,
    update_record_for_client_period,
)
from safebooks.services.dashboard_service import get_dashboard_summary_for_bookkeeper
from safebooks.services.analytics_service import get_analytics_summary_for_bookkeeper
from safebooks.services.settings_service import (
    get_workspace_defaults_for_bookkeeper,
    update_workspace_defaults_for_bookkeeper,
)
from safebooks.services.admin_approvals_service import (
    approve_bookkeeper,
    reject_bookkeeper,
    list_admin_approvals,
)
from safebooks.services.admin_bookkeepers_service import (
    list_admin_bookkeepers,
    deactivate_bookkeeper,
    reactivate_bookkeeper,
    delete_bookkeeper_account,
)
from safebooks.services.admin_dashboard_service import get_admin_dashboard_summary


SESSION_BOOKKEEPER_ID_KEY = "safebooks_bookkeeper_id"
SESSION_ADMIN_ID_KEY = "safebooks_admin_id"


def _decode_request_data(request):
    content_type = (request.content_type or "").lower()

    if "application/json" not in content_type:
        if request.POST:
            return request.POST.dict()
        return None

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def _is_api_request(request):
    path = request.path or ""
    accepts_header = (request.headers.get("Accept") or "").lower()
    requested_with = request.headers.get("X-Requested-With") or ""

    return (
        path.startswith("/api/")
        or "application/json" in accepts_header
        or requested_with == "XMLHttpRequest"
    )


def _get_session_bookkeeper(request):
    account_id = request.session.get(SESSION_BOOKKEEPER_ID_KEY)
    if not account_id:
        return None

    account = BookkeeperAccount.objects.filter(id=account_id).first()
    if account is None:
        request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)

    return account


def _get_session_admin(request):
    account_id = request.session.get(SESSION_ADMIN_ID_KEY)
    if not account_id:
        return None

    account = AdminAccount.objects.filter(id=account_id, is_active=True).first()
    if account is None:
        request.session.pop(SESSION_ADMIN_ID_KEY, None)

    return account


def _build_user_context(account):
    display_name = (
        (account.full_name or "").strip()
        or (account.username or "").strip()
        or (account.email or "").strip()
        or "Bookkeeper User"
    )

    name_parts = display_name.split()
    if not name_parts:
        initials = "SB"
    elif len(name_parts) == 1:
        initials = name_parts[0][:2].upper()
    else:
        initials = f"{name_parts[0][0]}{name_parts[1][0]}".upper()

    return {
        "current_user_name": display_name,
        "current_user_initials": initials,
    }


def _mask_email_address(email: str) -> str:
    normalized = str(email or "").strip()
    if not normalized or "@" not in normalized:
        return normalized

    local_part, domain = normalized.split("@", 1)
    if len(local_part) <= 2:
        masked_local = f"{local_part[:1]}*" if local_part else "*"
    else:
        masked_local = f"{local_part[0]}{'*' * (len(local_part) - 2)}{local_part[-1]}"

    return f"{masked_local}@{domain}"


def _resolve_post_login_redirect(request, payload):
    default_redirect = reverse("dashboard")
    candidate = str(payload.get("next_url", "")).strip()

    if not candidate:
        return default_redirect

    is_safe = url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )

    if not is_safe:
        return default_redirect

    return candidate


def _build_admin_context(account):
    display_name = (account.full_name or "").strip() or (account.email or "").strip() or "System Admin"

    name_parts = display_name.split()
    if not name_parts:
        initials = "SA"
    elif len(name_parts) == 1:
        initials = name_parts[0][:2].upper()
    else:
        initials = f"{name_parts[0][0]}{name_parts[1][0]}".upper()

    return {
        "current_admin_name": display_name,
        "current_admin_initials": initials,
        "current_admin_email": account.email,
        "current_admin_last_login": account.last_login,
        "current_admin_role_label": "System Manager",
    }


def require_bookkeeper_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        account = _get_session_bookkeeper(request)
        if account is None:
            admin_account = _get_session_admin(request)
            if admin_account is not None:
                if _is_api_request(request):
                    return JsonResponse(
                        {"ok": False, "message": "Bookkeeper access required."},
                        status=403,
                    )

                return redirect("admin_dashboard")

            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Authentication required."},
                    status=401,
                )

            login_url = reverse("login")
            next_path = request.get_full_path()
            if next_path and next_path != login_url:
                query = urlencode({"next": next_path})
                return redirect(f"{login_url}?{query}")

            return redirect(login_url)

        status = account.status or BookkeeperAccount.STATUS_PENDING
        pending_path = reverse("pending_approval")

        if status in {BookkeeperAccount.STATUS_REJECTED, BookkeeperAccount.STATUS_SUSPENDED}:
            request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)
            request.session.modified = True

            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Account not active."},
                    status=403,
                )

            return redirect("login")

        verify_email_path = reverse("verify_email")
        verify_api_path = reverse("api_verify_email")
        resend_api_path = reverse("api_resend_verification")
        logout_api_path = reverse("api_logout")
        allowed_unverified_paths = {
            verify_email_path,
            verify_api_path,
            resend_api_path,
            logout_api_path,
        }

        if not getattr(account, "email_verified", True):
            if request.path in allowed_unverified_paths:
                request.bookkeeper_account = account
                return view_func(request, *args, **kwargs)

            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Email verification required."},
                    status=403,
                )

            return redirect("verify_email")

        if status == BookkeeperAccount.STATUS_PENDING:
            if request.path == pending_path:
                request.bookkeeper_account = account
                return view_func(request, *args, **kwargs)

            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Approval required."},
                    status=403,
                )

            return redirect("pending_approval")

        if status == BookkeeperAccount.STATUS_APPROVED and request.path == pending_path:
            return redirect("dashboard")

        request.bookkeeper_account = account
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def require_admin_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        account = _get_session_admin(request)
        if account is None:
            bookkeeper_account = _get_session_bookkeeper(request)
            if bookkeeper_account is not None:
                if _is_api_request(request):
                    return JsonResponse(
                        {"ok": False, "message": "Admin access required."},
                        status=403,
                    )

                return redirect("dashboard")

            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Admin authentication required."},
                    status=401,
                )

            login_url = reverse("login")
            next_path = request.get_full_path()
            if next_path and next_path != login_url:
                query = urlencode({"next": next_path})
                return redirect(f"{login_url}?{query}")

            return redirect(login_url)

        request.admin_account = account
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def require_any_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        admin_account = _get_session_admin(request)
        bookkeeper_account = _get_session_bookkeeper(request)

        if admin_account is None and bookkeeper_account is None:
            if _is_api_request(request):
                return JsonResponse(
                    {"ok": False, "message": "Authentication required."},
                    status=401,
                )

            return redirect("login")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def home_page_view(request):
    if _get_session_admin(request):
        return redirect("admin_dashboard")

    bookkeeper_account = _get_session_bookkeeper(request)
    if bookkeeper_account:
        if not bookkeeper_account.email_verified:
            return redirect("verify_email")
        status = bookkeeper_account.status or BookkeeperAccount.STATUS_PENDING
        if status == BookkeeperAccount.STATUS_PENDING:
            return redirect("pending_approval")
        if status in {BookkeeperAccount.STATUS_REJECTED, BookkeeperAccount.STATUS_SUSPENDED}:
            request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)
            request.session.modified = True
            return redirect("login")
        return redirect("dashboard")

    return render(request, "authentication/landing.html")


def login_page_view(request):
    if _get_session_admin(request):
        return redirect("admin_dashboard")

    bookkeeper_account = _get_session_bookkeeper(request)
    if bookkeeper_account:
        if not bookkeeper_account.email_verified:
            return redirect("verify_email")
        status = bookkeeper_account.status or BookkeeperAccount.STATUS_PENDING
        if status == BookkeeperAccount.STATUS_PENDING:
            return redirect("pending_approval")
        if status in {BookkeeperAccount.STATUS_REJECTED, BookkeeperAccount.STATUS_SUSPENDED}:
            request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)
            request.session.modified = True
            return render(request, "authentication/login.html")
        return redirect("dashboard")

    return render(request, "authentication/login.html")


def signup_page_view(request):
    if _get_session_admin(request):
        return redirect("admin_dashboard")

    bookkeeper_account = _get_session_bookkeeper(request)
    if bookkeeper_account:
        if not bookkeeper_account.email_verified:
            return redirect("verify_email")
        status = bookkeeper_account.status or BookkeeperAccount.STATUS_PENDING
        if status == BookkeeperAccount.STATUS_PENDING:
            return redirect("pending_approval")
        if status in {BookkeeperAccount.STATUS_REJECTED, BookkeeperAccount.STATUS_SUSPENDED}:
            request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)
            request.session.modified = True
            return render(request, "authentication/signup.html")
        return redirect("dashboard")

    return render(request, "authentication/signup.html")


@require_bookkeeper_auth
@ensure_csrf_cookie
def dashboard_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "dashboard"
    return render(request, "base/dashboard.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def clients_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "clients"
    return render(request, "base/clients.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def financial_records_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "financial_records"
    return render(request, "base/financial_records.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def financial_records_client_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "financial_records"
    return render(request, "base/financial_records_client.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def analytics_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "analytics"
    return render(request, "base/analytics.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def reports_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "reports"
    return render(request, "base/reports.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def pending_approval_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = ""
    return render(request, "authentication/pending_approval.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def verify_email_page_view(request):
    account = request.bookkeeper_account
    if getattr(account, "email_verified", True):
        status = account.status or BookkeeperAccount.STATUS_PENDING
        if status == BookkeeperAccount.STATUS_PENDING:
            return redirect("pending_approval")
        if status == BookkeeperAccount.STATUS_APPROVED:
            return redirect("dashboard")

    context = _build_user_context(account)
    context["active_nav"] = ""
    context["verification_email"] = account.email
    context["verification_email_masked"] = _mask_email_address(account.email)
    context["verification_resend_cooldown_seconds"] = getattr(
        settings,
        "SAFEBOOKS_EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS",
        60,
    )
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    if settings.DEBUG and email_backend == "django.core.mail.backends.console.EmailBackend":
        context["verification_delivery_hint"] = (
            "Dev note: verification emails are printed in the server console."
        )
    return render(request, "authentication/email_verification.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def settings_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "settings"
    return render(request, "base/settings.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def profile_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    context["active_nav"] = "profile"
    return render(request, "base/profile.html", context)


@require_admin_auth
@ensure_csrf_cookie
def admin_dashboard_page_view(request):
    context = _build_admin_context(request.admin_account)
    context["active_admin_nav"] = "dashboard"
    return render(request, "admin_panel/dashboard.html", context)


@require_admin_auth
@ensure_csrf_cookie
def admin_bookkeepers_page_view(request):
    context = _build_admin_context(request.admin_account)
    context["active_admin_nav"] = "bookkeepers"
    return render(request, "admin_panel/bookkeepers.html", context)


@require_admin_auth
@ensure_csrf_cookie
def admin_approvals_page_view(request):
    context = _build_admin_context(request.admin_account)
    context["active_admin_nav"] = "approvals"
    return render(request, "admin_panel/approvals.html", context)


@require_admin_auth
@ensure_csrf_cookie
def admin_system_settings_page_view(request):
    context = _build_admin_context(request.admin_account)
    context["active_admin_nav"] = "system_settings"
    return render(request, "admin_panel/system_settings.html", context)


@require_admin_auth
@ensure_csrf_cookie
def admin_profile_page_view(request):
    context = _build_admin_context(request.admin_account)
    context["active_admin_nav"] = "profile"
    return render(request, "admin_panel/admin_profile.html", context)


def _resolve_client_error_status(result):
    message = result.get("message", "")
    if message == "Client not found.":
        return 404
    if message == "TIN already exists.":
        return 409
    return 400


def _resolve_financial_record_error_status(result):
    message = result.get("message", "")
    if message in {"Client not found.", "Financial record not found."}:
        return 404
    return 400


def _resolve_analytics_error_status(result):
    message = result.get("message", "")
    if message == "Client not found.":
        return 404
    return 400


def _resolve_admin_approval_error_status(result):
    message = result.get("message", "")
    if message == "Bookkeeper not found.":
        return 404
    return 400


def _resolve_admin_bookkeeper_error_status(result):
    message = result.get("message", "")
    if message == "Bookkeeper not found.":
        return 404
    return 400


@require_http_methods(["GET", "POST"])
@require_bookkeeper_auth
def workspace_defaults_api_view(request):
    if request.method == "GET":
        result = get_workspace_defaults_for_bookkeeper(request.bookkeeper_account)
        return JsonResponse(result)

    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = update_workspace_defaults_for_bookkeeper(request.bookkeeper_account, payload)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=400)


@require_http_methods(["GET", "POST"])
@require_bookkeeper_auth
def clients_api_view(request):
    if request.method == "GET":
        result = list_clients_for_bookkeeper(request.bookkeeper_account)
        return JsonResponse(result)

    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = create_client_for_bookkeeper(request.bookkeeper_account, payload)
    if result.get("ok"):
        return JsonResponse(result, status=201)

    return JsonResponse(result, status=_resolve_client_error_status(result))


@require_http_methods(["PUT", "PATCH", "DELETE"])
@require_bookkeeper_auth
def client_detail_api_view(request, client_id):
    if request.method == "DELETE":
        result = delete_client_for_bookkeeper(request.bookkeeper_account, client_id)
        if result.get("ok"):
            return JsonResponse(result)
        return JsonResponse(result, status=_resolve_client_error_status(result))

    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = update_client_for_bookkeeper(request.bookkeeper_account, client_id, payload)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_client_error_status(result))


@require_http_methods(["GET"])
@require_bookkeeper_auth
def financial_record_clients_api_view(request):
    result = list_financial_clients_for_bookkeeper(request.bookkeeper_account)
    return JsonResponse(result)


@require_http_methods(["GET"])
@require_bookkeeper_auth
def dashboard_summary_api_view(request):
    result = get_dashboard_summary_for_bookkeeper(request.bookkeeper_account)
    return JsonResponse(result)


@require_http_methods(["GET"])
@require_bookkeeper_auth
def analytics_summary_api_view(request):
    client_id_param = (request.GET.get("client_id") or "").strip()
    client_id = None

    if client_id_param:
        if not client_id_param.isdigit():
            return JsonResponse(
                {"ok": False, "message": "Invalid client id."},
                status=400,
            )
        client_id = int(client_id_param)

    result = get_analytics_summary_for_bookkeeper(
        request.bookkeeper_account,
        client_id=client_id,
    )
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_analytics_error_status(result))


@require_http_methods(["GET"])
@require_admin_auth
def admin_approvals_api_view(request):
    status_value = (request.GET.get("status") or "").strip()
    search_value = (request.GET.get("search") or "").strip()
    sort_value = (request.GET.get("sort") or "").strip()

    result = list_admin_approvals(
        request.admin_account,
        status_value,
        search_value,
        sort_value,
    )
    return JsonResponse(result)


@require_http_methods(["POST"])
@require_admin_auth
def admin_approvals_approve_api_view(request, bookkeeper_id):
    result = approve_bookkeeper(request.admin_account, bookkeeper_id)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_admin_approval_error_status(result))


@require_http_methods(["POST"])
@require_admin_auth
def admin_approvals_reject_api_view(request, bookkeeper_id):
    payload = _decode_request_data(request) or {}
    rejection_reason = payload.get("rejection_reason") or payload.get("reason")

    result = reject_bookkeeper(request.admin_account, bookkeeper_id, rejection_reason)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_admin_approval_error_status(result))


@require_http_methods(["GET"])
@require_admin_auth
def admin_bookkeepers_api_view(request):
    status_value = (request.GET.get("status") or "").strip()
    search_value = (request.GET.get("search") or "").strip()
    sort_value = (request.GET.get("sort") or "").strip()
    clients_value = (request.GET.get("clients") or "").strip()

    result = list_admin_bookkeepers(
        request.admin_account,
        status_value,
        search_value,
        sort_value,
        clients_value,
    )
    return JsonResponse(result)


@require_http_methods(["POST"])
@require_admin_auth
def admin_bookkeepers_deactivate_api_view(request, bookkeeper_id):
    result = deactivate_bookkeeper(request.admin_account, bookkeeper_id)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_admin_bookkeeper_error_status(result))


@require_http_methods(["POST"])
@require_admin_auth
def admin_bookkeepers_reactivate_api_view(request, bookkeeper_id):
    result = reactivate_bookkeeper(request.admin_account, bookkeeper_id)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_admin_bookkeeper_error_status(result))


@require_http_methods(["POST"])
@require_admin_auth
def admin_bookkeepers_delete_api_view(request, bookkeeper_id):
    result = delete_bookkeeper_account(request.admin_account, bookkeeper_id)
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_admin_bookkeeper_error_status(result))


@require_http_methods(["GET"])
@require_admin_auth
def admin_dashboard_summary_api_view(request):
    result = get_admin_dashboard_summary(request.admin_account)
    return JsonResponse(result)


@require_http_methods(["GET"])
@require_bookkeeper_auth
def reports_print_layout_api_view(request):
    client_id_param = (request.GET.get("client_id") or "").strip()
    if not client_id_param:
        return JsonResponse(
            {"ok": False, "message": "Client id is required."},
            status=400,
        )
    if not client_id_param.isdigit():
        return JsonResponse(
            {"ok": False, "message": "Invalid client id."},
            status=400,
        )

    result = list_transactions_for_client_range(
        request.bookkeeper_account,
        int(client_id_param),
        request.GET.get("date_from"),
        request.GET.get("date_to"),
    )
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_financial_record_error_status(result))


@require_http_methods(["GET", "POST"])
@require_bookkeeper_auth
def financial_records_api_view(request, client_id):
    if request.method == "GET":
        result = list_records_for_client_period(
            request.bookkeeper_account,
            client_id,
            request.GET.get("month"),
            request.GET.get("year"),
        )
        if result.get("ok"):
            return JsonResponse(result)
        return JsonResponse(result, status=_resolve_financial_record_error_status(result))

    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = create_record_for_client_period(request.bookkeeper_account, client_id, payload)
    if result.get("ok"):
        return JsonResponse(result, status=201)

    return JsonResponse(result, status=_resolve_financial_record_error_status(result))


@require_http_methods(["PUT", "PATCH", "DELETE"])
@require_bookkeeper_auth
def financial_record_detail_api_view(request, client_id, record_id):
    if request.method == "DELETE":
        result = delete_record_for_client(request.bookkeeper_account, client_id, record_id)
        if result.get("ok"):
            return JsonResponse(result)
        return JsonResponse(result, status=_resolve_financial_record_error_status(result))

    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = update_record_for_client_period(
        request.bookkeeper_account,
        client_id,
        record_id,
        payload,
    )
    if result.get("ok"):
        return JsonResponse(result)

    return JsonResponse(result, status=_resolve_financial_record_error_status(result))


@require_POST
def register_view(request):
    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = register_user(payload)
    if result.get("ok"):
        user_payload = result.get("user") or {}
        account_id = user_payload.get("id")
        if account_id:
            request.session[SESSION_BOOKKEEPER_ID_KEY] = account_id
            request.session.pop(SESSION_ADMIN_ID_KEY, None)
            request.session.modified = True

        result["redirect_url"] = reverse("verify_email")
        return JsonResponse(result, status=201)

    error_message = result.get("message", "Unable to register account.")
    if error_message in {"Email already exists.", "Username already exists."}:
        return JsonResponse(result, status=409)

    return JsonResponse(result, status=400)


@require_POST
def login_view(request):
    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    result = login_user_or_admin(payload)
    if result.get("ok"):
        role = result.get("role")
        user_payload = result.get("user") or {}
        account_id = user_payload.get("id")
        if account_id and role == "admin":
            request.session[SESSION_ADMIN_ID_KEY] = account_id
            request.session.pop(SESSION_BOOKKEEPER_ID_KEY, None)
            request.session.modified = True
            result["redirect_url"] = reverse("admin_dashboard")
        else:
            status = user_payload.get("status") or BookkeeperAccount.STATUS_APPROVED
            email_verified = user_payload.get("email_verified", True)
            if account_id:
                request.session[SESSION_BOOKKEEPER_ID_KEY] = account_id
                request.session.pop(SESSION_ADMIN_ID_KEY, None)
                request.session.modified = True

            if not email_verified:
                result["redirect_url"] = reverse("verify_email")
                if account_id:
                    account = BookkeeperAccount.objects.filter(id=account_id).first()
                    if account:
                        verification_result = send_email_verification_code(account, force=False)
                        result["verification_email_sent"] = verification_result.get("ok", False)
                        if "retry_after_seconds" in verification_result:
                            result["verification_retry_after_seconds"] = verification_result["retry_after_seconds"]
                return JsonResponse(result)

            if status == BookkeeperAccount.STATUS_PENDING:
                result["redirect_url"] = reverse("pending_approval")
            else:
                result["redirect_url"] = _resolve_post_login_redirect(request, payload)
        return JsonResponse(result)

    error_message = result.get("message", "Unable to login.")
    if error_message == "Email or username and password are required.":
        return JsonResponse(result, status=400)

    # Keep expected auth failures as normal API responses to avoid noisy server warnings.
    return JsonResponse(result)


@require_POST
@require_bookkeeper_auth
def resend_email_verification_api_view(request):
    result = send_email_verification_code(request.bookkeeper_account, force=False)
    if result.get("ok"):
        return JsonResponse(result)

    status_code = 400
    if "retry_after_seconds" in result:
        status_code = 429
    return JsonResponse(result, status=status_code)


@require_POST
@require_bookkeeper_auth
def verify_email_api_view(request):
    payload = _decode_request_data(request)
    if payload is None:
        return JsonResponse(
            {"ok": False, "message": "Invalid request payload."},
            status=400,
        )

    code = payload.get("code") or payload.get("verification_code")
    result = verify_email_code(request.bookkeeper_account, code)
    if result.get("ok"):
        status = request.bookkeeper_account.status or BookkeeperAccount.STATUS_PENDING
        if status == BookkeeperAccount.STATUS_PENDING:
            result["redirect_url"] = reverse("pending_approval")
        else:
            result["redirect_url"] = reverse("dashboard")
        return JsonResponse(result)

    return JsonResponse(result, status=400)


@require_POST
@require_any_auth
def logout_view(request):
    request.session.flush()
    return JsonResponse(
        {
            "ok": True,
            "message": "Logged out successfully.",
            "redirect_url": reverse("login"),
        }
    )
