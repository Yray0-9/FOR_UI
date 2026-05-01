import json
from functools import wraps
from urllib.parse import urlencode

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from safebooks.models import BookkeeperAccount
from safebooks.services.auth_service import login_user, register_user
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
    update_record_for_client_period,
)
from safebooks.services.dashboard_service import get_dashboard_summary_for_bookkeeper
from safebooks.services.analytics_service import get_analytics_summary_for_bookkeeper


SESSION_BOOKKEEPER_ID_KEY = "safebooks_bookkeeper_id"


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


def require_bookkeeper_auth(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        account = _get_session_bookkeeper(request)
        if account is None:
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

        request.bookkeeper_account = account
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def home_page_view(request):
    if _get_session_bookkeeper(request):
        return redirect("dashboard")

    return render(request, "authentication/landing.html")


def login_page_view(request):
    if _get_session_bookkeeper(request):
        return redirect("dashboard")

    return render(request, "authentication/login.html")


def signup_page_view(request):
    if _get_session_bookkeeper(request):
        return redirect("dashboard")

    return render(request, "authentication/signup.html")


@require_bookkeeper_auth
@ensure_csrf_cookie
def dashboard_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/dashboard.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def clients_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/clients.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def financial_records_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/financial_records.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def financial_records_client_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/financial_records_client.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def analytics_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/analytics.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def reports_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/reports.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def settings_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/settings.html", context)


@require_bookkeeper_auth
@ensure_csrf_cookie
def profile_page_view(request):
    context = _build_user_context(request.bookkeeper_account)
    return render(request, "base/profile.html", context)


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
        result["redirect_url"] = reverse("login")
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

    result = login_user(payload)
    if result.get("ok"):
        user_payload = result.get("user") or {}
        account_id = user_payload.get("id")
        if account_id:
            request.session[SESSION_BOOKKEEPER_ID_KEY] = account_id
            request.session.modified = True

        result["redirect_url"] = _resolve_post_login_redirect(request, payload)
        return JsonResponse(result)

    error_message = result.get("message", "Unable to login.")
    if error_message == "Email or username and password are required.":
        return JsonResponse(result, status=400)

    # Keep expected auth failures as normal API responses to avoid noisy server warnings.
    return JsonResponse(result)


@require_POST
@require_bookkeeper_auth
def logout_view(request):
    request.session.flush()
    return JsonResponse(
        {
            "ok": True,
            "message": "Logged out successfully.",
            "redirect_url": reverse("login"),
        }
    )
