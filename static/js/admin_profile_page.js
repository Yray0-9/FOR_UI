(() => {
    const config = window.SafeBooksAdminProfileConfig || {};
    const urls = config.urls || {};
    const initialProfile = config.profile || {};
    const shared = window.SafeBooksShared || null;

    const adminIdentityForm = document.getElementById("adminIdentity");
    const adminSecurityForm = document.getElementById("adminSecurity");
    const adminFullNameInput = document.getElementById("adminFullName");
    const adminEmailInput = document.getElementById("adminEmail");
    const adminProfileSave = document.getElementById("adminProfileSave");
    const adminProfileReset = document.getElementById("adminProfileReset");
    const adminProfileStatus = document.getElementById("adminProfileStatus");

    const adminCurrentPassword = document.getElementById("adminCurrentPassword");
    const adminNewPassword = document.getElementById("adminNewPassword");
    const adminConfirmPassword = document.getElementById("adminConfirmPassword");
    const adminPasswordSave = document.getElementById("adminPasswordSave");
    const adminPasswordStatus = document.getElementById("adminPasswordStatus");

    const adminProfileName = document.getElementById("adminProfileName");
    const adminProfileEmail = document.getElementById("adminProfileEmail");
    const adminProfileAvatar = document.getElementById("adminProfileAvatar");
    const adminUserName = document.getElementById("adminUserName");
    const adminUserAvatar = document.getElementById("adminUserAvatar");
    const uiToastContainer = document.getElementById("uiToastContainer");

    const adminTwoFactorStatus = document.getElementById("adminTwoFactorStatus");
    const adminTwoFactorTitle = document.getElementById("adminTwoFactorTitle");
    const adminTwoFactorDescription = document.getElementById("adminTwoFactorDescription");
    const adminTwoFactorAction = document.getElementById("adminTwoFactorAction");
    const adminTwoFactorRecoveryAction = document.getElementById("adminTwoFactorRecoveryAction");
    const adminTwoFactorSetupModalElement = document.getElementById("adminTwoFactorSetupModal");
    const adminTwoFactorSetupForm = document.getElementById("adminTwoFactorSetupForm");
    const adminTwoFactorPasswordStep = document.getElementById("adminTwoFactorPasswordStep");
    const adminTwoFactorCodeStep = document.getElementById("adminTwoFactorCodeStep");
    const adminTwoFactorCurrentPassword = document.getElementById("adminTwoFactorCurrentPassword");
    const adminTwoFactorQrPanel = document.getElementById("adminTwoFactorQrPanel");
    const adminTwoFactorQrCode = document.getElementById("adminTwoFactorQrCode");
    const adminTwoFactorSetupKey = document.getElementById("adminTwoFactorSetupKey");
    const adminTwoFactorCopyKey = document.getElementById("adminTwoFactorCopyKey");
    const adminTwoFactorCode = document.getElementById("adminTwoFactorCode");
    const adminTwoFactorSetupFeedback = document.getElementById("adminTwoFactorSetupFeedback");
    const adminTwoFactorBegin = document.getElementById("adminTwoFactorBegin");
    const adminTwoFactorConfirm = document.getElementById("adminTwoFactorConfirm");
    const adminRecoveryCodesModalElement = document.getElementById("adminRecoveryCodesModal");
    const adminRecoveryCodeList = document.getElementById("adminRecoveryCodeList");
    const adminRecoveryCodesFeedback = document.getElementById("adminRecoveryCodesFeedback");
    const adminRecoveryCodesCopy = document.getElementById("adminRecoveryCodesCopy");
    const adminRecoveryCodesPrint = document.getElementById("adminRecoveryCodesPrint");
    const adminRecoveryCodesDone = document.getElementById("adminRecoveryCodesDone");
    const adminRecoveryRegenerateModalElement = document.getElementById("adminRecoveryRegenerateModal");
    const adminRecoveryRegenerateForm = document.getElementById("adminRecoveryRegenerateForm");
    const adminRecoveryRegeneratePassword = document.getElementById("adminRecoveryRegeneratePassword");
    const adminRecoveryRegenerateCode = document.getElementById("adminRecoveryRegenerateCode");
    const adminRecoveryRegenerateFeedback = document.getElementById("adminRecoveryRegenerateFeedback");
    const adminRecoveryRegenerateButton = document.getElementById("adminRecoveryRegenerate");
    const adminTwoFactorDisableModalElement = document.getElementById("adminTwoFactorDisableModal");
    const adminTwoFactorDisableForm = document.getElementById("adminTwoFactorDisableForm");
    const adminTwoFactorDisablePassword = document.getElementById("adminTwoFactorDisablePassword");
    const adminTwoFactorDisableCode = document.getElementById("adminTwoFactorDisableCode");
    const adminTwoFactorDisableFeedback = document.getElementById("adminTwoFactorDisableFeedback");
    const adminTwoFactorDisableButton = document.getElementById("adminTwoFactorDisable");

    const setupModal = adminTwoFactorSetupModalElement && window.bootstrap
        ? window.bootstrap.Modal.getOrCreateInstance(adminTwoFactorSetupModalElement)
        : null;
    const recoveryCodesModal = adminRecoveryCodesModalElement && window.bootstrap
        ? window.bootstrap.Modal.getOrCreateInstance(adminRecoveryCodesModalElement)
        : null;
    const recoveryRegenerateModal = adminRecoveryRegenerateModalElement && window.bootstrap
        ? window.bootstrap.Modal.getOrCreateInstance(adminRecoveryRegenerateModalElement)
        : null;
    const disableModal = adminTwoFactorDisableModalElement && window.bootstrap
        ? window.bootstrap.Modal.getOrCreateInstance(adminTwoFactorDisableModalElement)
        : null;

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

    const parseJsonSafe = async (response) => {
        if (shared && typeof shared.parseJsonSafe === "function") {
            return shared.parseJsonSafe(response);
        }
        try {
            return await response.json();
        } catch (error) {
            return null;
        }
    };

    const getCookieValue = (name) => {
        if (shared && typeof shared.getCookieValue === "function") {
            return shared.getCookieValue(name);
        }
        return "";
    };

    const resolveInitials = (name) => {
        const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
        if (!parts.length) {
            return "SA";
        }
        if (parts.length === 1) {
            return parts[0].slice(0, 2).toUpperCase();
        }
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    };

    const setButtonLoading = (button, isLoading, loadingText) => {
        if (!button) {
            return;
        }
        if (!button.dataset.defaultLabel) {
            button.dataset.defaultLabel = button.textContent || "";
        }
        button.disabled = isLoading;
        button.textContent = isLoading ? loadingText : button.dataset.defaultLabel;
    };

    const postJson = async (url, payload) => {
        const csrfToken = getCookieValue("csrftoken");
        return fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
                "X-CSRFToken": csrfToken,
            },
            credentials: "same-origin",
            body: JSON.stringify(payload || {}),
        });
    };

    const handleAuthRedirect = (response) => {
        if (response.status === 401 || response.status === 403) {
            showToast("Admin session expired. Please log in again.", "warning");
            window.location.assign(String(urls.loginPage || "/login/"));
            return true;
        }
        return false;
    };

    const updateIdentityDisplay = (profile) => {
        const fullName = String(profile && profile.full_name ? profile.full_name : "").trim() || "System Admin";
        const email = String(profile && profile.email ? profile.email : "").trim();
        const initials = resolveInitials(fullName);

        if (adminProfileName) {
            adminProfileName.textContent = fullName;
        }
        if (adminProfileEmail) {
            adminProfileEmail.textContent = email;
        }
        if (adminProfileAvatar) {
            adminProfileAvatar.textContent = initials;
        }
        if (adminUserName) {
            adminUserName.textContent = fullName;
        }
        if (adminUserAvatar) {
            adminUserAvatar.textContent = initials;
        }
    };

    const setProfileStatus = (message) => {
        if (adminProfileStatus) {
            adminProfileStatus.textContent = message;
        }
    };

    const setPasswordStatus = (message) => {
        if (adminPasswordStatus) {
            adminPasswordStatus.textContent = message;
        }
    };

    const setSecurityFeedback = (element, message, isSuccess = false) => {
        if (!element) {
            return;
        }
        element.textContent = String(message || "");
        element.classList.toggle("is-success", Boolean(isSuccess));
    };

    let twoFactorEnabled = false;
    let recoveryCodesRemaining = 0;
    let visibleRecoveryCodes = [];
    let pendingRecoveryCodes = [];

    const renderTwoFactorStatus = (status) => {
        twoFactorEnabled = Boolean(status && status.enabled);
        recoveryCodesRemaining = Number.isFinite(Number(status && status.recovery_codes_remaining))
            ? Math.max(0, Number(status.recovery_codes_remaining))
            : 0;
        if (adminTwoFactorStatus) {
            adminTwoFactorStatus.textContent = twoFactorEnabled ? "Enabled" : "Not enabled";
            adminTwoFactorStatus.classList.remove("is-loading");
            adminTwoFactorStatus.classList.toggle("is-enabled", twoFactorEnabled);
        }
        if (adminTwoFactorTitle) {
            adminTwoFactorTitle.textContent = twoFactorEnabled
                ? "Authenticator connected"
                : "Two-factor authentication";
        }
        if (adminTwoFactorDescription) {
            adminTwoFactorDescription.textContent = twoFactorEnabled
                ? `${recoveryCodesRemaining} recovery ${recoveryCodesRemaining === 1 ? "code" : "codes"} available.`
                : "Password-only admin access is currently active.";
        }
        if (adminTwoFactorRecoveryAction) {
            adminTwoFactorRecoveryAction.classList.toggle("d-none", !twoFactorEnabled);
            adminTwoFactorRecoveryAction.disabled = !twoFactorEnabled;
        }
        if (adminTwoFactorAction) {
            adminTwoFactorAction.disabled = false;
            adminTwoFactorAction.textContent = twoFactorEnabled ? "Disable 2FA" : "Enable 2FA";
        }
    };

    const resetSetupModal = () => {
        if (adminTwoFactorSetupForm) {
            adminTwoFactorSetupForm.reset();
        }
        if (adminTwoFactorSetupKey) {
            adminTwoFactorSetupKey.value = "";
        }
        if (adminTwoFactorQrCode) {
            adminTwoFactorQrCode.removeAttribute("src");
        }
        if (adminTwoFactorQrPanel) {
            adminTwoFactorQrPanel.classList.add("d-none");
        }
        if (adminTwoFactorPasswordStep) {
            adminTwoFactorPasswordStep.classList.remove("d-none");
        }
        if (adminTwoFactorCodeStep) {
            adminTwoFactorCodeStep.classList.add("d-none");
        }
        if (adminTwoFactorBegin) {
            adminTwoFactorBegin.classList.remove("d-none");
            setButtonLoading(adminTwoFactorBegin, false, "Continue");
        }
        if (adminTwoFactorConfirm) {
            adminTwoFactorConfirm.classList.add("d-none");
            setButtonLoading(adminTwoFactorConfirm, false, "Enable 2FA");
        }
        setSecurityFeedback(adminTwoFactorSetupFeedback, "");
    };

    const resetDisableModal = () => {
        if (adminTwoFactorDisableForm) {
            adminTwoFactorDisableForm.reset();
        }
        if (adminTwoFactorDisableButton) {
            setButtonLoading(adminTwoFactorDisableButton, false, "Disable 2FA");
        }
        setSecurityFeedback(adminTwoFactorDisableFeedback, "");
    };

    const resetRecoveryRegenerateModal = () => {
        if (adminRecoveryRegenerateForm) {
            adminRecoveryRegenerateForm.reset();
        }
        if (adminRecoveryRegenerateButton) {
            setButtonLoading(adminRecoveryRegenerateButton, false, "Create new codes");
        }
        setSecurityFeedback(adminRecoveryRegenerateFeedback, "");
    };

    const clearVisibleRecoveryCodes = () => {
        visibleRecoveryCodes = [];
        if (adminRecoveryCodeList) {
            adminRecoveryCodeList.replaceChildren();
        }
        setSecurityFeedback(adminRecoveryCodesFeedback, "");
    };

    const showRecoveryCodes = (codes) => {
        visibleRecoveryCodes = Array.isArray(codes)
            ? codes.map((code) => String(code || "").trim()).filter(Boolean)
            : [];
        if (!visibleRecoveryCodes.length || !adminRecoveryCodeList) {
            showToast("Recovery codes could not be displayed. Create a new set before login enforcement is enabled.", "danger");
            return;
        }

        adminRecoveryCodeList.replaceChildren(...visibleRecoveryCodes.map((code) => {
            const codeElement = document.createElement("code");
            codeElement.className = "profile-recovery-code";
            codeElement.textContent = code;
            return codeElement;
        }));
        setSecurityFeedback(adminRecoveryCodesFeedback, "These codes are visible only during this step.", true);
        if (recoveryCodesModal) {
            recoveryCodesModal.show();
        }
    };

    const queueRecoveryCodes = (codes, sourceModal) => {
        pendingRecoveryCodes = Array.isArray(codes) ? [...codes] : [];
        if (sourceModal) {
            sourceModal.hide();
            return;
        }
        const codesToShow = [...pendingRecoveryCodes];
        pendingRecoveryCodes = [];
        showRecoveryCodes(codesToShow);
    };

    const printRecoveryCodes = () => {
        if (!visibleRecoveryCodes.length) {
            return false;
        }
        const printWindow = window.open("", "_blank", "width=720,height=720");
        if (!printWindow) {
            return false;
        }
        printWindow.opener = null;
        const codeMarkup = visibleRecoveryCodes
            .map((code) => `<li>${escapeHtml(code)}</li>`)
            .join("");
        printWindow.document.write(`<!doctype html>
            <html lang="en">
                <head>
                    <meta charset="utf-8">
                    <title>SafeBooks recovery codes</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; color: #142c57; }
                        h1 { font-size: 24px; margin-bottom: 8px; }
                        p { color: #536b94; line-height: 1.5; }
                        ul { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 0; list-style: none; }
                        li { border: 1px solid #c9d9f5; padding: 12px; font-family: Consolas, monospace; font-weight: 700; text-align: center; }
                    </style>
                </head>
                <body>
                    <h1>SafeBooks admin recovery codes</h1>
                    <p>Each code works once. Store this page privately and mark codes as they are used.</p>
                    <ul>${codeMarkup}</ul>
                </body>
            </html>`);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
        return true;
    };

    let savedProfile = {
        full_name: String(initialProfile.full_name || "").trim(),
        email: String(initialProfile.email || "").trim(),
    };

    const resetProfileForm = () => {
        if (adminFullNameInput) {
            adminFullNameInput.value = savedProfile.full_name;
        }
        if (adminEmailInput) {
            adminEmailInput.value = savedProfile.email;
        }
        setProfileStatus("Saved");
    };

    const loadProfile = async () => {
        const url = String(urls.adminProfileApi || "");
        if (!url) {
            return;
        }

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                },
                credentials: "same-origin",
            });
            if (handleAuthRedirect(response)) {
                return;
            }
            const payload = await parseJsonSafe(response);
            if (!response.ok || !payload || !payload.ok) {
                return;
            }

            if (payload.profile) {
                savedProfile = {
                    full_name: String(payload.profile.full_name || "").trim(),
                    email: String(payload.profile.email || "").trim(),
                };
                resetProfileForm();
                updateIdentityDisplay(payload.profile);
            }
            renderTwoFactorStatus(payload.two_factor || {});
        } catch (error) {
            // The form keeps its server-rendered values if the refresh request fails.
        }
    };

    if (adminIdentityForm) {
        adminIdentityForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const url = String(urls.adminProfileApi || "");
            if (!url) {
                showToast("Admin profile updates are unavailable.", "warning");
                return;
            }

            const payload = {
                full_name: adminFullNameInput ? adminFullNameInput.value.trim() : "",
                email: adminEmailInput ? adminEmailInput.value.trim() : "",
            };

            setButtonLoading(adminProfileSave, true, "Saving...");
            setProfileStatus("Saving...");

            try {
                const response = await postJson(url, payload);
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to update admin profile.");
                }

                if (result.profile) {
                    savedProfile = {
                        full_name: String(result.profile.full_name || "").trim(),
                        email: String(result.profile.email || "").trim(),
                    };
                    updateIdentityDisplay(result.profile);
                }
                setProfileStatus("Saved");
                showToast(result.message || "Admin profile updated.", "success");
            } catch (error) {
                setProfileStatus("Update failed");
                showToast(error && error.message ? String(error.message) : "Unable to update admin profile.", "danger");
            } finally {
                setButtonLoading(adminProfileSave, false, "Save profile");
            }
        });
    }

    if (adminProfileReset) {
        adminProfileReset.addEventListener("click", resetProfileForm);
    }

    if (adminFullNameInput) {
        adminFullNameInput.addEventListener("input", () => setProfileStatus("Unsaved changes"));
    }
    if (adminEmailInput) {
        adminEmailInput.addEventListener("input", () => setProfileStatus("Unsaved changes"));
    }

    if (adminSecurityForm) {
        adminSecurityForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const url = String(urls.adminPasswordApi || "");
            if (!url) {
                showToast("Password updates are unavailable.", "warning");
                return;
            }

            const payload = {
                current_password: adminCurrentPassword ? adminCurrentPassword.value : "",
                new_password: adminNewPassword ? adminNewPassword.value : "",
                confirm_password: adminConfirmPassword ? adminConfirmPassword.value : "",
            };

            setButtonLoading(adminPasswordSave, true, "Updating...");
            setPasswordStatus("Updating...");

            try {
                const response = await postJson(url, payload);
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to update admin password.");
                }

                adminSecurityForm.reset();
                setPasswordStatus("Password updated");
                showToast(result.message || "Admin password updated.", "success");
            } catch (error) {
                setPasswordStatus("Update failed");
                showToast(error && error.message ? String(error.message) : "Unable to update admin password.", "danger");
            } finally {
                setButtonLoading(adminPasswordSave, false, "Update password");
            }
        });
    }

    if (adminTwoFactorAction) {
        adminTwoFactorAction.addEventListener("click", () => {
            if (twoFactorEnabled) {
                resetDisableModal();
                if (disableModal) {
                    disableModal.show();
                }
                return;
            }

            resetSetupModal();
            if (setupModal) {
                setupModal.show();
            }
        });
    }

    if (adminTwoFactorRecoveryAction) {
        adminTwoFactorRecoveryAction.addEventListener("click", () => {
            if (!twoFactorEnabled) {
                return;
            }
            resetRecoveryRegenerateModal();
            if (recoveryRegenerateModal) {
                recoveryRegenerateModal.show();
            }
        });
    }

    if (adminTwoFactorBegin) {
        adminTwoFactorBegin.addEventListener("click", async () => {
            const currentPassword = adminTwoFactorCurrentPassword
                ? adminTwoFactorCurrentPassword.value
                : "";
            if (!currentPassword) {
                setSecurityFeedback(adminTwoFactorSetupFeedback, "Enter your current password.");
                if (adminTwoFactorCurrentPassword) {
                    adminTwoFactorCurrentPassword.focus();
                }
                return;
            }

            setButtonLoading(adminTwoFactorBegin, true, "Checking...");
            setSecurityFeedback(adminTwoFactorSetupFeedback, "");
            try {
                const response = await postJson(String(urls.adminTwoFactorSetupApi || ""), {
                    current_password: currentPassword,
                });
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to start authenticator setup.");
                }

                if (adminTwoFactorSetupKey) {
                    adminTwoFactorSetupKey.value = String(result.secret || "");
                }
                const qrCodeDataUrl = String(result.qr_code_data_url || "");
                if (adminTwoFactorQrCode && qrCodeDataUrl.startsWith("data:image/svg+xml;base64,")) {
                    adminTwoFactorQrCode.src = qrCodeDataUrl;
                    if (adminTwoFactorQrPanel) {
                        adminTwoFactorQrPanel.classList.remove("d-none");
                    }
                }
                if (adminTwoFactorPasswordStep) {
                    adminTwoFactorPasswordStep.classList.add("d-none");
                }
                if (adminTwoFactorCodeStep) {
                    adminTwoFactorCodeStep.classList.remove("d-none");
                }
                adminTwoFactorBegin.classList.add("d-none");
                if (adminTwoFactorConfirm) {
                    adminTwoFactorConfirm.classList.remove("d-none");
                }
                setSecurityFeedback(
                    adminTwoFactorSetupFeedback,
                    "Setup key ready. Enter the six-digit code shown in your authenticator app.",
                    true,
                );
                if (adminTwoFactorCode) {
                    adminTwoFactorCode.focus();
                }
            } catch (error) {
                setSecurityFeedback(
                    adminTwoFactorSetupFeedback,
                    error && error.message ? String(error.message) : "Unable to start authenticator setup.",
                );
            } finally {
                setButtonLoading(adminTwoFactorBegin, false, "Continue");
            }
        });
    }

    if (adminTwoFactorConfirm) {
        adminTwoFactorConfirm.addEventListener("click", async () => {
            const code = adminTwoFactorCode ? adminTwoFactorCode.value.trim() : "";
            if (!/^\d{6}$/.test(code)) {
                setSecurityFeedback(adminTwoFactorSetupFeedback, "Enter the six-digit authenticator code.");
                if (adminTwoFactorCode) {
                    adminTwoFactorCode.focus();
                }
                return;
            }

            setButtonLoading(adminTwoFactorConfirm, true, "Enabling...");
            setSecurityFeedback(adminTwoFactorSetupFeedback, "");
            try {
                const response = await postJson(String(urls.adminTwoFactorConfirmApi || ""), { code });
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to enable two-factor authentication.");
                }

                const recoveryCodes = Array.isArray(result.recovery_codes)
                    ? result.recovery_codes
                    : [];
                renderTwoFactorStatus(result.two_factor || {
                    enabled: true,
                    recovery_codes_remaining: recoveryCodes.length,
                });
                showToast(result.message || "Two-factor authentication enabled.", "success");
                queueRecoveryCodes(recoveryCodes, setupModal);
            } catch (error) {
                setSecurityFeedback(
                    adminTwoFactorSetupFeedback,
                    error && error.message ? String(error.message) : "Unable to enable two-factor authentication.",
                );
            } finally {
                setButtonLoading(adminTwoFactorConfirm, false, "Enable 2FA");
            }
        });
    }

    if (adminRecoveryRegenerateButton) {
        adminRecoveryRegenerateButton.addEventListener("click", async () => {
            const currentPassword = adminRecoveryRegeneratePassword
                ? adminRecoveryRegeneratePassword.value
                : "";
            const code = adminRecoveryRegenerateCode ? adminRecoveryRegenerateCode.value.trim() : "";
            if (!currentPassword) {
                setSecurityFeedback(adminRecoveryRegenerateFeedback, "Enter your current password.");
                if (adminRecoveryRegeneratePassword) {
                    adminRecoveryRegeneratePassword.focus();
                }
                return;
            }
            if (!/^\d{6}$/.test(code)) {
                setSecurityFeedback(adminRecoveryRegenerateFeedback, "Enter the six-digit authenticator code.");
                if (adminRecoveryRegenerateCode) {
                    adminRecoveryRegenerateCode.focus();
                }
                return;
            }

            setButtonLoading(adminRecoveryRegenerateButton, true, "Creating...");
            setSecurityFeedback(adminRecoveryRegenerateFeedback, "");
            try {
                const response = await postJson(String(urls.adminTwoFactorRecoveryCodesApi || ""), {
                    current_password: currentPassword,
                    code,
                });
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to create recovery codes.");
                }

                const recoveryCodes = Array.isArray(result.recovery_codes)
                    ? result.recovery_codes
                    : [];
                renderTwoFactorStatus(result.two_factor || {
                    enabled: true,
                    recovery_codes_remaining: recoveryCodes.length,
                });
                showToast(result.message || "New recovery codes created.", "success");
                queueRecoveryCodes(recoveryCodes, recoveryRegenerateModal);
            } catch (error) {
                setSecurityFeedback(
                    adminRecoveryRegenerateFeedback,
                    error && error.message ? String(error.message) : "Unable to create recovery codes.",
                );
            } finally {
                setButtonLoading(adminRecoveryRegenerateButton, false, "Create new codes");
            }
        });
    }

    if (adminTwoFactorDisableButton) {
        adminTwoFactorDisableButton.addEventListener("click", async () => {
            const currentPassword = adminTwoFactorDisablePassword
                ? adminTwoFactorDisablePassword.value
                : "";
            const code = adminTwoFactorDisableCode ? adminTwoFactorDisableCode.value.trim() : "";
            if (!currentPassword) {
                setSecurityFeedback(adminTwoFactorDisableFeedback, "Enter your current password.");
                if (adminTwoFactorDisablePassword) {
                    adminTwoFactorDisablePassword.focus();
                }
                return;
            }
            const validVerificationCode = /^(?:\d{6}|[A-F0-9]{4}(?:-?[A-F0-9]{4}){2})$/i.test(
                code.replace(/\s/g, ""),
            );
            if (!validVerificationCode) {
                setSecurityFeedback(adminTwoFactorDisableFeedback, "Enter a valid authenticator or recovery code.");
                if (adminTwoFactorDisableCode) {
                    adminTwoFactorDisableCode.focus();
                }
                return;
            }

            setButtonLoading(adminTwoFactorDisableButton, true, "Disabling...");
            setSecurityFeedback(adminTwoFactorDisableFeedback, "");
            try {
                const response = await postJson(String(urls.adminTwoFactorDisableApi || ""), {
                    current_password: currentPassword,
                    code,
                });
                if (handleAuthRedirect(response)) {
                    return;
                }
                const result = await parseJsonSafe(response);
                if (!result || !result.ok) {
                    throw new Error(result && result.message ? result.message : "Unable to disable two-factor authentication.");
                }

                renderTwoFactorStatus(result.two_factor || { enabled: false });
                if (disableModal) {
                    disableModal.hide();
                }
                showToast(result.message || "Two-factor authentication disabled.", "success");
                await loadProfile();
            } catch (error) {
                setSecurityFeedback(
                    adminTwoFactorDisableFeedback,
                    error && error.message ? String(error.message) : "Unable to disable two-factor authentication.",
                );
            } finally {
                setButtonLoading(adminTwoFactorDisableButton, false, "Disable 2FA");
            }
        });
    }

    [adminTwoFactorCode, adminRecoveryRegenerateCode].filter(Boolean).forEach((input) => {
        input.addEventListener("input", () => {
            input.value = input.value.replace(/\D/g, "").slice(0, 6);
        });
    });

    if (adminTwoFactorDisableCode) {
        adminTwoFactorDisableCode.addEventListener("input", () => {
            adminTwoFactorDisableCode.value = adminTwoFactorDisableCode.value
                .replace(/[^A-Fa-f0-9-]/g, "")
                .slice(0, 14)
                .toUpperCase();
        });
    }

    if (adminTwoFactorCopyKey) {
        adminTwoFactorCopyKey.addEventListener("click", async () => {
            const setupKey = adminTwoFactorSetupKey ? adminTwoFactorSetupKey.value : "";
            if (!setupKey) {
                return;
            }
            try {
                await navigator.clipboard.writeText(setupKey);
                setSecurityFeedback(adminTwoFactorSetupFeedback, "Setup key copied.", true);
            } catch (error) {
                if (adminTwoFactorSetupKey) {
                    adminTwoFactorSetupKey.select();
                }
                setSecurityFeedback(adminTwoFactorSetupFeedback, "Select and copy the setup key.");
            }
        });
    }

    if (adminRecoveryCodesCopy) {
        adminRecoveryCodesCopy.addEventListener("click", async () => {
            if (!visibleRecoveryCodes.length) {
                return;
            }
            try {
                await navigator.clipboard.writeText(visibleRecoveryCodes.join("\n"));
                setSecurityFeedback(adminRecoveryCodesFeedback, "Recovery codes copied.", true);
            } catch (error) {
                setSecurityFeedback(adminRecoveryCodesFeedback, "Copy was blocked. Select the codes manually.");
            }
        });
    }

    if (adminRecoveryCodesPrint) {
        adminRecoveryCodesPrint.addEventListener("click", () => {
            if (!printRecoveryCodes()) {
                setSecurityFeedback(adminRecoveryCodesFeedback, "Print window was blocked. Copy the codes instead.");
            }
        });
    }

    if (adminRecoveryCodesDone) {
        adminRecoveryCodesDone.addEventListener("click", () => {
            if (recoveryCodesModal) {
                recoveryCodesModal.hide();
            }
        });
    }

    if (adminTwoFactorSetupModalElement) {
        adminTwoFactorSetupModalElement.addEventListener("hidden.bs.modal", () => {
            resetSetupModal();
            if (pendingRecoveryCodes.length) {
                const codesToShow = [...pendingRecoveryCodes];
                pendingRecoveryCodes = [];
                showRecoveryCodes(codesToShow);
            }
        });
    }
    if (adminRecoveryRegenerateModalElement) {
        adminRecoveryRegenerateModalElement.addEventListener("hidden.bs.modal", () => {
            resetRecoveryRegenerateModal();
            if (pendingRecoveryCodes.length) {
                const codesToShow = [...pendingRecoveryCodes];
                pendingRecoveryCodes = [];
                showRecoveryCodes(codesToShow);
            }
        });
    }
    if (adminRecoveryCodesModalElement) {
        adminRecoveryCodesModalElement.addEventListener("hidden.bs.modal", async () => {
            clearVisibleRecoveryCodes();
            await loadProfile();
        });
    }
    if (adminTwoFactorDisableModalElement) {
        adminTwoFactorDisableModalElement.addEventListener("hidden.bs.modal", resetDisableModal);
    }

    const scrollTargets = Array.from(document.querySelectorAll("[data-scroll-target]"));
    scrollTargets.forEach((button) => {
        button.addEventListener("click", (event) => {
            const selector = String(button.dataset.scrollTarget || "").trim();
            if (!selector) {
                return;
            }
            const target = document.querySelector(selector);
            if (!target) {
                return;
            }

            event.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
            if (target.hasAttribute("tabindex")) {
                target.focus({ preventScroll: true });
            }
        });
    });

    resetProfileForm();
    renderTwoFactorStatus({ enabled: false });
    loadProfile();
})();
