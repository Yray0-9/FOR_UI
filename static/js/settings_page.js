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
    const themeSwatches = Array.from(document.querySelectorAll("[data-theme-swatch]"));
    const themeStatus = document.getElementById("settingsThemeStatus");
    const applyThemeButton = document.getElementById("settingsApplyThemeButton");
    const appearanceSection = document.getElementById("settingsAppearance");

    const defaultsSection = document.getElementById("settingsDefaults");
    const defaultScopeSelect = document.getElementById("settingsDefaultScope");
    const defaultReportSelect = document.getElementById("settingsDefaultReport");
    const defaultRangeSelect = document.getElementById("settingsDefaultRange");
    const defaultRangeFromInput = document.getElementById("settingsDefaultRangeFrom");
    const defaultRangeToInput = document.getElementById("settingsDefaultRangeTo");
    const customRangeFields = Array.from(document.querySelectorAll("[data-custom-range-field]"));
    const defaultsSaveButton = defaultsSection
        ? defaultsSection.querySelector("[data-settings-defaults-save]")
        : null;

    const plannedFeatureButtons = Array.from(document.querySelectorAll("[data-planned-feature]"));

    const settingsSections = Array.from(document.querySelectorAll("[data-settings-section]"));
    const settingsNavLinks = Array.from(document.querySelectorAll(".settings-nav-link"));

    const workspaceDefaultsUrl = String(urls.workspaceDefaultsApi || "");
    const securityChangePasswordUrl = String(urls.securityChangePasswordApi || "");
    const securityLoginAlertsUrl = String(urls.securityLoginAlertsApi || "");

    const changePasswordForm = document.getElementById("settingsChangePasswordForm");
    const changePasswordStatus = document.getElementById("settingsChangePasswordStatus");
    const changePasswordButton = document.getElementById("settingsChangePasswordButton");
    const changePasswordModalElement = document.getElementById("settingsChangePasswordModal");
    const currentPasswordInput = document.getElementById("settingsCurrentPassword");
    const newPasswordInput = document.getElementById("settingsNewPassword");
    const confirmPasswordInput = document.getElementById("settingsConfirmPassword");
    const passwordRulesContainer = document.getElementById("settingsPasswordRules");
    const loginAlertsPanel = document.getElementById("settingsLoginAlertsPanel");
    const loginAlertsToggle = document.getElementById("settingsLoginAlertsToggle");
    const loginAlertsStatus = document.getElementById("settingsLoginAlertsStatus");
    const loginAlertsFeedback = document.getElementById("settingsLoginAlertsFeedback");

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

    const parseJsonSafe = (response) => {
        if (shared && typeof shared.parseJsonSafe === "function") {
            return shared.parseJsonSafe(response);
        }

        return response
            .json()
            .catch(() => null);
    };

    const getCookieValue = (cookieName) => {
        if (shared && typeof shared.getCookieValue === "function") {
            return shared.getCookieValue(cookieName);
        }

        return "";
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

    const setSaveButtonState = (saveButton, isEnabled) => {
        if (!saveButton) {
            return;
        }

        saveButton.disabled = !isEnabled;
        if (saveButton.hasAttribute("aria-disabled")) {
            saveButton.setAttribute("aria-disabled", String(!isEnabled));
        }
    };

    const markSectionDirty = (section) => {
        if (!section) {
            return;
        }

        const saveButton = section.querySelector("[data-settings-save]");
        const status = section.querySelector("[data-settings-status]");
        if (saveButton) {
            setSaveButtonState(saveButton, true);
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
            setSaveButtonState(saveButton, false);
        }
        if (status) {
            status.textContent = "Saved";
        }
    };

    const setInlineStatus = (element, message, variant) => {
        if (!element) {
            return;
        }

        element.textContent = message;
        element.classList.remove("is-success", "is-warning", "is-danger");
        if (variant) {
            element.classList.add(`is-${variant}`);
        }
    };

    const clearInlineStatus = (element) => {
        if (!element) {
            return;
        }

        element.textContent = "";
        element.classList.remove("is-success", "is-warning", "is-danger");
    };

    const setButtonLoading = (button, isLoading, loadingLabel) => {
        if (!button) {
            return;
        }

        if (!button.dataset.defaultLabel) {
            button.dataset.defaultLabel = button.textContent || "";
        }

        if (isLoading) {
            button.dataset.wasDisabled = button.disabled ? "true" : "false";
            if (button.hasAttribute("aria-disabled")) {
                button.dataset.wasAriaDisabled = button.getAttribute("aria-disabled") || "false";
                button.setAttribute("aria-disabled", "true");
            }
            button.disabled = true;
        } else {
            const wasDisabled = button.dataset.wasDisabled === "true";
            if (button.hasAttribute("aria-disabled") && button.dataset.wasAriaDisabled) {
                button.setAttribute("aria-disabled", button.dataset.wasAriaDisabled);
            }
            button.disabled = wasDisabled;
            delete button.dataset.wasDisabled;
            delete button.dataset.wasAriaDisabled;
        }

        button.textContent = isLoading
            ? String(loadingLabel || "Working...")
            : button.dataset.defaultLabel;
    };

    const postJson = async (url, payload) => {
        const csrfToken = getCookieValue("csrftoken");
        const headers = {
            Accept: "application/json",
            "Content-Type": "application/json",
        };
        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken;
        }

        return fetch(url, {
            method: "POST",
            headers,
            credentials: "same-origin",
            body: JSON.stringify(payload || {}),
        });
    };

    const getModalInstance = (element) => {
        if (!element || !window.bootstrap || !window.bootstrap.Modal) {
            return null;
        }

        if (typeof window.bootstrap.Modal.getOrCreateInstance === "function") {
            return window.bootstrap.Modal.getOrCreateInstance(element);
        }

        return new window.bootstrap.Modal(element);
    };

    let changePasswordModal = null;

    const getPasswordRequirementState = () => {
        const currentValue = currentPasswordInput ? currentPasswordInput.value : "";
        const newValue = newPasswordInput ? newPasswordInput.value : "";
        const confirmValue = confirmPasswordInput ? confirmPasswordInput.value : "";

        const state = {
            length: newValue.length >= 8,
            uppercase: /[A-Z]/.test(newValue),
            lowercase: /[a-z]/.test(newValue),
            number: /\d/.test(newValue),
            symbol: /[^A-Za-z0-9]/.test(newValue),
            match: Boolean(newValue) && newValue === confirmValue,
            hasCurrent: Boolean(currentValue),
            hasConfirm: Boolean(confirmValue),
        };

        state.isDifferent = !currentValue || !newValue || currentValue !== newValue;
        state.isValid = state.length && state.uppercase && state.lowercase
            && state.number && state.symbol && state.match;

        return state;
    };

    const updatePasswordRequirementsUi = () => {
        const state = getPasswordRequirementState();

        if (passwordRulesContainer) {
            const ruleElements = passwordRulesContainer.querySelectorAll("[data-rule]");
            ruleElements.forEach((ruleElement) => {
                const ruleName = ruleElement.getAttribute("data-rule");
                const isValid = Boolean(ruleName && state[ruleName]);
                ruleElement.classList.toggle("is-valid", isValid);
            });
        }

        return state;
    };

    const bindPasswordToggles = () => {
        document.querySelectorAll("[data-password-toggle-target]").forEach((toggleButton) => {
            toggleButton.addEventListener("click", () => {
                const targetId = toggleButton.getAttribute("data-password-toggle-target");
                const inputElement = targetId ? document.getElementById(targetId) : null;
                if (!(inputElement instanceof HTMLInputElement)) {
                    return;
                }

                const shouldShow = inputElement.type === "password";
                inputElement.type = shouldShow ? "text" : "password";

                const iconElement = toggleButton.querySelector("i");
                if (iconElement) {
                    iconElement.classList.toggle("bi-eye", !shouldShow);
                    iconElement.classList.toggle("bi-eye-slash", shouldShow);
                }

                toggleButton.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
            });
        });
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

            if (saveButton.hasAttribute("data-theme-save")
                || saveButton.hasAttribute("data-settings-defaults-save")) {
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
    let storedTheme = "light";

    const getStoredThemeState = () => {
        if (shared && typeof shared.getThemePreference === "function") {
            const preference = shared.getThemePreference();
            return {
                theme: preference.theme || "light",
                followSystem: Boolean(preference.followSystem),
            };
        }

        return {
            theme: "light",
            followSystem: false,
        };
    };

    const resolveThemeFromBody = () => {
        if (!body) {
            return "light";
        }

        return body.classList.contains("theme-dark") ? "dark" : "light";
    };

    const applyThemeStateToUI = (themeValue) => {
        themeButtons.forEach((button) => {
            const value = String(button.dataset.themeValue || "light");
            const isActive = value === themeValue;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-pressed", String(isActive));
        });

        themeSwatches.forEach((swatch) => {
            const value = String(swatch.dataset.themeSwatch || "").trim();
            swatch.classList.toggle("is-active", value === themeValue);
        });

        if (themeStatus) {
            themeStatus.textContent = `Theme set to ${themeValue === "dark" ? "Dark" : "Light"}.`;
        }
    };

    const updateAppearanceDirtyState = () => {
        if (!appearanceSection) {
            return;
        }

        if (pendingTheme === storedTheme) {
            resetSectionDirty(appearanceSection);
        } else {
            markSectionDirty(appearanceSection);
        }
    };

    const syncThemeState = () => {
        const storedState = getStoredThemeState();
        storedTheme = storedState.theme || "light";

        if (storedState.followSystem) {
            const resolvedTheme = resolveThemeFromBody();
            storedTheme = resolvedTheme;
            if (shared && typeof shared.setThemePreference === "function") {
                shared.setThemePreference(resolvedTheme, false);
            }
        }

        pendingTheme = storedTheme;
        applyThemeStateToUI(pendingTheme);
        updateAppearanceDirtyState();
    };

    const handleThemeSave = () => {
        if (shared && typeof shared.setThemePreference === "function") {
            shared.setThemePreference(pendingTheme, false);
        }
        showToast("Theme updated.", "success");
        syncThemeState();
    };

    const bindThemeControls = () => {
        const setPendingTheme = (nextValue) => {
            const value = String(nextValue || "light");
            pendingTheme = value === "dark" ? "dark" : "light";
            applyThemeStateToUI(pendingTheme);
            updateAppearanceDirtyState();
        };

        themeButtons.forEach((button) => {
            button.addEventListener("click", () => {
                setPendingTheme(button.dataset.themeValue || "light");
            });
        });

        themeSwatches.forEach((swatch) => {
            swatch.addEventListener("click", () => {
                setPendingTheme(swatch.dataset.themeSwatch || "light");
            });
        });

        if (applyThemeButton) {
            applyThemeButton.addEventListener("click", () => {
                handleThemeSave();
            });
        }
    };

    const setSelectValue = (selectElement, nextValue) => {
        if (!selectElement) {
            return;
        }

        const value = String(nextValue || "").trim();
        if (!value) {
            return;
        }

        const optionExists = Array.from(selectElement.options)
            .some((optionItem) => optionItem.value === value);
        if (optionExists) {
            selectElement.value = value;
        }
    };

    const setCustomRangeVisibility = (isCustomRange) => {
        customRangeFields.forEach((field) => {
            field.hidden = !isCustomRange;
        });
    };

    const setDateValue = (inputElement, nextValue) => {
        if (!inputElement) {
            return;
        }

        inputElement.value = String(nextValue || "").trim();
    };

    const validateCustomRange = () => {
        if (!defaultRangeSelect || defaultRangeSelect.value !== "custom") {
            return "";
        }

        const fromValue = defaultRangeFromInput ? defaultRangeFromInput.value : "";
        const toValue = defaultRangeToInput ? defaultRangeToInput.value : "";

        if (!fromValue || !toValue) {
            return "Custom range requires both start and end dates.";
        }

        if (fromValue > toValue) {
            return "Custom range start must be on or before the end date.";
        }

        return "";
    };

    const applyWorkspaceDefaults = (defaults) => {
        if (!defaults || typeof defaults !== "object") {
            return;
        }

        setSelectValue(defaultScopeSelect, defaults.default_client_scope);
        setSelectValue(defaultReportSelect, defaults.default_report_type);
        setSelectValue(defaultRangeSelect, defaults.default_report_range);
        setDateValue(defaultRangeFromInput, defaults.default_report_range_from);
        setDateValue(defaultRangeToInput, defaults.default_report_range_to);
        setCustomRangeVisibility(defaultRangeSelect && defaultRangeSelect.value === "custom");
    };

    const loadWorkspaceDefaults = async () => {
        if (!workspaceDefaultsUrl || !defaultsSection) {
            return;
        }

        const status = defaultsSection.querySelector("[data-settings-status]");
        if (status) {
            status.textContent = "Loading...";
        }
        if (defaultsSaveButton) {
            defaultsSaveButton.disabled = true;
        }

        try {
            const response = await fetch(workspaceDefaultsUrl, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                credentials: "same-origin",
            });

            if (response.status === 401) {
                window.location.assign(String(urls.loginPage || "/login/"));
                return;
            }

            const payload = await parseJsonSafe(response);
            if (!response.ok || !payload || !payload.ok) {
                throw new Error(payload && payload.message ? String(payload.message) : "Unable to load workspace defaults.");
            }

            applyWorkspaceDefaults(payload.defaults);
            resetSectionDirty(defaultsSection);
        } catch (error) {
            if (status) {
                status.textContent = "Unable to load";
            }
            showToast("Workspace defaults could not be loaded.", "warning");
            if (defaultsSaveButton) {
                defaultsSaveButton.disabled = false;
            }
        } finally {
            setCustomRangeVisibility(defaultRangeSelect && defaultRangeSelect.value === "custom");
        }
    };

    const saveWorkspaceDefaults = async () => {
        if (!workspaceDefaultsUrl || !defaultsSection) {
            showToast("Workspace defaults are unavailable.", "warning");
            return;
        }

        const customRangeError = validateCustomRange();
        if (customRangeError) {
            showToast(customRangeError, "warning");
            return;
        }

        const payload = {
            default_client_scope: defaultScopeSelect ? defaultScopeSelect.value : "",
            default_report_type: defaultReportSelect ? defaultReportSelect.value : "",
            default_report_range: defaultRangeSelect ? defaultRangeSelect.value : "",
            default_report_range_from: defaultRangeFromInput ? defaultRangeFromInput.value : "",
            default_report_range_to: defaultRangeToInput ? defaultRangeToInput.value : "",
        };

        const status = defaultsSection.querySelector("[data-settings-status]");
        if (status) {
            status.textContent = "Saving...";
        }
        if (defaultsSaveButton) {
            defaultsSaveButton.disabled = true;
        }

        try {
            const csrfToken = getCookieValue("csrftoken");
            const headers = {
                Accept: "application/json",
                "Content-Type": "application/json",
            };
            if (csrfToken) {
                headers["X-CSRFToken"] = csrfToken;
            }

            const response = await fetch(workspaceDefaultsUrl, {
                method: "POST",
                headers,
                credentials: "same-origin",
                body: JSON.stringify(payload),
            });

            if (response.status === 401) {
                window.location.assign(String(urls.loginPage || "/login/"));
                return;
            }

            const result = await parseJsonSafe(response);
            if (!response.ok || !result || !result.ok) {
                const message = result && result.message
                    ? String(result.message)
                    : "Unable to save workspace defaults.";
                throw new Error(message);
            }

            applyWorkspaceDefaults(result.defaults);
            resetSectionDirty(defaultsSection);
            showToast("Workspace defaults saved.", "success");
        } catch (error) {
            if (status) {
                status.textContent = "Unsaved changes";
            }
            showToast(error && error.message ? String(error.message) : "Unable to save workspace defaults.", "danger");
            if (defaultsSaveButton) {
                defaultsSaveButton.disabled = false;
            }
        }
    };

    const bindWorkspaceDefaults = () => {
        if (!defaultsSaveButton) {
            return;
        }

        defaultsSaveButton.addEventListener("click", () => {
            saveWorkspaceDefaults();
        });

        if (defaultRangeSelect) {
            defaultRangeSelect.addEventListener("change", () => {
                setCustomRangeVisibility(defaultRangeSelect.value === "custom");
            });
        }
    };

    const isLoginAlertsEnabled = () => {
        if (!loginAlertsPanel) {
            return false;
        }

        return String(loginAlertsPanel.dataset.loginAlertsEnabled || "false") === "true";
    };

    const updateLoginAlertsUiState = (isEnabled) => {
        if (loginAlertsPanel) {
            loginAlertsPanel.dataset.loginAlertsEnabled = isEnabled ? "true" : "false";
        }

        if (loginAlertsStatus) {
            loginAlertsStatus.textContent = isEnabled ? "On" : "Off";
            loginAlertsStatus.classList.toggle("is-enabled", isEnabled);
        }

        if (loginAlertsToggle) {
            loginAlertsToggle.checked = isEnabled;
        }
    };

    const setLoginAlertsLoading = (isLoading) => {
        if (loginAlertsToggle) {
            loginAlertsToggle.disabled = isLoading;
        }
    };

    const handleLoginAlertsToggle = async (nextValue) => {
        if (!securityLoginAlertsUrl) {
            showToast("Login alerts are unavailable.", "warning");
            updateLoginAlertsUiState(isLoginAlertsEnabled());
            return;
        }

        const previousValue = isLoginAlertsEnabled();
        setLoginAlertsLoading(true);
        setInlineStatus(loginAlertsFeedback, "Saving...", "warning");

        try {
            const response = await postJson(securityLoginAlertsUrl, {
                enabled: Boolean(nextValue),
            });

            if (response.status === 401) {
                window.location.assign(String(urls.loginPage || "/login/"));
                return;
            }

            const result = await parseJsonSafe(response);
            if (!response.ok || !result || !result.ok) {
                const message = result && result.message
                    ? String(result.message)
                    : "Unable to update login alerts.";
                throw new Error(message);
            }

            updateLoginAlertsUiState(Boolean(result.login_alerts_enabled));
            setInlineStatus(loginAlertsFeedback, "Updated", "success");
            showToast("Login alerts updated.", "success");
        } catch (error) {
            updateLoginAlertsUiState(previousValue);
            setInlineStatus(loginAlertsFeedback, "Update failed", "danger");
            showToast(error && error.message ? String(error.message) : "Unable to update login alerts.", "danger");
        } finally {
            setLoginAlertsLoading(false);
        }
    };

    const resetChangePasswordInputs = () => {
        if (currentPasswordInput) {
            currentPasswordInput.value = "";
        }
        if (newPasswordInput) {
            newPasswordInput.value = "";
        }
        if (confirmPasswordInput) {
            confirmPasswordInput.value = "";
        }
        updatePasswordRequirementsUi();
    };

    const handleChangePassword = async () => {
        if (!securityChangePasswordUrl || !changePasswordForm) {
            showToast("Password updates are unavailable.", "warning");
            return;
        }

        const requirementState = updatePasswordRequirementsUi();
        if (!requirementState.hasCurrent) {
            setInlineStatus(changePasswordStatus, "Current password is required.", "danger");
            showToast("Current password is required.", "warning");
            return;
        }

        if (!requirementState.hasConfirm) {
            setInlineStatus(changePasswordStatus, "Confirm your new password.", "danger");
            showToast("Confirm your new password.", "warning");
            return;
        }

        if (!requirementState.match) {
            setInlineStatus(changePasswordStatus, "Passwords do not match.", "danger");
            showToast("Passwords do not match.", "warning");
            return;
        }

        if (!requirementState.isDifferent) {
            setInlineStatus(changePasswordStatus, "New password must be different.", "danger");
            showToast("New password must be different from the current password.", "warning");
            return;
        }

        if (!requirementState.isValid) {
            setInlineStatus(changePasswordStatus, "Password requirements not met.", "danger");
            showToast("Password requirements not met.", "warning");
            return;
        }

        if (!changePasswordForm.checkValidity()) {
            changePasswordForm.reportValidity();
            return;
        }

        const payload = {
            current_password: currentPasswordInput ? currentPasswordInput.value : "",
            new_password: newPasswordInput ? newPasswordInput.value : "",
            confirm_password: confirmPasswordInput ? confirmPasswordInput.value : "",
        };

        setButtonLoading(changePasswordButton, true, "Updating...");
        setInlineStatus(changePasswordStatus, "Saving...", "warning");

        try {
            const response = await postJson(securityChangePasswordUrl, payload);
            if (response.status === 401) {
                window.location.assign(String(urls.loginPage || "/login/"));
                return;
            }

            const result = await parseJsonSafe(response);
            if (!response.ok || !result || !result.ok) {
                const message = result && result.message
                    ? String(result.message)
                    : "Unable to update password.";
                throw new Error(message);
            }

            resetChangePasswordInputs();
            setInlineStatus(changePasswordStatus, "Updated", "success");
            showToast("Password updated successfully.", "success");
            if (changePasswordModal) {
                changePasswordModal.hide();
            }
        } catch (error) {
            setInlineStatus(changePasswordStatus, "Update failed", "danger");
            showToast(error && error.message ? String(error.message) : "Unable to update password.", "danger");
        } finally {
            setButtonLoading(changePasswordButton, false);
        }
    };

    const bindSecurityActions = () => {
        bindPasswordToggles();

        if (changePasswordModalElement) {
            changePasswordModal = getModalInstance(changePasswordModalElement);
            changePasswordModalElement.addEventListener("shown.bs.modal", () => {
                if (currentPasswordInput) {
                    currentPasswordInput.focus();
                }
                clearInlineStatus(changePasswordStatus);
                updatePasswordRequirementsUi();
            });
            changePasswordModalElement.addEventListener("hidden.bs.modal", () => {
                resetChangePasswordInputs();
                clearInlineStatus(changePasswordStatus);
            });
        }

        if (changePasswordForm) {
            changePasswordForm.addEventListener("submit", (event) => {
                event.preventDefault();
                handleChangePassword();
            });
        }

        [currentPasswordInput, newPasswordInput, confirmPasswordInput].forEach((input) => {
            if (!input) {
                return;
            }
            input.addEventListener("input", () => {
                updatePasswordRequirementsUi();
                clearInlineStatus(changePasswordStatus);
            });
        });

        if (loginAlertsToggle) {
            loginAlertsToggle.addEventListener("change", () => {
                handleLoginAlertsToggle(loginAlertsToggle.checked);
            });
        }

        updateLoginAlertsUiState(isLoginAlertsEnabled());
        clearInlineStatus(changePasswordStatus);
        clearInlineStatus(loginAlertsFeedback);
        updatePasswordRequirementsUi();
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
        bindWorkspaceDefaults();
        bindSecurityActions();
        bindPlannedFeatures();
        bindSettingsScrollSpy();
        bindHeaderActions();
        syncThemeState();
        loadWorkspaceDefaults();

        window.addEventListener("resize", () => {
            sidebarState.closeMobileSidebar();
            sidebarState.restoreDesktopState();
        });
    };

    initializeSettingsPage();
})();
