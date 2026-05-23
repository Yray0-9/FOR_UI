(() => {
    const navLinks = Array.from(document.querySelectorAll(".settings-nav-link"));
    if (!navLinks.length) {
        return;
    }

    const sections = navLinks
        .map((link) => {
            const target = String(link.getAttribute("href") || "").trim();
            if (!target.startsWith("#")) {
                return null;
            }

            const element = document.querySelector(target);
            if (!element) {
                return null;
            }

            return { link, element };
        })
        .filter(Boolean);

    if (!sections.length) {
        return;
    }

    const setActiveLink = (activeLink) => {
        navLinks.forEach((link) => {
            const isActive = link === activeLink;
            link.classList.toggle("is-active", isActive);
            if (isActive) {
                link.setAttribute("aria-current", "true");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    };

    const resolveScrollOffset = () => {
        const layout = document.querySelector(".admin-settings-layout, .settings-layout");
        if (!layout) {
            return 160;
        }

        const rawValue = getComputedStyle(layout)
            .getPropertyValue("--settings-sticky-offset")
            .trim();
        if (!rawValue) {
            return 160;
        }

        const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
        if (rawValue.endsWith("rem")) {
            return (parseFloat(rawValue) || 0) * rootFontSize + 16;
        }

        if (rawValue.endsWith("px")) {
            return (parseFloat(rawValue) || 0) + 16;
        }

        const numericValue = parseFloat(rawValue);
        return Number.isFinite(numericValue) ? numericValue + 16 : 160;
    };

    let scrollOffset = resolveScrollOffset();
    let rafPending = false;

    const updateActiveFromScroll = () => {
        const scrollPosition = window.scrollY + scrollOffset;
        let activeLink = sections[0].link;

        sections.forEach((section) => {
            if (section.element.offsetTop <= scrollPosition) {
                activeLink = section.link;
            }
        });

        setActiveLink(activeLink);
    };

    const scheduleUpdate = () => {
        if (rafPending) {
            return;
        }

        rafPending = true;
        window.requestAnimationFrame(() => {
            rafPending = false;
            updateActiveFromScroll();
        });
    };

    navLinks.forEach((link) => {
        link.addEventListener("click", () => {
            setActiveLink(link);
        });
    });

    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", () => {
        scrollOffset = resolveScrollOffset();
        scheduleUpdate();
    });
    scrollOffset = resolveScrollOffset();
    updateActiveFromScroll();
})();
