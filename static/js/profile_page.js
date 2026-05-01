(function () {
    const config = window.SafeBooksProfileConfig || {};
    const urls = config.urls || {};
    const shared = window.SafeBooksShared || null;

    const AUTH_USER_KEY = String(config.authUserKey || "safebooks.authUser");
    const LOGIN_WELCOME_KEY = String(config.loginWelcomeKey || "safebooks.loginWelcome");
    const SIDEBAR_STATE_KEY = String(config.sidebarStateKey || "safebooks.sidebarCollapsed");
    const DESKTOP_QUERY = String(config.desktopQuery || "(min-width: 992px)");

    const body = document.body;
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarCollapseToggle = document.getElementById("sidebarCollapseToggle");
    const sidebarCollapseIcon = document.getElementById("sidebarCollapseIcon");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");

    const dashboardUserAvatar = document.getElementById("dashboardUserAvatar");
    const dashboardUserName = document.getElementById("dashboardUserName");
    const dashboardProfileAction = document.getElementById("dashboardProfileAction");
    const dashboardLogoutAction = document.getElementById("dashboardLogoutAction");

    const uiToastContainer = document.getElementById("uiToastContainer");

    const profileDisplayName = document.getElementById("profileDisplayName");
    const profileDisplayEmail = document.getElementById("profileDisplayEmail");
    const profileAvatar = document.getElementById("profileAvatar");

    const profileCompletionValue = document.getElementById("profileCompletionValue");
    const profileCompletionTrack = document.getElementById("profileCompletionTrack");
    const profileCompletionBar = document.getElementById("profileCompletionBar");

    const profileSections = Array.from(document.querySelectorAll("[data-profile-section]"));
    const profileTrackInputs = Array.from(document.querySelectorAll("[data-profile-track]"));

    const scrollTargets = Array.from(document.querySelectorAll("[data-scroll-target]"));
    const plannedFeatureButtons = Array.from(document.querySelectorAll("[data-planned-feature]"));

    if (!body || !uiToastContainer) {
        return;
    }

    window.setTimeout(() => {
        if (body.classList.contains("skeleton-active") && !body.classList.contains("skeleton-loaded")) {
            body.classList.remove("skeleton-active");
            body.classList.add("skeleton-loaded");
        }
    }, 1800);

    const sidebarState = shared && typeof shared.initializeSidebarBehavior === "function"
        ? shared.initializeSidebarBehavior({
            bodyElement: body,
            sidebarToggle,
            sidebarCollapseToggle,
            sidebarCollapseIcon,
            sidebarBackdrop,
            storageKey: SIDEBAR_STATE_KEY,
            desktopQuery: DESKTOP_QUERY,
        })
        : {
            closeMobileSidebar: () => {},
            restoreDesktopState: () => {},
        };

    const showToast = (message, variantClass = "") => {
        if (!shared || typeof shared.showToast !== "function") {
            return;
        }

        shared.showToast(uiToastContainer, message, variantClass, {
            delay: 2800,
        });
    };

    const hydrateHeaderUser = () => {
        if (!shared || typeof shared.hydrateHeaderUser !== "function") {
            return;
        }

        shared.hydrateHeaderUser({
            avatarElement: dashboardUserAvatar,
            nameElement: dashboardUserName,
            authUserKey: AUTH_USER_KEY,
            defaultName: String(config.defaultName || "Bookkeeper User"),
            defaultInitials: String(config.defaultInitials || "SB"),
        });
    };

    const logoutCurrentUser = async () => {
        if (!shared || typeof shared.logoutCurrentUser !== "function") {
            return String(urls.loginPage || "/login/");
        }

        return shared.logoutCurrentUser({
            logoutUrl: String(urls.logoutApi || ""),
            loginUrl: String(urls.loginPage || "/login/"),
            authUserKey: AUTH_USER_KEY,
            loginWelcomeKey: LOGIN_WELCOME_KEY,
        });
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

    const getAuthUser = () => {
        if (!AUTH_USER_KEY) {
            return null;
        }

        try {
            const rawValue = window.localStorage.getItem(AUTH_USER_KEY) || "";
            if (!rawValue) {
                return null;
            }

            const parsedValue = JSON.parse(rawValue);
            if (!parsedValue || typeof parsedValue !== "object") {
                return null;
            }

            return parsedValue;
        } catch (error) {
            return null;
        }
    };

    const hydrateProfileIdentity = () => {
        const authUser = getAuthUser();
        const displayName = authUser && authUser.full_name ? String(authUser.full_name).trim() : String(config.defaultName || "Bookkeeper User");
        const displayEmail = authUser && authUser.email ? String(authUser.email).trim() : "name@company.com";
        const initials = resolveInitials(displayName, String(config.defaultInitials || "SB"));

        if (profileDisplayName) {
            profileDisplayName.textContent = displayName;
        }

        if (profileDisplayEmail) {
            profileDisplayEmail.textContent = displayEmail;
        }

        if (profileAvatar) {
            profileAvatar.textContent = initials;
        }
    };

    const markSectionDirty = (section) => {
        if (!section) {
            return;
        }

        const saveButton = section.querySelector("[data-profile-save]");
        const status = section.querySelector("[data-profile-status]");
        if (saveButton) {
            saveButton.disabled = false;
        }
        if (status) {
            status.textContent = "Unsaved changes";
        }
    };

    const resetSectionDirty = (section) => {
        if (!section) {
            return;
        }

        const saveButton = section.querySelector("[data-profile-save]");
        const status = section.querySelector("[data-profile-status]");
        if (saveButton) {
            saveButton.disabled = true;
        }
        if (status) {
            status.textContent = "Saved";
        }
    };

    const isInputFilled = (input) => {
        if (!input) {
            return false;
        }

        if (input.type === "checkbox" || input.type === "radio") {
            return input.checked;
        }

        return Boolean(String(input.value || "").trim());
    };

    const updateCompletion = () => {
        if (!profileCompletionValue || !profileCompletionBar || !profileCompletionTrack || !profileTrackInputs.length) {
            return;
        }

        const filledCount = profileTrackInputs.filter((input) => isInputFilled(input)).length;
        const completion = Math.round((filledCount / profileTrackInputs.length) * 100);
        const safeCompletion = Number.isFinite(completion) ? completion : 0;

        profileCompletionValue.textContent = `${safeCompletion}%`;
        profileCompletionBar.style.width = `${safeCompletion}%`;
        profileCompletionTrack.setAttribute("aria-valuenow", String(safeCompletion));
    };

    const bindSectionInputs = () => {
        profileSections.forEach((section) => {
            const inputs = Array.from(section.querySelectorAll("input, select, textarea"));
            inputs.forEach((input) => {
                input.addEventListener("input", () => {
                    markSectionDirty(section);
                    updateCompletion();
                });
                input.addEventListener("change", () => {
                    markSectionDirty(section);
                    updateCompletion();
                });
            });

            const saveButton = section.querySelector("[data-profile-save]");
            if (!saveButton) {
                return;
            }

            saveButton.addEventListener("click", () => {
                if (section instanceof HTMLFormElement && !section.checkValidity()) {
                    section.reportValidity();
                    return;
                }

                resetSectionDirty(section);
                showToast("Profile updated.", "success");
            });
        });
    };

    const bindScrollTargets = () => {
        scrollTargets.forEach((button) => {
            button.addEventListener("click", () => {
                const targetSelector = String(button.dataset.scrollTarget || "").trim();
                if (!targetSelector) {
                    return;
                }

                const target = document.querySelector(targetSelector);
                if (!target) {
                    return;
                }

                target.scrollIntoView({ behavior: "smooth", block: "start" });
                if (target.hasAttribute("tabindex")) {
                    target.focus({ preventScroll: true });
                }
            });
        });
    };

    const bindPlannedFeatures = () => {
        plannedFeatureButtons.forEach((button) => {
            button.addEventListener("click", (event) => {
                event.preventDefault();
                const label = String(button.dataset.plannedFeature || "This feature").trim();
                showToast(`${label} is planned and will be available soon.`);
            });
        });
    };

    const bindHeaderActions = () => {
        if (dashboardProfileAction) {
            dashboardProfileAction.addEventListener("click", () => {
                window.location.assign(String(urls.profilePage || "/profile/"));
            });
        }

        if (dashboardLogoutAction) {
            dashboardLogoutAction.addEventListener("click", async () => {
                dashboardLogoutAction.disabled = true;

                try {
                    const redirectUrl = await logoutCurrentUser();
                    showToast("Logging out...", "success");
                    window.location.assign(redirectUrl);
                } finally {
                    dashboardLogoutAction.disabled = false;
                }
            });
        }
    };

    const initializeProfilePage = () => {
        sidebarState.restoreDesktopState();
        hydrateHeaderUser();

        if (shared && typeof shared.applyStoredTheme === "function") {
            shared.applyStoredTheme();
        }

        hydrateProfileIdentity();
        bindSectionInputs();
        bindScrollTargets();
        bindPlannedFeatures();
        bindHeaderActions();
        updateCompletion();

        window.addEventListener("resize", () => {
            sidebarState.closeMobileSidebar();
            sidebarState.restoreDesktopState();
        });
    };

    initializeProfilePage();
})();
