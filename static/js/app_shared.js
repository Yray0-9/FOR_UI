(function () {
    const parseJsonSafe = async (response) => {
        try {
            return await response.json();
        } catch (error) {
            return null;
        }
    };

    const getCookieValue = (cookieName) => {
        const source = document.cookie || "";
        const parts = source.split(";");

        for (const part of parts) {
            const trimmed = part.trim();
            if (!trimmed.startsWith(`${cookieName}=`)) {
                continue;
            }
            return decodeURIComponent(trimmed.substring(cookieName.length + 1));
        }

        return "";
    };

    const getStoredAuthUser = (authUserKey) => {
        try {
            const rawValue = window.localStorage.getItem(authUserKey) || "";
            if (!rawValue) {
                return null;
            }

            const parsedValue = JSON.parse(rawValue);
            if (!parsedValue || typeof parsedValue !== "object") {
                return null;
            }

            return parsedValue;
        } catch (storageError) {
            return null;
        }
    };

    const resolveDisplayName = (user, fallbackName = "Bookkeeper User") => {
        const fullName = user && typeof user.full_name === "string" ? user.full_name.trim() : "";
        if (fullName) {
            return fullName;
        }

        const username = user && typeof user.username === "string" ? user.username.trim() : "";
        if (username) {
            return username;
        }

        const email = user && typeof user.email === "string" ? user.email.trim() : "";
        if (email && email.includes("@")) {
            return email.split("@")[0];
        }

        return fallbackName;
    };

    const resolveInitials = (name, fallbackInitials = "SB") => {
        const nameParts = String(name || "").trim().split(/\s+/).filter(Boolean);

        if (!nameParts.length) {
            return fallbackInitials;
        }

        if (nameParts.length === 1) {
            return nameParts[0].slice(0, 2).toUpperCase();
        }

        return `${nameParts[0][0]}${nameParts[1][0]}`.toUpperCase();
    };

    const hydrateHeaderUser = (options) => {
        const config = options || {};
        const authUserKey = String(config.authUserKey || "").trim();
        const defaultName = String(config.defaultName || "Bookkeeper User");
        const defaultInitials = String(config.defaultInitials || "SB");
        const nameElement = config.nameElement || null;
        const avatarElement = config.avatarElement || null;

        if (!authUserKey) {
            if (nameElement) {
                nameElement.textContent = defaultName;
            }
            if (avatarElement) {
                avatarElement.textContent = defaultInitials;
            }
            return;
        }

        const user = getStoredAuthUser(authUserKey);
        const displayName = resolveDisplayName(user, defaultName);

        if (nameElement) {
            nameElement.textContent = displayName;
        }

        if (avatarElement) {
            avatarElement.textContent = resolveInitials(displayName, defaultInitials);
        }
    };

    const escapeHtml = (value) => {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
    };

    const showToast = (toastContainer, message, variantClass = "", options = {}) => {
        if (!toastContainer) {
            return;
        }

        const delay = Number.isFinite(options.delay) ? options.delay : 2800;
        const toastElement = document.createElement("div");
        toastElement.className = `toast safebooks-toast ${variantClass}`.trim();
        toastElement.setAttribute("role", "status");
        toastElement.setAttribute("aria-live", "polite");
        toastElement.setAttribute("aria-atomic", "true");
        toastElement.innerHTML = `<div class="toast-body">${escapeHtml(message || "Action completed.")}</div>`;
        toastContainer.appendChild(toastElement);

        if (window.bootstrap && window.bootstrap.Toast) {
            toastElement.addEventListener("hidden.bs.toast", () => {
                toastElement.remove();
            });

            const toastInstance = new window.bootstrap.Toast(toastElement, {
                delay,
                autohide: true,
            });
            toastInstance.show();
            return;
        }

        window.setTimeout(() => {
            toastElement.remove();
        }, delay);
    };

    const logoutCurrentUser = async (options) => {
        const config = options || {};
        const logoutUrl = String(config.logoutUrl || "").trim();
        let redirectUrl = String(config.loginUrl || "").trim() || "/login/";

        const csrfToken = getCookieValue("csrftoken");
        const headers = {};
        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken;
        }

        if (logoutUrl) {
            try {
                const response = await fetch(logoutUrl, {
                    method: "POST",
                    headers,
                    credentials: "same-origin",
                });

                const payload = await parseJsonSafe(response);
                if (payload && typeof payload.redirect_url === "string" && payload.redirect_url.trim()) {
                    redirectUrl = payload.redirect_url.trim();
                }
            } catch (requestError) {
                // Keep local cleanup + redirect behavior even on network failures.
            }
        }

        try {
            if (config.authUserKey) {
                window.localStorage.removeItem(config.authUserKey);
            }
            if (config.loginWelcomeKey) {
                window.sessionStorage.removeItem(config.loginWelcomeKey);
            }
        } catch (storageError) {
            // Ignore storage errors to avoid blocking logout flow.
        }

        return redirectUrl;
    };

    const THEME_STORAGE_KEY = "safebooks.ui.theme";
    const THEME_FOLLOW_KEY = "safebooks.ui.followSystem";
    const VALID_THEMES = new Set(["light", "dark"]);
    let systemThemeMedia = null;
    let systemThemeListener = null;

    const normalizeTheme = (value) => {
        return VALID_THEMES.has(value) ? value : "light";
    };

    const readThemePreference = () => {
        let theme = "light";
        let followSystem = false;

        try {
            const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
            const storedFollow = window.localStorage.getItem(THEME_FOLLOW_KEY);
            theme = normalizeTheme(String(storedTheme || "light"));
            followSystem = storedFollow === "1";
        } catch (error) {
            theme = "light";
            followSystem = false;
        }

        return { theme, followSystem };
    };

    const resolveSystemTheme = () => {
        if (!window.matchMedia) {
            return "light";
        }

        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };

    const applyThemeClass = (themeValue) => {
        const theme = normalizeTheme(themeValue);
        const pageBody = document.body;
        if (!pageBody) {
            return theme;
        }

        pageBody.classList.remove("theme-light", "theme-dark");
        pageBody.classList.add(`theme-${theme}`);
        return theme;
    };

    const syncSystemThemeListener = (enabled) => {
        if (!window.matchMedia) {
            return;
        }

        if (!systemThemeMedia) {
            systemThemeMedia = window.matchMedia("(prefers-color-scheme: dark)");
        }

        if (enabled && !systemThemeListener) {
            systemThemeListener = (event) => {
                applyThemeClass(event.matches ? "dark" : "light");
            };
            systemThemeMedia.addEventListener("change", systemThemeListener);
        } else if (!enabled && systemThemeListener) {
            systemThemeMedia.removeEventListener("change", systemThemeListener);
            systemThemeListener = null;
        }
    };

    const applyStoredTheme = () => {
        const preference = readThemePreference();
        const resolvedTheme = preference.followSystem ? resolveSystemTheme() : preference.theme;
        applyThemeClass(resolvedTheme);
        syncSystemThemeListener(preference.followSystem);
        return {
            theme: resolvedTheme,
            followSystem: preference.followSystem,
        };
    };

    const setThemePreference = (themeValue, followSystemValue) => {
        const theme = normalizeTheme(themeValue);
        const followSystem = Boolean(followSystemValue);

        try {
            window.localStorage.setItem(THEME_STORAGE_KEY, theme);
            window.localStorage.setItem(THEME_FOLLOW_KEY, followSystem ? "1" : "0");
        } catch (error) {
            // Ignore storage errors to keep UI responsive.
        }

        return applyStoredTheme();
    };

    const getThemePreference = () => {
        return readThemePreference();
    };

    const initializeSidebarBehavior = (options = {}) => {
        const bodyElement = options.bodyElement || document.body;
        const sidebarToggle = options.sidebarToggle || null;
        const sidebarCollapseToggle = options.sidebarCollapseToggle || null;
        const sidebarCollapseIcon = options.sidebarCollapseIcon || null;
        const sidebarBackdrop = options.sidebarBackdrop || null;
        const storageKey = String(options.storageKey || "safebooks.sidebarCollapsed").trim() || "safebooks.sidebarCollapsed";
        const desktopQuery = String(options.desktopQuery || "(min-width: 992px)").trim() || "(min-width: 992px)";

        const noopState = {
            closeMobileSidebar: () => {},
            restoreDesktopState: () => {},
            toggleSidebarCollapsed: () => {},
        };

        if (!bodyElement) {
            return noopState;
        }

        const isDesktop = () => window.matchMedia(desktopQuery).matches;

        const closeMobileSidebar = () => {
            bodyElement.classList.remove("sidebar-open");
        };

        const syncSidebarCollapseUI = () => {
            const isCollapsed = bodyElement.classList.contains("sidebar-collapsed");

            if (sidebarCollapseToggle) {
                sidebarCollapseToggle.setAttribute("aria-expanded", String(!isCollapsed));
                sidebarCollapseToggle.setAttribute("aria-label", isCollapsed ? "Expand sidebar" : "Collapse sidebar");
            }

            if (sidebarCollapseIcon) {
                sidebarCollapseIcon.classList.toggle("bi-layout-sidebar-inset", !isCollapsed);
                sidebarCollapseIcon.classList.toggle("bi-layout-sidebar-inset-reverse", isCollapsed);
            }
        };

        const persistCollapsedState = (collapsed) => {
            try {
                window.localStorage.setItem(storageKey, collapsed ? "1" : "0");
            } catch (error) {
                // Ignore storage access issues and keep interaction responsive.
            }
        };

        const getStoredCollapsedState = () => {
            try {
                return window.localStorage.getItem(storageKey) === "1";
            } catch (error) {
                return false;
            }
        };

        const setSidebarCollapsed = (collapsed, persistState = true) => {
            if (!isDesktop()) {
                bodyElement.classList.remove("sidebar-collapsed");
                syncSidebarCollapseUI();
                return;
            }

            bodyElement.classList.toggle("sidebar-collapsed", collapsed);
            syncSidebarCollapseUI();

            if (persistState) {
                persistCollapsedState(collapsed);
            }
        };

        const toggleSidebarCollapsed = () => {
            const shouldCollapse = !bodyElement.classList.contains("sidebar-collapsed");
            setSidebarCollapsed(shouldCollapse, true);
        };

        const restoreDesktopState = () => {
            if (isDesktop()) {
                setSidebarCollapsed(getStoredCollapsedState(), false);
            } else {
                bodyElement.classList.remove("sidebar-collapsed");
                syncSidebarCollapseUI();
            }
        };

        restoreDesktopState();

        if (sidebarToggle) {
            sidebarToggle.addEventListener("click", (event) => {
                event.preventDefault();

                if (isDesktop()) {
                    toggleSidebarCollapsed();
                    return;
                }

                bodyElement.classList.toggle("sidebar-open");
            });
        }

        if (sidebarCollapseToggle) {
            sidebarCollapseToggle.addEventListener("click", (event) => {
                event.preventDefault();
                toggleSidebarCollapsed();
            });
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener("click", closeMobileSidebar);
        }

        return {
            closeMobileSidebar,
            restoreDesktopState,
            toggleSidebarCollapsed,
        };
    };

    applyStoredTheme();

    window.SafeBooksShared = {
        parseJsonSafe,
        getCookieValue,
        hydrateHeaderUser,
        showToast,
        logoutCurrentUser,
        applyStoredTheme,
        setThemePreference,
        getThemePreference,
        initializeSidebarBehavior,
    };
})();