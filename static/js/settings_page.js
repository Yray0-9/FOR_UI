(function () {
    const config = window.SafeBooksSettingsConfig || {};
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

    const themeButtons = Array.from(document.querySelectorAll("[data-theme-value]"));
    const followSystemToggle = document.getElementById("settingsFollowSystemToggle");
    const themeStatus = document.getElementById("settingsThemeStatus");
    const applyThemeButton = document.getElementById("settingsApplyThemeButton");

    const plannedFeatureButtons = Array.from(document.querySelectorAll("[data-planned-feature]"));

    const settingsSections = Array.from(document.querySelectorAll("[data-settings-section]"));
    const settingsNavLinks = Array.from(document.querySelectorAll(".settings-nav-link"));

    if (!body || !uiToastContainer || !settingsSections.length) {
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

    const markSectionDirty = (section) => {
        if (!section) {
            return;
        }

        const saveButton = section.querySelector("[data-settings-save]");
        const status = section.querySelector("[data-settings-status]");
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

        const saveButton = section.querySelector("[data-settings-save]");
        const status = section.querySelector("[data-settings-status]");
        if (saveButton) {
            saveButton.disabled = true;
        }
        if (status) {
            status.textContent = "Saved";
        }
    };

    const bindSectionInputs = () => {
        settingsSections.forEach((section) => {
            const inputs = Array.from(section.querySelectorAll("input, select, textarea"));
            inputs.forEach((input) => {
                input.addEventListener("input", () => markSectionDirty(section));
                input.addEventListener("change", () => markSectionDirty(section));
            });

            const saveButton = section.querySelector("[data-settings-save]");
            if (!saveButton) {
                return;
            }

            if (saveButton.hasAttribute("data-theme-save")) {
                return;
            }

            saveButton.addEventListener("click", () => {
                if (section instanceof HTMLFormElement && !section.checkValidity()) {
                    section.reportValidity();
                    return;
                }

                resetSectionDirty(section);
                showToast("Settings saved.", "success");
            });
        });
    };

    let pendingTheme = "light";
    let pendingFollowSystem = false;

    const getStoredThemeState = () => {
        if (shared && typeof shared.getThemePreference === "function") {
            return shared.getThemePreference();
        }

        return {
            theme: "light",
            followSystem: false,
        };
    };

    const applyThemeStateToUI = (themeValue, followSystemValue) => {
        themeButtons.forEach((button) => {
            const value = String(button.dataset.themeValue || "light");
            const isActive = value === themeValue;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        });

        if (followSystemToggle) {
            followSystemToggle.checked = Boolean(followSystemValue);
        }

        if (themeStatus) {
            if (followSystemValue) {
                themeStatus.textContent = "Following system appearance.";
            } else {
                themeStatus.textContent = `Theme set to ${themeValue === "dark" ? "Dark" : "Light"}.`;
            }
        }
    };

    const syncThemeState = () => {
        const storedState = getStoredThemeState();
        pendingTheme = storedState.theme || "light";
        pendingFollowSystem = Boolean(storedState.followSystem);
        applyThemeStateToUI(pendingTheme, pendingFollowSystem);
    };

    const handleThemeSave = () => {
        if (shared && typeof shared.setThemePreference === "function") {
            shared.setThemePreference(pendingTheme, pendingFollowSystem);
        }
        showToast("Theme updated.", "success");
        const appearanceSection = document.getElementById("settingsAppearance");
        resetSectionDirty(appearanceSection);
    };

    const bindThemeControls = () => {
        themeButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const value = String(button.dataset.themeValue || "light");
                pendingTheme = value === "dark" ? "dark" : "light";
                applyThemeStateToUI(pendingTheme, pendingFollowSystem);
                const appearanceSection = document.getElementById("settingsAppearance");
                markSectionDirty(appearanceSection);
            });
        });

        if (followSystemToggle) {
            followSystemToggle.addEventListener("change", () => {
                pendingFollowSystem = Boolean(followSystemToggle.checked);
                applyThemeStateToUI(pendingTheme, pendingFollowSystem);
                const appearanceSection = document.getElementById("settingsAppearance");
                markSectionDirty(appearanceSection);
            });
        }

        if (applyThemeButton) {
            applyThemeButton.addEventListener("click", () => {
                handleThemeSave();
            });
        }
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

    const bindSettingsScrollSpy = () => {
        if (!settingsNavLinks.length || !settingsSections.length) {
            return;
        }

        const sectionById = settingsSections
            .filter((section) => Boolean(section.id))
            .map((section) => ({
                id: section.id,
                element: section,
            }));

        if (!sectionById.length) {
            return;
        }

        const navById = new Map(
            settingsNavLinks
                .map((link) => {
                    const href = String(link.getAttribute("href") || "").trim();
                    if (!href.startsWith("#")) {
                        return null;
                    }
                    return [href.slice(1), link];
                })
                .filter(Boolean)
        );

        const setActiveLink = (targetId) => {
            settingsNavLinks.forEach((link) => {
                const href = String(link.getAttribute("href") || "").trim();
                const linkTarget = href.startsWith("#") ? href.slice(1) : "";
                const isActive = linkTarget === targetId;
                link.classList.toggle("is-active", isActive);
                if (isActive) {
                    link.setAttribute("aria-current", "true");
                } else {
                    link.removeAttribute("aria-current");
                }
            });
        };

        let pendingAnimationFrame = null;
        const scrollOffset = 160;

        const updateActiveFromScroll = () => {
            const scrollPosition = window.scrollY + scrollOffset;
            let activeId = sectionById[0].id;

            sectionById.forEach((section) => {
                if (section.element.offsetTop <= scrollPosition) {
                    activeId = section.id;
                }
            });

            setActiveLink(activeId);
        };

        const scheduleScrollUpdate = () => {
            if (pendingAnimationFrame) {
                return;
            }
            pendingAnimationFrame = window.requestAnimationFrame(() => {
                pendingAnimationFrame = null;
                updateActiveFromScroll();
            });
        };

        settingsNavLinks.forEach((link) => {
            link.addEventListener("click", () => {
                const href = String(link.getAttribute("href") || "").trim();
                const targetId = href.startsWith("#") ? href.slice(1) : "";
                if (targetId && navById.has(targetId)) {
                    setActiveLink(targetId);
                }
            });
        });

        window.addEventListener("scroll", scheduleScrollUpdate, { passive: true });
        window.addEventListener("resize", scheduleScrollUpdate);
        updateActiveFromScroll();
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

    const initializeSettingsPage = () => {
        sidebarState.restoreDesktopState();
        hydrateHeaderUser();

        if (shared && typeof shared.applyStoredTheme === "function") {
            shared.applyStoredTheme();
        }

        bindSectionInputs();
        bindThemeControls();
        bindPlannedFeatures();
        bindSettingsScrollSpy();
        bindHeaderActions();
        syncThemeState();

        window.addEventListener("resize", () => {
            sidebarState.closeMobileSidebar();
            sidebarState.restoreDesktopState();
        });
    };

    initializeSettingsPage();
})();
