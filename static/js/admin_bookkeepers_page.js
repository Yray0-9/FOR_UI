(() => {
    const config = window.SafeBooksAdminBookkeepersConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;

    const bookkeepersTableBody = document.getElementById("bookkeepersTableBody");
    const bookkeepersSearchInput = document.getElementById("bookkeepersSearchInput");
    const bookkeepersSortSelect = document.getElementById("bookkeepersSortSelect");
    const bookkeepersStatusFilters = Array.from(document.querySelectorAll("[data-bookkeeper-status]"));
    const bookkeepersClientFilters = Array.from(document.querySelectorAll("[data-bookkeeper-clients]"));
    const bookkeepersCountTag = document.getElementById("bookkeepersCountTag");
    const bookkeepersRefreshButton = document.getElementById("bookkeepersRefreshButton");

    const bookkeepersTotalCount = document.getElementById("bookkeepersTotalCount");
    const bookkeepersActiveCount = document.getElementById("bookkeepersActiveCount");
    const bookkeepersDeactivatedCount = document.getElementById("bookkeepersDeactivatedCount");
    const bookkeepersApprovedCount = document.getElementById("bookkeepersApprovedCount");
    const bookkeepersDeactivatedSummary = document.getElementById("bookkeepersDeactivatedSummary");
    const bookkeepersInactiveCount = document.getElementById("bookkeepersInactiveCount");

    const bookkeepersClientsZeroToFive = document.getElementById("bookkeepersClientsZeroToFive");
    const bookkeepersClientsSixToFifteen = document.getElementById("bookkeepersClientsSixToFifteen");
    const bookkeepersClientsSixteenPlus = document.getElementById("bookkeepersClientsSixteenPlus");

    const bookkeeperActionModal = document.getElementById("bookkeeperActionModal");
    const bookkeeperActionModalLabel = document.getElementById("bookkeeperActionModalLabel");
    const bookkeeperActionModalMessage = document.getElementById("bookkeeperActionModalMessage");
    const bookkeeperActionModalWarning = document.getElementById("bookkeeperActionModalWarning");
    const bookkeeperActionConfirm = document.getElementById("bookkeeperActionConfirm");

    const uiToastContainer = document.getElementById("uiToastContainer");

    if (!bookkeepersTableBody || !bookkeepersSearchInput || !bookkeepersSortSelect) {
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

    const setCounts = (counts, clientSummary) => {
        const totalValue = Number.isFinite(counts.total) ? counts.total : 0;
        if (bookkeepersCountTag) {
            bookkeepersCountTag.textContent = `${totalValue} bookkeeper${totalValue === 1 ? "" : "s"}`;
        }

        if (bookkeepersTotalCount) {
            bookkeepersTotalCount.textContent = String(totalValue);
        }
        if (bookkeepersActiveCount) {
            bookkeepersActiveCount.textContent = String((counts && counts.active) || 0);
        }
        if (bookkeepersDeactivatedCount) {
            bookkeepersDeactivatedCount.textContent = String((counts && counts.deactivated) || 0);
        }
        if (bookkeepersApprovedCount) {
            bookkeepersApprovedCount.textContent = String((counts && counts.active) || 0);
        }
        if (bookkeepersDeactivatedSummary) {
            bookkeepersDeactivatedSummary.textContent = String((counts && counts.deactivated) || 0);
        }
        if (bookkeepersInactiveCount) {
            bookkeepersInactiveCount.textContent = String((counts && counts.inactive) || 0);
        }

        if (bookkeepersClientsZeroToFive) {
            bookkeepersClientsZeroToFive.textContent = String((clientSummary && clientSummary.zero_to_five) || 0);
        }
        if (bookkeepersClientsSixToFifteen) {
            bookkeepersClientsSixToFifteen.textContent = String((clientSummary && clientSummary.six_to_fifteen) || 0);
        }
        if (bookkeepersClientsSixteenPlus) {
            bookkeepersClientsSixteenPlus.textContent = String((clientSummary && clientSummary.sixteen_plus) || 0);
        }
    };

    const renderEmptyRow = (message) => {
        bookkeepersTableBody.innerHTML = `
            <tr class="admin-table-empty">
                <td colspan="6">${escapeHtml(message || "No bookkeepers available yet.")}</td>
            </tr>
        `;
    };

    const buildActionButton = (label, action, bookkeeperId, enabled, extraClass) => {
        const classes = ["admin-action-btn", extraClass];
        if (enabled) {
            classes.push("is-enabled");
        }

        return `
            <button type="button" class="${classes.filter(Boolean).join(" ")}" data-action="${action}" data-bookkeeper-id="${bookkeeperId}" ${enabled ? "" : "disabled"}>
                ${escapeHtml(label)}
            </button>
        `;
    };

    const renderBookkeepers = (bookkeepers) => {
        if (!Array.isArray(bookkeepers) || bookkeepers.length === 0) {
            renderEmptyRow("No bookkeepers available yet.");
            return;
        }

        bookkeepersTableBody.innerHTML = bookkeepers
            .map((bookkeeper) => {
                const statusMeta = resolveStatusMeta(bookkeeper.status);
                const clientsCount = Number.isFinite(bookkeeper.client_count)
                    ? bookkeeper.client_count
                    : Number(bookkeeper.client_count || 0);
                const canToggle = bookkeeper.status === "approved" || bookkeeper.status === "suspended";
                const toggleAction = bookkeeper.status === "suspended" ? "reactivate" : "deactivate";
                const toggleLabel = bookkeeper.status === "suspended" ? "Reactivate" : "Deactivate";
                const toggleClass = bookkeeper.status === "suspended" ? "reactivate" : "deactivate";

                return `
                    <tr data-bookkeeper-id="${bookkeeper.id}">
                        <td>${escapeHtml(bookkeeper.full_name || "-")}</td>
                        <td>${escapeHtml(bookkeeper.email || "-")}</td>
                        <td><span class="admin-status-chip ${statusMeta.className}">${escapeHtml(statusMeta.label)}</span></td>
                        <td>${escapeHtml(String(clientsCount))}</td>
                        <td>${escapeHtml(formatDate(bookkeeper.last_login))}</td>
                        <td>
                            <div class="admin-table-actions">
                                ${buildActionButton(toggleLabel, toggleAction, bookkeeper.id, canToggle, toggleClass)}
                                ${buildActionButton("Delete", "delete", bookkeeper.id, true, "delete")}
                            </div>
                        </td>
                    </tr>
                `;
            })
            .join("");
    };

    const buildBookkeepersUrl = () => {
        const baseUrl = String(urls.bookkeepersApi || "");
        if (!baseUrl) {
            return "";
        }

        const searchParams = new URLSearchParams();
        if (state.status && state.status !== "all") {
            searchParams.set("status", state.status);
        }
        if (state.clients) {
            searchParams.set("clients", state.clients);
        }
        if (state.search) {
            searchParams.set("search", state.search);
        }
        if (state.sort) {
            searchParams.set("sort", state.sort);
        }

        return searchParams.toString() ? `${baseUrl}?${searchParams.toString()}` : baseUrl;
    };

    const buildActionUrl = (bookkeeperId, action) => {
        const baseUrl = String(urls.bookkeepersBaseApi || urls.bookkeepersApi || "");
        if (!baseUrl) {
            return "";
        }

        const normalizedBase = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
        return `${normalizedBase}${bookkeeperId}/${action}/`;
    };

    const fetchBookkeepers = async () => {
        const url = buildBookkeepersUrl();
        if (!url) {
            renderEmptyRow("Bookkeepers API is not configured.");
            return;
        }

        renderEmptyRow("Loading bookkeepers...");

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
                renderEmptyRow(payload && payload.message ? payload.message : "Unable to load bookkeepers.");
                return;
            }

            bookkeepersCache = Array.isArray(payload.bookkeepers) ? payload.bookkeepers : [];
            renderBookkeepers(bookkeepersCache);
            setCounts(payload.counts || {}, payload.client_summary || {});
        } catch (error) {
            renderEmptyRow("Unable to load bookkeepers right now.");
        }
    };

    const runBookkeeperAction = async (bookkeeperId, action) => {
        const url = buildActionUrl(bookkeeperId, action);
        if (!url) {
            showToast("Bookkeeper action is unavailable.", "warning");
            return;
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
                body: JSON.stringify({}),
            });

            const result = shared && typeof shared.parseJsonSafe === "function"
                ? await shared.parseJsonSafe(response)
                : await response.json();

            if (!response.ok || !result || !result.ok) {
                showToast(result && result.message ? result.message : "Action failed.", "warning");
                return;
            }

            showToast(result.message || "Action completed.", "success");
            await fetchBookkeepers();
        } catch (error) {
            showToast("Unable to complete action right now.", "warning");
        }
    };

    const setActiveStatusFilter = (nextStatus) => {
        state.status = nextStatus;
        bookkeepersStatusFilters.forEach((button) => {
            const statusValue = String(button.dataset.bookkeeperStatus || "all");
            const isActive = statusValue === nextStatus;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
        });
    };

    const setActiveClientFilter = (nextClients) => {
        state.clients = nextClients;
        bookkeepersClientFilters.forEach((button) => {
            const filterValue = String(button.dataset.bookkeeperClients || "");
            const isActive = filterValue === nextClients && nextClients !== "";
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
            state.search = bookkeepersSearchInput.value.trim();
            fetchBookkeepers();
        }, 320);
    };

    let actionModalInstance = null;
    if (bookkeeperActionModal && window.bootstrap && window.bootstrap.Modal) {
        actionModalInstance = new window.bootstrap.Modal(bookkeeperActionModal, {
            backdrop: "static",
            keyboard: false,
        });
    }

    const openActionModal = (bookkeeper, action) => {
        if (!bookkeeper || !actionModalInstance) {
            showToast("Action modal is not available. Refresh the page.", "warning");
            return;
        }

        const name = bookkeeper.full_name || "this bookkeeper";
        pendingAction = {
            id: bookkeeper.id,
            action,
        };

        if (bookkeeperActionModalWarning) {
            bookkeeperActionModalWarning.hidden = true;
            bookkeeperActionModalWarning.textContent = "";
        }

        if (action === "deactivate") {
            if (bookkeeperActionModalLabel) {
                bookkeeperActionModalLabel.textContent = "Deactivate bookkeeper account";
            }
            if (bookkeeperActionModalMessage) {
                bookkeeperActionModalMessage.textContent = `Deactivate ${name}?`;
            }
            if (bookkeeperActionModalWarning) {
                bookkeeperActionModalWarning.hidden = false;
                bookkeeperActionModalWarning.textContent = "This account will lose access until reactivated.";
            }
            if (bookkeeperActionConfirm) {
                bookkeeperActionConfirm.textContent = "Deactivate";
                bookkeeperActionConfirm.classList.remove("primary");
                bookkeeperActionConfirm.classList.add("outline");
            }
        } else if (action === "reactivate") {
            if (bookkeeperActionModalLabel) {
                bookkeeperActionModalLabel.textContent = "Reactivate bookkeeper account";
            }
            if (bookkeeperActionModalMessage) {
                bookkeeperActionModalMessage.textContent = `Reactivate ${name}?`;
            }
            if (bookkeeperActionConfirm) {
                bookkeeperActionConfirm.textContent = "Reactivate";
                bookkeeperActionConfirm.classList.remove("outline");
                bookkeeperActionConfirm.classList.add("primary");
            }
        } else {
            if (bookkeeperActionModalLabel) {
                bookkeeperActionModalLabel.textContent = "Delete bookkeeper account";
            }
            if (bookkeeperActionModalMessage) {
                bookkeeperActionModalMessage.textContent = `Delete ${name}?`;
            }
            if (bookkeeperActionModalWarning) {
                bookkeeperActionModalWarning.hidden = false;
                bookkeeperActionModalWarning.textContent = "This action permanently removes the account.";
            }
            if (bookkeeperActionConfirm) {
                bookkeeperActionConfirm.textContent = "Delete";
                bookkeeperActionConfirm.classList.remove("primary");
                bookkeeperActionConfirm.classList.add("outline");
            }
        }

        actionModalInstance.show();
    };

    const state = {
        status: "all",
        clients: "",
        search: "",
        sort: "recent",
    };

    let bookkeepersCache = [];
    let pendingAction = null;

    bookkeepersStatusFilters.forEach((button) => {
        button.addEventListener("click", () => {
            const nextStatus = String(button.dataset.bookkeeperStatus || "all");
            setActiveStatusFilter(nextStatus);
            fetchBookkeepers();
        });
    });

    bookkeepersClientFilters.forEach((button) => {
        button.addEventListener("click", () => {
            const filterValue = String(button.dataset.bookkeeperClients || "");
            const nextValue = state.clients === filterValue ? "" : filterValue;
            setActiveClientFilter(nextValue);
            fetchBookkeepers();
        });
    });

    bookkeepersSortSelect.addEventListener("change", () => {
        state.sort = String(bookkeepersSortSelect.value || "recent");
        fetchBookkeepers();
    });

    bookkeepersSearchInput.addEventListener("input", scheduleSearch);

    if (bookkeepersRefreshButton) {
        bookkeepersRefreshButton.addEventListener("click", () => {
            fetchBookkeepers();
        });
    }

    bookkeepersTableBody.addEventListener("click", (event) => {
        const actionButton = event.target.closest("button[data-action]");
        if (!actionButton) {
            return;
        }

        const action = String(actionButton.dataset.action || "");
        const bookkeeperId = Number(actionButton.dataset.bookkeeperId || 0);
        if (!action || !bookkeeperId) {
            return;
        }

        const selected = bookkeepersCache.find((item) => item.id === bookkeeperId) || null;
        if (!selected) {
            showToast("Unable to locate this bookkeeper.", "warning");
            return;
        }

        openActionModal(selected, action);
    });

    if (bookkeeperActionConfirm) {
        bookkeeperActionConfirm.addEventListener("click", async () => {
            if (!pendingAction) {
                return;
            }

            const { id, action } = pendingAction;
            bookkeeperActionConfirm.disabled = true;
            await runBookkeeperAction(id, action);
            bookkeeperActionConfirm.disabled = false;
            pendingAction = null;

            if (actionModalInstance) {
                actionModalInstance.hide();
            }
        });
    }

    setActiveStatusFilter("all");
    setActiveClientFilter("");
    fetchBookkeepers();
})();
