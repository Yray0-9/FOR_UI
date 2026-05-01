(function () {
    const body = document.body;
    if (!body) {
        return;
    }

    const MIN_INITIAL_MS = 420;
    const TRANSITION_FLASH_MS = 420;
    const startTime = performance.now();

    const hideSkeleton = () => {
        const elapsed = performance.now() - startTime;
        const delay = Math.max(0, MIN_INITIAL_MS - elapsed);
        window.setTimeout(() => {
            body.classList.remove("skeleton-active");
            body.classList.add("skeleton-loaded");
        }, delay);
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", hideSkeleton, { once: true });
    } else {
        hideSkeleton();
    }

    const shouldInterceptLink = (link, event) => {
        if (!link || event.defaultPrevented || event.button !== 0) {
            return false;
        }

        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return false;
        }

        if (link.dataset.noSkeleton !== undefined) {
            return false;
        }

        const target = link.getAttribute("target");
        if (target && target.toLowerCase() !== "_self") {
            return false;
        }

        if (link.hasAttribute("download")) {
            return false;
        }

        const rawHref = link.getAttribute("href");
        if (!rawHref || rawHref.startsWith("#") || rawHref.startsWith("javascript:") || rawHref.startsWith("mailto:") || rawHref.startsWith("tel:")) {
            return false;
        }

        let targetUrl;
        try {
            targetUrl = new URL(link.href, window.location.href);
        } catch {
            return false;
        }

        if (targetUrl.origin !== window.location.origin) {
            return false;
        }

        const current = window.location.pathname + window.location.search;
        const next = targetUrl.pathname + targetUrl.search;
        if (current === next) {
            return false;
        }

        return true;
    };

    document.addEventListener(
        "click",
        (event) => {
            const link = event.target.closest("a[href]");
            if (!shouldInterceptLink(link, event)) {
                return;
            }

            event.preventDefault();
            body.classList.remove("skeleton-loaded");
            body.classList.add("skeleton-active");

            window.setTimeout(() => {
                window.location.assign(link.href);
            }, TRANSITION_FLASH_MS);
        },
        true
    );

    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        // Skip AJAX or custom-handled submits to avoid stuck loading overlays.
        if (event.defaultPrevented || form.dataset.noSkeletonSubmit !== undefined || form.dataset.noSkeleton !== undefined) {
            return;
        }

        body.classList.remove("skeleton-loaded");
        body.classList.add("skeleton-active");
    });
})();
