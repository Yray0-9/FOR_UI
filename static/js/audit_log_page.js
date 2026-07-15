(() => {
    const config = window.SafeBooksAuditLogConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;
    const body = document.body;

    const tableBody = document.getElementById("auditLogTableBody");
    const searchInput = document.getElementById("auditLogSearchInput");
    const sortSelect = document.getElementById("auditLogSortSelect");
    const filterButtons = Array.from(document.querySelectorAll("[data-audit-action]"));
    const countTag = document.getElementById("auditLogCountTag");

    if (!body || !tableBody || !searchInput || !sortSelect) {
        return;
    }

    const sidebarState = shared && typeof shared.initializeSidebarBehavior === "function"
        ? shared.initializeSidebarBehavior({
            bodyElement: body,
            sidebarToggle: document.getElementById("sidebarToggle"),
            sidebarCollapseToggle: document.getElementById("sidebarCollapseToggle"),
            sidebarCollapseIcon: document.getElementById("sidebarCollapseIcon"),
            sidebarBackdrop: document.getElementById("sidebarBackdrop"),
            storageKey: String(config.sidebarStateKey || "safebooks.sidebarCollapsed"),
            desktopQuery: String(config.desktopQuery || "(min-width: 992px)"),
        })
        : { closeMobileSidebar: () => {}, restoreDesktopState: () => {} };

    const escapeHtml = (value) => String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");

    const dateTimeFormatter = new Intl.DateTimeFormat("en-PH", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
    });

    const formatDateTime = (value) => {
        const parsed = new Date(String(value || ""));
        return Number.isNaN(parsed.getTime()) ? "-" : dateTimeFormatter.format(parsed);
    };

    const actionClass = (actionType) => {
        const action = String(actionType || "");
        if (action.startsWith("record.")) return "records";
        if (action.startsWith("security.") || action.startsWith("settings.")) return "security";
        return "";
    };

    const renderEmpty = (message) => {
        tableBody.innerHTML = `<tr class="audit-log-empty"><td colspan="4">${escapeHtml(message)}</td></tr>`;
    };

    const renderLogs = (logs) => {
        if (!Array.isArray(logs) || !logs.length) {
            renderEmpty("No activity matches the current filters.");
            return;
        }

        tableBody.innerHTML = logs.map((log) => `
            <tr>
                <td data-label="Date and time">${escapeHtml(formatDateTime(log.created_at))}</td>
                <td data-label="Activity"><span class="audit-action-badge ${actionClass(log.action_type)}">${escapeHtml(log.action_label || "Activity")}</span></td>
                <td data-label="Client"><span class="audit-log-client">${escapeHtml(log.client_name || "-")}</span></td>
                <td data-label="Details">${escapeHtml(log.message || "-")}</td>
            </tr>
        `).join("");
    };

    const state = { action: "all", search: "", sort: "newest" };

    const buildUrl = () => {
        const baseUrl = String(urls.auditLogApi || "");
        const params = new URLSearchParams();
        if (state.action !== "all") params.set("action", state.action);
        if (state.search) params.set("search", state.search);
        params.set("sort", state.sort);
        return `${baseUrl}?${params.toString()}`;
    };

    const fetchLogs = async () => {
        renderEmpty("Loading activity...");
        try {
            const response = await fetch(buildUrl(), {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            if (response.status === 401 || response.status === 403) {
                window.location.assign(String(urls.loginPage || "/login/"));
                return;
            }
            const payload = shared && typeof shared.parseJsonSafe === "function"
                ? await shared.parseJsonSafe(response)
                : await response.json();
            if (!response.ok || !payload || !payload.ok) {
                renderEmpty("Unable to load activity right now.");
                return;
            }
            renderLogs(payload.logs || []);
            if (countTag) {
                const total = Number(payload.total_count) || 0;
                countTag.textContent = `${total} ${total === 1 ? "activity" : "activities"}`;
            }
        } catch (error) {
            renderEmpty("Unable to load activity right now.");
        }
    };

    const setActiveFilter = (action) => {
        state.action = action;
        filterButtons.forEach((button) => {
            const active = String(button.dataset.auditAction || "all") === action;
            button.classList.toggle("is-active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });
    };

    let searchTimer = null;
    searchInput.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(() => {
            state.search = searchInput.value.trim();
            fetchLogs();
        }, 300);
    });

    sortSelect.addEventListener("change", () => {
        state.sort = String(sortSelect.value || "newest");
        fetchLogs();
    });

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setActiveFilter(String(button.dataset.auditAction || "all"));
            fetchLogs();
        });
    });

    sidebarState.restoreDesktopState();
    if (shared && typeof shared.applyStoredTheme === "function") shared.applyStoredTheme();
    window.addEventListener("resize", () => {
        sidebarState.closeMobileSidebar();
        sidebarState.restoreDesktopState();
    });
    setActiveFilter("all");
    fetchLogs();
})();
