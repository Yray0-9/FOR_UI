(() => {
    const config = window.SafeBooksAdminDashboardConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;

    const totalBookkeepers = document.getElementById("adminDashboardTotalBookkeepers");
    const pendingApprovals = document.getElementById("adminDashboardPendingApprovals");
    const activeAccounts = document.getElementById("adminDashboardActiveAccounts");
    const highLoad = document.getElementById("adminDashboardHighLoad");

    const loadTableBody = document.getElementById("adminDashboardLoadTableBody");

    const statusPending = document.getElementById("adminDashboardStatusPending");
    const statusApproved = document.getElementById("adminDashboardStatusApproved");
    const statusDeactivated = document.getElementById("adminDashboardStatusDeactivated");
    const statusInactive = document.getElementById("adminDashboardStatusInactive");

    const approvalNew = document.getElementById("adminDashboardApprovalNew");
    const approvalWaiting = document.getElementById("adminDashboardApprovalWaiting");
    const approvalOverdue = document.getElementById("adminDashboardApprovalOverdue");

    const uiToastContainer = document.getElementById("uiToastContainer");

    if (!totalBookkeepers || !pendingApprovals || !activeAccounts || !highLoad || !loadTableBody) {
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

    const resolveStatusMeta = (statusValue) => {
        const status = String(statusValue || "").toLowerCase();
        if (status === "approved") {
            return { label: "Approved", className: "approved" };
        }
        if (status === "suspended") {
            return { label: "Deactivated", className: "suspended" };
        }
        if (status === "rejected") {
            return { label: "Inactive", className: "inactive" };
        }
        if (status === "pending") {
            return { label: "Pending", className: "pending" };
        }
        return { label: "Inactive", className: "inactive" };
    };

    const renderEmptyRow = (message) => {
        loadTableBody.innerHTML = `
            <tr class="admin-table-empty">
                <td colspan="3">${escapeHtml(message || "No load data available yet.")}</td>
            </tr>
        `;
    };

    const renderLoadSnapshot = (items) => {
        if (!Array.isArray(items) || items.length === 0) {
            renderEmptyRow("No load data available yet.");
            return;
        }

        loadTableBody.innerHTML = items
            .map((item) => {
                const statusMeta = resolveStatusMeta(item.status);
                const countValue = Number.isFinite(item.client_count)
                    ? item.client_count
                    : Number(item.client_count || 0);

                return `
                    <tr>
                        <td>${escapeHtml(item.full_name || "-")}</td>
                        <td><span class="admin-status-chip ${statusMeta.className}">${escapeHtml(statusMeta.label)}</span></td>
                        <td>${escapeHtml(String(countValue))}</td>
                    </tr>
                `;
            })
            .join("");
    };

    const setCounts = (payload) => {
        const kpis = payload.kpis || {};
        totalBookkeepers.textContent = String(kpis.total_bookkeepers || 0);
        pendingApprovals.textContent = String(kpis.pending_approvals || 0);
        activeAccounts.textContent = String(kpis.active_accounts || 0);
        highLoad.textContent = String(kpis.high_client_load || 0);

        const statusOverview = payload.status_overview || {};
        if (statusPending) {
            statusPending.textContent = String(statusOverview.pending || 0);
        }
        if (statusApproved) {
            statusApproved.textContent = String(statusOverview.approved || 0);
        }
        if (statusDeactivated) {
            statusDeactivated.textContent = String(statusOverview.deactivated || 0);
        }
        if (statusInactive) {
            statusInactive.textContent = String(statusOverview.inactive || 0);
        }

        const readiness = payload.approval_readiness || {};
        if (approvalNew) {
            approvalNew.textContent = String(readiness.new || 0);
        }
        if (approvalWaiting) {
            approvalWaiting.textContent = String(readiness.waiting || 0);
        }
        if (approvalOverdue) {
            approvalOverdue.textContent = String(readiness.overdue || 0);
        }
    };

    const fetchDashboardSummary = async () => {
        const url = String(urls.dashboardSummaryApi || "");
        if (!url) {
            renderEmptyRow("Dashboard summary API is not configured.");
            return;
        }

        renderEmptyRow("Loading summary...");

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
                renderEmptyRow(payload && payload.message ? payload.message : "Unable to load dashboard summary.");
                return;
            }

            setCounts(payload);
            renderLoadSnapshot(payload.load_snapshot || []);
        } catch (error) {
            renderEmptyRow("Unable to load dashboard summary right now.");
        }
    };

    fetchDashboardSummary();
})();
