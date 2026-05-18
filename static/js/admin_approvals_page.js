(() => {
    const config = window.SafeBooksAdminApprovalsConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;

    const approvalsTableBody = document.getElementById("approvalsTableBody");
    const approvalsSearchInput = document.getElementById("approvalsSearchInput");
    const approvalsSortSelect = document.getElementById("approvalsSortSelect");
    const approvalsStatusFilters = Array.from(document.querySelectorAll("[data-approval-status]"));
    const approvalsCountTag = document.getElementById("approvalsCountTag");
    const approvalsRefreshButton = document.getElementById("approvalsRefreshButton");

    const approvalsPendingCount = document.getElementById("approvalsPendingCount");
    const approvalsApprovedCount = document.getElementById("approvalsApprovedCount");
    const approvalsRejectedCount = document.getElementById("approvalsRejectedCount");
    const approvalsApprovedToday = document.getElementById("approvalsApprovedToday");
    const approvalsRejectedToday = document.getElementById("approvalsRejectedToday");

    const approvalsActionModal = document.getElementById("approvalsActionModal");
    const approvalsActionModalLabel = document.getElementById("approvalsActionModalLabel");
    const approvalsActionModalMessage = document.getElementById("approvalsActionModalMessage");
    const approvalsActionConfirm = document.getElementById("approvalsActionConfirm");
    const approvalsActionReasonWrap = document.getElementById("approvalsActionReasonWrap");
    const approvalsActionReasonInput = document.getElementById("approvalsActionReasonInput");

    const approvalDetailEmpty = document.getElementById("approvalDetailEmpty");
    const approvalDetailList = document.getElementById("approvalDetailList");
    const approvalDetailName = document.getElementById("approvalDetailName");
    const approvalDetailEmail = document.getElementById("approvalDetailEmail");
    const approvalDetailDate = document.getElementById("approvalDetailDate");
    const approvalDetailStatus = document.getElementById("approvalDetailStatus");

    const uiToastContainer = document.getElementById("uiToastContainer");

    if (!approvalsTableBody || !approvalsSearchInput || !approvalsSortSelect || !approvalsStatusFilters.length) {
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

    const dateFormatter = new Intl.DateTimeFormat("en-PH", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });

    const formatDate = (value) => {
        const parsed = new Date(String(value || ""));
        if (Number.isNaN(parsed.getTime())) {
            return "-";
        }
        return dateFormatter.format(parsed);
    };

    const resolveStatusMeta = (statusValue) => {
        const status = String(statusValue || "").toLowerCase();
        if (status === "pending") {
            return { label: "Pending", className: "pending" };
        }
        if (status === "approved") {
            return { label: "Approved", className: "approved" };
        }
        if (status === "rejected") {
            return { label: "Rejected", className: "rejected" };
        }
        if (status === "suspended") {
            return { label: "Suspended", className: "suspended" };
        }
        return { label: "Inactive", className: "inactive" };
    };

    const setDetailState = (approval) => {
        if (!approval) {
            if (approvalDetailEmpty) {
                approvalDetailEmpty.hidden = false;
            }
            if (approvalDetailList) {
                approvalDetailList.hidden = true;
            }
            return;
        }

        const statusMeta = resolveStatusMeta(approval.status);
        if (approvalDetailEmpty) {
            approvalDetailEmpty.hidden = true;
        }
        if (approvalDetailList) {
            approvalDetailList.hidden = false;
        }
        if (approvalDetailName) {
            approvalDetailName.textContent = approval.full_name || "-";
        }
        if (approvalDetailEmail) {
            approvalDetailEmail.textContent = approval.email || "-";
        }
        if (approvalDetailDate) {
            approvalDetailDate.textContent = formatDate(approval.created_at);
        }
        if (approvalDetailStatus) {
            approvalDetailStatus.textContent = statusMeta.label;
            approvalDetailStatus.className = `admin-status-chip ${statusMeta.className}`;
        }
    };

    const setCounts = (counts, total) => {
        if (!approvalsCountTag) {
            return;
        }

        const totalValue = Number.isFinite(total) ? total : 0;
        approvalsCountTag.textContent = `${totalValue} request${totalValue === 1 ? "" : "s"}`;

        if (approvalsPendingCount) {
            approvalsPendingCount.textContent = String((counts && counts.pending) || 0);
        }
        if (approvalsApprovedCount) {
            approvalsApprovedCount.textContent = String((counts && counts.approved) || 0);
        }
        if (approvalsRejectedCount) {
            approvalsRejectedCount.textContent = String((counts && counts.rejected) || 0);
        }
        if (approvalsApprovedToday) {
            approvalsApprovedToday.textContent = String((counts && counts.approved_today) || 0);
        }
        if (approvalsRejectedToday) {
            approvalsRejectedToday.textContent = String((counts && counts.rejected_today) || 0);
        }
    };

    const renderEmptyRow = (message) => {
        approvalsTableBody.innerHTML = `
            <tr class="admin-table-empty">
                <td colspan="5">${escapeHtml(message || "No approval requests yet.")}</td>
            </tr>
        `;
    };

    const buildActionButton = (label, action, approvalId, enabled, extraClass) => {
        const classes = ["admin-action-btn", extraClass];
        if (enabled) {
            classes.push("is-enabled");
        }

        return `
            <button type="button" class="${classes.filter(Boolean).join(" ")}" data-action="${action}" data-approval-id="${approvalId}" ${enabled ? "" : "disabled"}>
                ${escapeHtml(label)}
            </button>
        `;
    };

    const renderApprovals = (approvals) => {
        if (!Array.isArray(approvals) || approvals.length === 0) {
            renderEmptyRow("No approval requests yet.");
            setDetailState(null);
            return;
        }

        approvalsTableBody.innerHTML = approvals
            .map((approval) => {
                const statusMeta = resolveStatusMeta(approval.status);
                const canApprove = approval.status === "pending" || approval.status === "rejected";
                const canReject = approval.status === "pending";

                return `
                    <tr data-approval-id="${approval.id}">
                        <td>${escapeHtml(approval.full_name || "-")}</td>
                        <td>${escapeHtml(approval.email || "-")}</td>
                        <td>${escapeHtml(formatDate(approval.created_at))}</td>
                        <td><span class="admin-status-chip ${statusMeta.className}">${escapeHtml(statusMeta.label)}</span></td>
                        <td>
                            <div class="admin-table-actions">
                                ${buildActionButton("Approve", "approve", approval.id, canApprove, "approve")}
                                ${buildActionButton("Reject", "reject", approval.id, canReject, "reject")}
                                ${buildActionButton("View details", "detail", approval.id, true, "detail")}
                            </div>
                        </td>
                    </tr>
                `;
            })
            .join("");
    };

    const getApprovalById = (approvalId) => {
        return approvalsCache.find((item) => item.id === approvalId) || null;
    };

    let actionModalInstance = null;
    if (approvalsActionModal && window.bootstrap && window.bootstrap.Modal) {
        actionModalInstance = new window.bootstrap.Modal(approvalsActionModal, {
            backdrop: "static",
            keyboard: false,
        });
    }

    const openActionModal = (approval, action) => {
        if (!approval || !actionModalInstance) {
            showToast("Action modal is not available. Refresh the page.", "warning");
            return;
        }

        const name = approval.full_name || "this bookkeeper";
        pendingAction = {
            id: approval.id,
            action,
        };

        if (approvalsActionReasonInput) {
            approvalsActionReasonInput.value = "";
        }

        if (action === "approve") {
            if (approvalsActionModalLabel) {
                approvalsActionModalLabel.textContent = "Approve bookkeeper account";
            }
            if (approvalsActionModalMessage) {
                approvalsActionModalMessage.textContent = `Approve ${name}?`;
            }
            if (approvalsActionReasonWrap) {
                approvalsActionReasonWrap.hidden = true;
            }
            if (approvalsActionConfirm) {
                approvalsActionConfirm.textContent = "Approve";
                approvalsActionConfirm.classList.remove("outline");
                approvalsActionConfirm.classList.add("primary");
            }
        } else {
            if (approvalsActionModalLabel) {
                approvalsActionModalLabel.textContent = "Reject bookkeeper account";
            }
            if (approvalsActionModalMessage) {
                approvalsActionModalMessage.textContent = `Reject ${name}?`;
            }
            if (approvalsActionReasonWrap) {
                approvalsActionReasonWrap.hidden = false;
            }
            if (approvalsActionConfirm) {
                approvalsActionConfirm.textContent = "Reject";
                approvalsActionConfirm.classList.remove("primary");
                approvalsActionConfirm.classList.add("outline");
            }
        }

        actionModalInstance.show();
    };

    const buildApprovalsUrl = () => {
        const baseUrl = String(urls.approvalsApi || "");
        if (!baseUrl) {
            return "";
        }

        const searchParams = new URLSearchParams();
        if (state.status !== "all") {
            searchParams.set("status", state.status);
        }
        if (state.search) {
            searchParams.set("search", state.search);
        }
        if (state.sort) {
            searchParams.set("sort", state.sort);
        }

        return searchParams.toString() ? `${baseUrl}?${searchParams.toString()}` : baseUrl;
    };

    const buildActionUrl = (approvalId, action) => {
        const baseUrl = String(urls.approvalsBaseApi || urls.approvalsApi || "");
        if (!baseUrl) {
            return "";
        }

        const normalizedBase = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
        return `${normalizedBase}${approvalId}/${action}/`;
    };

    const fetchApprovals = async () => {
        const url = buildApprovalsUrl();
        if (!url) {
            renderEmptyRow("Approvals API is not configured.");
            return;
        }

        renderEmptyRow("Loading approvals...");

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
                renderEmptyRow(payload && payload.message ? payload.message : "Unable to load approvals.");
                return;
            }

            approvalsCache = Array.isArray(payload.approvals) ? payload.approvals : [];
            renderApprovals(approvalsCache);
            setCounts(payload.counts, payload.total_count);

            if (approvalsCache.length > 0 && !selectedApprovalId) {
                selectedApprovalId = approvalsCache[0].id;
                setDetailState(approvalsCache[0]);
            }

            if (selectedApprovalId) {
                const selected = approvalsCache.find((item) => item.id === selectedApprovalId) || null;
                setDetailState(selected);
                if (!selected) {
                    selectedApprovalId = null;
                }
            }
        } catch (error) {
            renderEmptyRow("Unable to load approvals right now.");
        }
    };

    const runApprovalAction = async (approvalId, action, rejectionReason = "") => {
        const url = buildActionUrl(approvalId, action);
        if (!url) {
            showToast("Approval action is unavailable.", "warning");
            return;
        }

        let payload = {};
        if (action === "reject") {
            payload = { rejection_reason: rejectionReason };
        }

        const csrfToken = shared && typeof shared.getCookieValue === "function"
            ? shared.getCookieValue("csrftoken")
            : "";

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                    "X-CSRFToken": csrfToken,
                },
                credentials: "same-origin",
                body: JSON.stringify(payload),
            });

            const result = shared && typeof shared.parseJsonSafe === "function"
                ? await shared.parseJsonSafe(response)
                : await response.json();

            if (!response.ok || !result || !result.ok) {
                showToast(result && result.message ? result.message : "Action failed.", "warning");
                return;
            }

            showToast(result.message || "Action completed.", "success");
            await fetchApprovals();
        } catch (error) {
            showToast("Unable to complete action right now.", "warning");
        }
    };

    const setActiveFilter = (nextStatus) => {
        state.status = nextStatus;
        approvalsStatusFilters.forEach((button) => {
            const statusValue = String(button.dataset.approvalStatus || "all");
            const isActive = statusValue === nextStatus;
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
            state.search = approvalsSearchInput.value.trim();
            fetchApprovals();
        }, 320);
    };

    const state = {
        status: "all",
        search: "",
        sort: "newest",
    };

    let approvalsCache = [];
    let selectedApprovalId = null;
    let pendingAction = null;

    approvalsStatusFilters.forEach((button) => {
        button.addEventListener("click", () => {
            const nextStatus = String(button.dataset.approvalStatus || "all");
            setActiveFilter(nextStatus);
            fetchApprovals();
        });
    });

    approvalsSortSelect.addEventListener("change", () => {
        state.sort = String(approvalsSortSelect.value || "newest");
        fetchApprovals();
    });

    approvalsSearchInput.addEventListener("input", scheduleSearch);

    if (approvalsRefreshButton) {
        approvalsRefreshButton.addEventListener("click", () => {
            fetchApprovals();
        });
    }

    approvalsTableBody.addEventListener("click", (event) => {
        const actionButton = event.target.closest("button[data-action]");
        const row = event.target.closest("tr[data-approval-id]");

        if (actionButton) {
            const action = String(actionButton.dataset.action || "");
            const approvalId = Number(actionButton.dataset.approvalId || 0);
            if (!approvalId || !action) {
                return;
            }

            if (action === "detail") {
                const selected = getApprovalById(approvalId);
                selectedApprovalId = approvalId;
                setDetailState(selected);
                return;
            }

            if (action === "approve") {
                const selected = getApprovalById(approvalId);
                selectedApprovalId = approvalId;
                setDetailState(selected);
                openActionModal(selected, "approve");
                return;
            }

            if (action === "reject") {
                const selected = getApprovalById(approvalId);
                selectedApprovalId = approvalId;
                setDetailState(selected);
                openActionModal(selected, "reject");
                return;
            }
        }

        if (row) {
            const approvalId = Number(row.dataset.approvalId || 0);
            const selected = getApprovalById(approvalId);
            if (selected) {
                selectedApprovalId = approvalId;
                setDetailState(selected);
            }
        }
    });

    if (approvalsActionConfirm) {
        approvalsActionConfirm.addEventListener("click", async () => {
            if (!pendingAction) {
                return;
            }

            const { id, action } = pendingAction;
            const rejectionReason = approvalsActionReasonInput
                ? approvalsActionReasonInput.value.trim()
                : "";

            approvalsActionConfirm.disabled = true;
            await runApprovalAction(id, action, rejectionReason);
            approvalsActionConfirm.disabled = false;
            pendingAction = null;

            if (actionModalInstance) {
                actionModalInstance.hide();
            }
        });
    }

    setActiveFilter("all");
    fetchApprovals();
})();
