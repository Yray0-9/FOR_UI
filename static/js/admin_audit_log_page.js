(() => {
    const config = window.SafeBooksAdminAuditLogConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;

    const auditLogTableBody = document.getElementById("auditLogTableBody");
    const auditLogSearchInput = document.getElementById("auditLogSearchInput");
    const auditLogSortSelect = document.getElementById("auditLogSortSelect");
    const auditLogDateFromInput = document.getElementById("auditLogDateFromInput");
    const auditLogDateToInput = document.getElementById("auditLogDateToInput");
    const auditLogPreviousPage = document.getElementById("auditLogPreviousPage");
    const auditLogNextPage = document.getElementById("auditLogNextPage");
    const auditLogPageStatus = document.getElementById("auditLogPageStatus");
    const auditLogActionFilters = Array.from(document.querySelectorAll("[data-audit-action]"));
    const auditLogCountTag = document.getElementById("auditLogCountTag");
    const auditLogTotalCount = document.getElementById("auditLogTotalCount");
    const auditLogApprovalCount = document.getElementById("auditLogApprovalCount");
    const auditLogAccessCount = document.getElementById("auditLogAccessCount");
    const uiToastContainer = document.getElementById("uiToastContainer");

    if (!auditLogTableBody || !auditLogSearchInput || !auditLogSortSelect || !auditLogDateFromInput || !auditLogDateToInput) {
        return;
    }

    const escapeHtml = (value) => {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    };

    const showToast = (message, variantClass = "") => {
        if (!shared || typeof shared.showToast !== "function") {
            return;
        }

        shared.showToast(uiToastContainer, message, variantClass, { delay: 2800 });
    };

    const dateTimeFormatter = new Intl.DateTimeFormat("en-PH", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });

    const formatDateTime = (value) => {
        const parsed = new Date(String(value || ""));
        if (Number.isNaN(parsed.getTime())) {
            return "-";
        }
        return dateTimeFormatter.format(parsed);
    };

    const resolveActionClass = (actionType) => {
        const action = String(actionType || "").toLowerCase();
        if (action.includes("approved") || action.includes("reactivated")) {
            return "approved";
        }
        if (action.includes("rejected") || action.includes("deleted")) {
            return "rejected";
        }
        if (action.includes("deactivated")) {
            return "suspended";
        }
        if (action === "admin.login") {
            return "approved";
        }
        if (action === "admin.logout") {
            return "suspended";
        }
        return "inactive";
    };

    const renderEmptyRow = (message) => {
        auditLogTableBody.innerHTML = `
            <tr class="admin-table-empty">
                <td colspan="5">${escapeHtml(message || "No admin activity recorded yet.")}</td>
            </tr>
        `;
    };

    const setCounts = (payload) => {
        const counts = payload && payload.counts ? payload.counts : {};
        const shownCount = Number(payload && payload.shown_count) || 0;
        const totalCount = Number(payload && payload.total_count) || 0;

        if (auditLogCountTag) {
            auditLogCountTag.textContent = `${shownCount} of ${totalCount}`;
        }
        if (auditLogTotalCount) {
            auditLogTotalCount.textContent = String(Number(counts.all) || totalCount || 0);
        }
        if (auditLogApprovalCount) {
            auditLogApprovalCount.textContent = String(Number(counts.approvals) || 0);
        }
        if (auditLogAccessCount) {
            auditLogAccessCount.textContent = String(Number(counts.access) || 0);
        }
    };

    const setPagination = (payload) => {
        const currentPage = Math.max(Number(payload && payload.page) || 1, 1);
        const totalPages = Math.max(Number(payload && payload.total_pages) || 1, 1);
        state.page = currentPage;

        if (auditLogPageStatus) {
            auditLogPageStatus.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        if (auditLogPreviousPage) {
            auditLogPreviousPage.disabled = !Boolean(payload && payload.has_previous);
        }
        if (auditLogNextPage) {
            auditLogNextPage.disabled = !Boolean(payload && payload.has_next);
        }
    };

    const renderLogs = (logs) => {
        if (!Array.isArray(logs) || logs.length === 0) {
            renderEmptyRow("No admin activity matches the current filters.");
            return;
        }

        auditLogTableBody.innerHTML = logs
            .map((log) => {
                const actionClass = resolveActionClass(log.action_type);
                const targetLines = [
                    `<strong>${escapeHtml(log.target_name || "-")}</strong>`,
                    log.target_email ? `<small>${escapeHtml(log.target_email)}</small>` : "",
                ].filter(Boolean).join("");
                const adminLines = [
                    `<strong>${escapeHtml(log.admin_name || "System")}</strong>`,
                    log.admin_email ? `<small>${escapeHtml(log.admin_email)}</small>` : "",
                ].filter(Boolean).join("");
                const decisionNote = String(log.metadata && log.metadata.decision_note || "").trim();
                const messageLines = [
                    `<span>${escapeHtml(log.message || "-")}</span>`,
                    decisionNote ? `<small class="admin-audit-decision-note">Note: ${escapeHtml(decisionNote)}</small>` : "",
                ].filter(Boolean).join("");

                return `
                    <tr>
                        <td>${escapeHtml(formatDateTime(log.created_at))}</td>
                        <td><div class="admin-audit-person">${adminLines}</div></td>
                        <td><span class="admin-status-chip ${actionClass}">${escapeHtml(log.action_label || log.action_type || "-")}</span></td>
                        <td><div class="admin-audit-person">${targetLines}</div></td>
                        <td><div class="admin-audit-message">${messageLines}</div></td>
                    </tr>
                `;
            })
            .join("");
    };

    const buildAuditLogUrl = () => {
        const baseUrl = String(urls.auditLogApi || "");
        if (!baseUrl) {
            return "";
        }

        const searchParams = new URLSearchParams();
        if (state.action && state.action !== "all") {
            searchParams.set("action", state.action);
        }
        if (state.search) {
            searchParams.set("search", state.search);
        }
        if (state.sort) {
            searchParams.set("sort", state.sort);
        }
        if (state.dateFrom) {
            searchParams.set("date_from", state.dateFrom);
        }
        if (state.dateTo) {
            searchParams.set("date_to", state.dateTo);
        }
        searchParams.set("page", String(state.page));
        searchParams.set("page_size", String(state.pageSize));

        return searchParams.toString() ? `${baseUrl}?${searchParams.toString()}` : baseUrl;
    };

    const fetchAuditLogs = async () => {
        const url = buildAuditLogUrl();
        if (!url) {
            renderEmptyRow("Audit log API is not configured.");
            return;
        }

        renderEmptyRow("Loading admin activity...");

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                credentials: "same-origin",
            });

            if (response.status === 401 || response.status === 403) {
                showToast("Admin session expired. Please log in again.", "warning");
                const loginPage = String(urls.loginPage || "/login/");
                window.location.assign(loginPage);
                return;
            }

            const payload = shared && typeof shared.parseJsonSafe === "function"
                ? await shared.parseJsonSafe(response)
                : await response.json();

            if (!response.ok || !payload || !payload.ok) {
                renderEmptyRow(payload && payload.message ? payload.message : "Unable to load audit log.");
                return;
            }

            renderLogs(payload.logs || []);
            setCounts(payload);
            setPagination(payload);
        } catch (error) {
            renderEmptyRow("Unable to load audit log right now.");
        }
    };

    const setActiveActionFilter = (nextAction) => {
        state.action = nextAction;
        auditLogActionFilters.forEach((button) => {
            const actionValue = String(button.dataset.auditAction || "all");
            const isActive = actionValue === nextAction;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
        });
    };

    let searchDebounceId = null;
    const scheduleSearch = () => {
        if (searchDebounceId) {
            window.clearTimeout(searchDebounceId);
        }
        searchDebounceId = window.setTimeout(() => {
            state.search = auditLogSearchInput.value.trim();
            state.page = 1;
            fetchAuditLogs();
        }, 320);
    };

    const state = {
        action: "all",
        search: "",
        sort: "newest",
        dateFrom: "",
        dateTo: "",
        page: 1,
        pageSize: 10,
    };

    auditLogActionFilters.forEach((button) => {
        button.addEventListener("click", () => {
            const nextAction = String(button.dataset.auditAction || "all");
            setActiveActionFilter(nextAction);
            state.page = 1;
            fetchAuditLogs();
        });
    });

    auditLogSortSelect.addEventListener("change", () => {
        state.sort = String(auditLogSortSelect.value || "newest");
        state.page = 1;
        fetchAuditLogs();
    });

    const hasCompleteYear = (value) => {
        const normalized = String(value || "");
        if (!normalized) {
            return true;
        }
        const match = /^(\d{4})-\d{2}-\d{2}$/.exec(normalized);
        return Boolean(match && Number(match[1]) >= 1000);
    };

    const applyDateFilters = () => {
        const dateFrom = String(auditLogDateFromInput.value || "");
        const dateTo = String(auditLogDateToInput.value || "");
        if (!hasCompleteYear(dateFrom) || !hasCompleteYear(dateTo)) {
            return;
        }
        if (dateFrom && dateTo && dateFrom > dateTo) {
            showToast("Date from cannot be after date to.", "warning");
            return;
        }
        state.dateFrom = dateFrom;
        state.dateTo = dateTo;
        state.page = 1;
        fetchAuditLogs();
    };

    auditLogDateFromInput.addEventListener("change", applyDateFilters);
    auditLogDateToInput.addEventListener("change", applyDateFilters);

    if (auditLogPreviousPage) {
        auditLogPreviousPage.addEventListener("click", () => {
            if (state.page <= 1) {
                return;
            }
            state.page -= 1;
            fetchAuditLogs();
        });
    }

    if (auditLogNextPage) {
        auditLogNextPage.addEventListener("click", () => {
            state.page += 1;
            fetchAuditLogs();
        });
    }

    auditLogSearchInput.addEventListener("input", scheduleSearch);

    setActiveActionFilter("all");
    fetchAuditLogs();
})();
