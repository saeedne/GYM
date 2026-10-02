document.addEventListener("DOMContentLoaded", function () {
    // Use the browser/device clock so the displayed date remains correct offline.
    const localClock = document.getElementById("currentDateTime");
    function updateLocalClock() {
        if (!localClock) return;
        const now = new Date();
        const options = {
            year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
        };
        try {
            localClock.textContent = new Intl.DateTimeFormat("fa-IR-u-ca-persian", options).format(now);
        } catch (_) {
            localClock.textContent = window.persianDate
                ? new window.persianDate(now).format("dddd D MMMM YYYY HH:mm:ss")
                : now.toLocaleString("fa-IR");
        }
        localClock.dateTime = now.toISOString();
    }
    updateLocalClock();
    window.setInterval(updateLocalClock, 1000);

    const userKey = document.body.dataset.themeUser || "default";
    const storageKey = "gym-manager-appearance-" + userKey;
    const guestStorageKey = "gym-manager-appearance-guest";
    // Carry the appearance selected on the login screen into the newly signed-in account.
    if (document.body.dataset.authenticated === "true" && userKey !== "guest") {
        try {
            if (!localStorage.getItem(storageKey) && localStorage.getItem(guestStorageKey)) {
                localStorage.setItem(storageKey, localStorage.getItem(guestStorageKey));
            }
        } catch (_) { /* Keep the current page usable when browser storage is unavailable. */ }
    }
    const presets = {
        blue:       { primary:"#2386ff", bg:"#07111f", panel:"#0d1b2d", panel2:"#10233a", line:"#1d3551", sidebar:"#081727", topbar:"#091827", input:"#091a2c", hover:"#10253c", link:"#72b2ff", tableAlt:"#11243a" },
        teal:       { primary:"#14b8a6", bg:"#071a1c", panel:"#0d2628", panel2:"#123638", line:"#1d4849", sidebar:"#082022", topbar:"#091f21", input:"#0a2022", hover:"#123638", link:"#65d9ca", tableAlt:"#112e30" },
        purple:     { primary:"#9b7bff", bg:"#130f20", panel:"#211a32", panel2:"#2c2342", line:"#44365f", sidebar:"#191329", topbar:"#1b152b", input:"#1b1529", hover:"#35294d", link:"#beaaff", tableAlt:"#2a2140" },
        amber:      { primary:"#f59e0b", bg:"#1b160d", panel:"#292114", panel2:"#382b18", line:"#5a4525", sidebar:"#21190e", topbar:"#211a10", input:"#21190e", hover:"#44331a", link:"#ffc45e", tableAlt:"#332817" },
        sunset:     { primary:"#f9735b", bg:"#211311", panel:"#321d1a", panel2:"#442520", line:"#653a32", sidebar:"#281714", topbar:"#2a1714", input:"#291815", hover:"#512c25", link:"#ffab96", tableAlt:"#3b211d" },
        terracotta: { primary:"#d76a43", bg:"#1e1512", panel:"#30211b", panel2:"#412b22", line:"#624235", sidebar:"#261a16", topbar:"#281b16", input:"#281b16", hover:"#4b3025", link:"#efa07d", tableAlt:"#38261f" },
        rose:       { primary:"#e45c78", bg:"#201219", panel:"#321c27", panel2:"#442431", line:"#663849", sidebar:"#281722", topbar:"#2a1823", input:"#291821", hover:"#512b39", link:"#ff9db2", tableAlt:"#3b222d" },
        copper:     { primary:"#c77936", bg:"#1d1711", panel:"#30241a", panel2:"#413020", line:"#62482f", sidebar:"#251c14", topbar:"#271d15", input:"#271d15", hover:"#4b3623", link:"#edb06e", tableAlt:"#38291d" },
        forest:     { primary:"#79a85a", bg:"#101810", panel:"#1a2819", panel2:"#243522", line:"#3a5236", sidebar:"#142014", topbar:"#162216", input:"#172317", hover:"#2b4028", link:"#acd48c", tableAlt:"#20301e" },
        emerald:    { primary:"#35a77c", bg:"#0d1915", panel:"#172923", panel2:"#20382f", line:"#345849", sidebar:"#11221b", topbar:"#13241c", input:"#14251d", hover:"#294537", link:"#83d8b6", tableAlt:"#1c3028" },
        graphite:   { primary:"#a7afb8", bg:"#14171a", panel:"#22272c", panel2:"#2d343a", line:"#454e56", sidebar:"#1a1e22", topbar:"#1c2024", input:"#1d2226", hover:"#343c43", link:"#d0d5da", tableAlt:"#282e33" },
        plum:       { primary:"#bb78a6", bg:"#1c141c", panel:"#2c202c", panel2:"#3a2b3a", line:"#584258", sidebar:"#241a24", topbar:"#261b26", input:"#251b25", hover:"#443246", link:"#e2abd0", tableAlt:"#332533" },
        sand:       { primary:"#c6a66b", bg:"#1c1913", panel:"#2d281e", panel2:"#3b3427", line:"#5b503a", sidebar:"#241f17", topbar:"#262117", input:"#252116", hover:"#443a29", link:"#e3c993", tableAlt:"#332d21" }
    };
    function saveAppearance(settings) {
        try { localStorage.setItem(storageKey, JSON.stringify(settings)); } catch (_) { /* Appearance still applies for this page. */ }
    }
    function readAppearance() {
        try { return JSON.parse(localStorage.getItem(storageKey) || "{}"); } catch (_) { return {}; }
    }
    function applyAppearance(settings) {
        const palette = presets[settings.theme] || presets.blue;
        const root = document.documentElement;
        root.style.setProperty("--primary", palette.primary);
        root.style.setProperty("--accent-soft", palette.hover);
        root.style.setProperty("--text", "#edf2f5");
        root.style.setProperty("--muted", "#aab6bc");
        root.style.setProperty("--bg", palette.bg);
        root.style.setProperty("--panel", palette.panel);
        root.style.setProperty("--panel2", palette.panel2);
        root.style.setProperty("--line", palette.line);
        root.style.setProperty("--sidebar", palette.sidebar);
        root.style.setProperty("--topbar", palette.topbar);
        root.style.setProperty("--input", palette.input);
        root.style.setProperty("--hover", palette.hover);
        root.style.setProperty("--link", palette.link);
        root.style.setProperty("--table-alt", palette.tableAlt);
        root.dataset.theme = presets[settings.theme] ? settings.theme : "blue";
        document.body.dataset.layout = settings.layout || "standard";
        document.querySelectorAll(".theme-choice").forEach(function (button) {
            const selected = button.dataset.theme === (settings.theme || "blue");
            button.classList.toggle("is-selected", selected);
            button.setAttribute("aria-pressed", selected ? "true" : "false");
        });
        document.querySelectorAll(".layout-choice").forEach(function (button) {
            const selected = button.dataset.layout === (settings.layout || "standard");
            button.classList.toggle("is-selected", selected);
            button.setAttribute("aria-pressed", selected ? "true" : "false");
        });
    }
    let appearance = readAppearance();
    applyAppearance(appearance);
    document.querySelectorAll(".theme-choice").forEach(function (button) {
        button.addEventListener("click", function () {
            appearance.theme = button.dataset.theme;
            applyAppearance(appearance);
            saveAppearance(appearance);
        });
    });
    document.querySelectorAll(".layout-choice").forEach(function (button) {
        button.addEventListener("click", function () {
            appearance.layout = button.dataset.layout;
            applyAppearance(appearance);
            saveAppearance(appearance);
        });
    });
    const reset = document.getElementById("resetAppearance");
    if (reset) reset.addEventListener("click", function () {
        try { localStorage.removeItem(storageKey); } catch (_) { /* Reset applies for this page too. */ }
        appearance = {};
        applyAppearance(appearance);
    });
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");
    function closeSidebar() {
        document.body.classList.remove("sidebar-open");
        if (sidebarToggle) sidebarToggle.setAttribute("aria-expanded", "false");
    }
    if (sidebarToggle) sidebarToggle.addEventListener("click", function () {
        const open = document.body.classList.toggle("sidebar-open");
        sidebarToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (sidebarBackdrop) sidebarBackdrop.addEventListener("click", closeSidebar);
    document.querySelectorAll(".sidebar nav a").forEach(function (link) {
        link.addEventListener("click", closeSidebar);
    });
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
        if (input.parentElement.classList.contains("password-wrap")) return;
        const wrap = document.createElement("span");
        wrap.className = "password-wrap";
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "password-toggle";
        toggle.setAttribute("aria-label", "نمایش گذرواژه");
        toggle.textContent = "◉";
        toggle.addEventListener("click", function () {
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            toggle.setAttribute("aria-label", show ? "پنهان کردن گذرواژه" : "نمایش گذرواژه");
            toggle.textContent = show ? "◎" : "◉";
        });
        wrap.appendChild(toggle);
    });
    if (window.jQuery && jQuery.fn.persianDatepicker) {
        jQuery(".jalali-date").each(function () {
            jQuery(this).persianDatepicker({
                format: "YYYY/MM/DD",
                autoClose: true,
                initialValue: false,
                observer: true,
                calendarType: "persian",
                initialValueType: "persian",
                calendar: { persian: { locale: "fa", leapYearMode: "astronomical" } }
            });
        });
    }
    document.querySelectorAll(".messages .message").forEach(function (el) {
        setTimeout(function () {
            el.style.opacity = "0";
            el.style.transition = "opacity .5s";
        }, 5000);
    });
});
