/*
 * Pyxis Effector - Plugin for Aegisub
 * Copyright (C) 2026 @mandholine, @effector2, @pholguinc
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 * For any question you can visit: https://discord.gg/rYsARc3fB9
 */

(function (window) {
    "use strict";

    window.getNodeCategory = function(nodeOrType) {
        if (!nodeOrType) return "Functions";
        const typeStr = typeof nodeOrType === "string" ? nodeOrType : (nodeOrType.type || nodeOrType.title || "");
        const raw = typeStr.trim();
        let cat = "";
        let subName = raw;
        if (raw.includes("/")) {
            const parts = raw.split("/");
            cat = parts[0].trim();
            subName = parts.slice(1).join("/").trim();
        }
        if (cat === "Basics") return "Basics";
        if (cat === "Math" || cat === "Text" || cat === "String") {
            if (subName === "Benchmark Math") return "System";
            return "Basics";
        }
        const basicNames = [
            "Number", "String", "Text", "Color Picker", "Math", "MultiRandom",
            "Concatenate", "Dynamic Format", "MultiTag", "Once", "Only",
            "Número", "Numero", "Cadena de Texto", "Texto", "Selector de Color",
            "Mates", "Concatenar", "Formato Dinámico", "Formato Dinamico"
        ];
        if (basicNames.includes(subName) || basicNames.includes(raw)) return "Basics";
        if (cat) return cat;
        if (raw === "Main Loop" || raw === "MaxLoop" || raw === "Module" || raw === "Bucle Principal" || raw === "Bucle Primario") return "Loops";
        if (raw === "Output" || raw === "Previewer" || raw === "Benchmark Math" || raw === "Script Code" || raw === "Salida" || raw === "Previsualizador" || raw === "Código Script") return "System";
        if (raw === "Define Vars" || raw === "Get Var" || raw === "Memory" || raw === "Sys Var" || raw === "Definir Variables" || raw === "Obtener Variable" || raw === "Memoria") return "Variables";
        if (raw === "Tag Oscillator" || raw === "Tag Manipulator" || raw === "Glitter" || raw === "Conditioner" || raw === "Color Gradient" || raw === "Clip Gradient" || raw === "IMG to pixels" || raw === "Move Tag" || raw === "Move Text" || raw === "Animation" || raw === "Bezier Curve" || raw === "Polar to Cartesian" || raw === "Interpolator" || raw === "Text on Path" || raw === "Text to Shape" || raw === "Particles") return "Functions";
        if (raw === "Library" || raw === "Slicer" || raw === "Transform" || raw === "Stroke" || raw === "Walker" || raw === "Array" || raw === "Union & Divide" || raw === "Multi" || raw === "Manipulator" || raw === "Filter" || raw === "Concentric Borders" || raw === "IMG to Shape") return "Shape";
        if (raw === "Modulator" || raw === "Waveform" || raw === "Modulador" || raw === "Forma de Onda") return "Audio";
        if (raw === "Lead In" || raw === "Lead Out" || raw === "Middle 1" || raw === "Middle 2" || raw === "Loop 1" || raw === "Loop 2" || raw === "Ipol" || raw === "Synced" || raw === "Offset" || raw === "Duration" || raw === "Duración" || raw === "Duracion" || raw === "Parse ASS Time" || raw === "Format ASS Time" || raw === "Time to Frame" || raw === "Frame to Time" || raw === "Retime" || raw === "Tiempo a Frame" || raw === "Frame a Tiempo") return "Time";
        return "Functions";
    };

    const DEFAULT_THEMES = {
        teal: {
            id: "teal",
            name: "Oceanic Teal",
            desc: "Teal, slate and deep navy palette",
            isDefault: true,
            canvasBg: "#081116",
            panelBg: "#101d24",
            topbarBg: "#0c171d",
            cardBg: "#152630",
            inputBg: "#0a1318",
            accentPrimary: "#22858C",
            accentPrimaryEnd: "#548C87",
            accentSecondary: "#3A628C",
            accentSecondaryGlow: "#4f84ba",
            textMain: "#ffffff",
            textMuted: "#c7d8e2",
            colors: ["#22858C", "#548C87", "#6A778C", "#3A628C", "#105A8C"],
            nodeBgGradient: { start: "#112028", end: "#091217" },
            categories: {
                "Basics": { color: "#548C87", gradientEnd: "#67aba5" },
                "Loops": { color: "#22858C", gradientEnd: "#2ba6af" },
                "System": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Variables": { color: "#3A628C", gradientEnd: "#497bb0" },
                "String": { color: "#6A778C", gradientEnd: "#8492aa" },
                "Text": { color: "#6A778C", gradientEnd: "#8492aa" },
                "Math": { color: "#548C87", gradientEnd: "#67aba5" },
                "Functions": { color: "#22858C", gradientEnd: "#2ba6af" },
                "Shape": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Time": { color: "#3A628C", gradientEnd: "#497bb0" },
                "Audio": { color: "#22858C", gradientEnd: "#2ba6af" },
                "Particles": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Meta": { color: "#548C87", gradientEnd: "#67aba5" }
            }
        },
        violet: {
            id: "violet",
            name: "Twilight Violet",
            desc: "Amethyst, violet and deep indigo palette",
            isDefault: true,
            canvasBg: "#0c0914",
            panelBg: "#171324",
            topbarBg: "#130f1e",
            cardBg: "#1e1930",
            inputBg: "#0f0c18",
            accentPrimary: "#67298C",
            accentPrimaryEnd: "#83558C",
            accentSecondary: "#452E8C",
            accentSecondaryGlow: "#7c59d9",
            textMain: "#ffffff",
            textMuted: "#ddd6fe",
            colors: ["#67298C", "#6F6A8C", "#83558C", "#452E8C", "#663F8C"],
            nodeBgGradient: { start: "#181426", end: "#0d0a17" },
            categories: {
                "Basics": { color: "#663F8C", gradientEnd: "#8052ad" },
                "Loops": { color: "#67298C", gradientEnd: "#8439b0" },
                "System": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Variables": { color: "#83558C", gradientEnd: "#9e6ba8" },
                "String": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Text": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Math": { color: "#663F8C", gradientEnd: "#8052ad" },
                "Functions": { color: "#67298C", gradientEnd: "#8439b0" },
                "Shape": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Time": { color: "#83558C", gradientEnd: "#9e6ba8" },
                "Audio": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Particles": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Meta": { color: "#83558C", gradientEnd: "#9e6ba8" }
            }
        },
        crimson: {
            id: "crimson",
            name: "Crimson Ember",
            desc: "Crimson, wine, amber and terracotta palette",
            isDefault: true,
            canvasBg: "#120908",
            panelBg: "#1c1010",
            topbarBg: "#170c0c",
            cardBg: "#221414",
            inputBg: "#140a0a",
            accentPrimary: "#8C1B0D",
            accentPrimaryEnd: "#8C3B19",
            accentSecondary: "#8C0E5B",
            accentSecondaryGlow: "#b81a7a",
            textMain: "#ffffff",
            textMuted: "#f5d0c5",
            colors: ["#8C1B0D", "#8C3742", "#8C3B19", "#8C0E5B", "#8C5C3C"],
            nodeBgGradient: { start: "#1c1212", end: "#100a0a" },
            categories: {
                "Basics": { color: "#8C5C3C", gradientEnd: "#a8714c" },
                "Loops": { color: "#8C3B19", gradientEnd: "#a64d24" },
                "System": { color: "#8C1B0D", gradientEnd: "#b02615" },
                "Variables": { color: "#8C0E5B", gradientEnd: "#ad1774" },
                "String": { color: "#8C3742", gradientEnd: "#a84754" },
                "Text": { color: "#8C3742", gradientEnd: "#a84754" },
                "Math": { color: "#8C5C3C", gradientEnd: "#a8714c" },
                "Functions": { color: "#8C0E5B", gradientEnd: "#ad1774" },
                "Shape": { color: "#8C3742", gradientEnd: "#a84754" },
                "Time": { color: "#8C3B19", gradientEnd: "#a64d24" },
                "Audio": { color: "#8C5C3C", gradientEnd: "#a8714c" },
                "Particles": { color: "#8C1B0D", gradientEnd: "#b02615" },
                "Meta": { color: "#8C3B19", gradientEnd: "#a64d24" }
            }
        }
    };

    function showPyxisConfirm(options = {}) {
        const {
            title = (window.t ? window.t("common.confirm") : "Confirmation"),
            message = (window.t ? window.t("common.confirm_question", null, "Are you sure you want to proceed?") : "Are you sure you want to proceed?"),
            confirmText = (window.t ? window.t("common.confirm") : "Confirm"),
            cancelText = (window.t ? window.t("common.cancel") : "Cancel"),
            isDanger = true,
            onConfirm = null,
            onCancel = null
        } = options;

        const existing = document.getElementById("pyxis-confirm-modal");
        if (existing) existing.remove();

        const overlay = document.createElement("div");
        overlay.id = "pyxis-confirm-modal";
        overlay.className = "pyxis-modal-overlay";
        overlay.style.setProperty("z-index", "5000000", "important");

        overlay.innerHTML = `
            <div class="pyxis-modal-dialog" style="width: 440px; max-width: 90vw; padding: 22px; gap: 16px; border: 1px solid ${isDanger ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-subtle)'}; box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);">
                <div class="pyxis-modal-header" style="padding-bottom: 12px; border-bottom: 1px solid var(--border-subtle);">
                    <div class="pyxis-modal-title" style="color: ${isDanger ? '#ef4444' : 'var(--accent-primary)'}; font-size: 16px;">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width: 18px; height: 18px;">
                            ${isDanger ? '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'}
                        </svg>
                        <span>${title}</span>
                    </div>
                    <button type="button" class="pyxis-modal-close" id="btn-close-confirm">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width: 16px; height: 16px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div style="font-size: 13.5px; line-height: 1.5; color: var(--text-main); padding: 4px 0;">
                    ${message}
                </div>
                <div class="pyxis-modal-actions" style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px;">
                    <button type="button" class="pyxis-btn pyxis-btn-secondary" id="btn-cancel-confirm">
                        <span>${cancelText}</span>
                    </button>
                    <button type="button" class="pyxis-btn ${isDanger ? 'pyxis-btn-danger' : 'pyxis-btn-primary'}" id="btn-ok-confirm">
                        ${isDanger ? '<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px;height:14px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>' : ''}
                        <span>${confirmText}</span>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const close = () => overlay.remove();

        overlay.querySelector("#btn-close-confirm").onclick = () => {
            close();
            if (typeof onCancel === "function") onCancel();
        };

        overlay.querySelector("#btn-cancel-confirm").onclick = () => {
            close();
            if (typeof onCancel === "function") onCancel();
        };

        overlay.querySelector("#btn-ok-confirm").onclick = () => {
            close();
            if (typeof onConfirm === "function") onConfirm();
        };
    }
    window.showPyxisConfirm = showPyxisConfirm;

    let customThemes = {};
    try {
        const stored = localStorage.getItem("pyxis_custom_themes");
        if (stored) customThemes = JSON.parse(stored);
    } catch (e) {
        customThemes = {};
    }

    let THEMES = Object.assign({}, DEFAULT_THEMES, customThemes);
    let currentTheme = localStorage.getItem("pyxis_theme");
    if (!currentTheme || !THEMES[currentTheme]) {
        currentTheme = "teal";
    }

    function getAllThemes() {
        return THEMES;
    }

    async function syncCustomThemesWithBackend() {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_custom_themes === "function") {
            try {
                const themes = await window.pywebview.api.get_custom_themes();
                if (themes && typeof themes === "object") {
                    customThemes = Object.assign({}, customThemes, themes);
                    THEMES = Object.assign({}, DEFAULT_THEMES, customThemes);
                    try {
                        localStorage.setItem("pyxis_custom_themes", JSON.stringify(customThemes));
                    } catch (e) {}
                    if (THEMES[currentTheme]) {
                        applyTheme(currentTheme);
                    }
                    return THEMES;
                }
            } catch (err) {
                console.warn("Pyxis: Could not sync custom themes", err);
            }
        }
        return THEMES;
    }

    window.addEventListener("pywebviewready", async () => {
        await syncCustomThemesWithBackend();
    });

    function hexToHsl(hex) {
        if (!hex || typeof hex !== "string") return [0, 0, 0.5];
        let c = hex.replace("#", "").trim();
        if (c.length === 3) c = c.split("").map(x => x + x).join("");
        if (c.length !== 6) return [0, 0, 0.5];
        const r = parseInt(c.substring(0, 2), 16) / 255;
        const g = parseInt(c.substring(2, 4), 16) / 255;
        const b = parseInt(c.substring(4, 6), 16) / 255;
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        let h = 0, s = 0, l = (max + min) / 2;
        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
            }
            h *= 60;
        }
        return [h, s, l];
    }

    function hslToHex(h, s, l) {
        h = ((h % 360) + 360) % 360;
        s = Math.max(0, Math.min(1, s));
        l = Math.max(0, Math.min(1, l));
        const c = (1 - Math.abs(2 * l - 1)) * s;
        const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
        const m = l - c / 2;
        let r1 = 0, g1 = 0, b1 = 0;
        if (h < 60) { r1 = c; g1 = x; }
        else if (h < 120) { r1 = x; g1 = c; }
        else if (h < 180) { g1 = c; b1 = x; }
        else if (h < 240) { g1 = x; b1 = c; }
        else if (h < 300) { r1 = x; b1 = c; }
        else { r1 = c; b1 = x; }
        const r = Math.round((r1 + m) * 255);
        const g = Math.round((g1 + m) * 255);
        const b = Math.round((b1 + m) * 255);
        return "#" + [r, g, b].map(v => v.toString(16).padStart(2, "0")).join("");
    }

    function applyTheme(themeId) {
        if (!THEMES[themeId]) themeId = "teal";
        currentTheme = themeId;
        localStorage.setItem("pyxis_theme", themeId);
        document.documentElement.setAttribute("data-theme", themeId);

        const themeData = THEMES[themeId];
        window.PYXIS_THEME = themeData;

        const root = document.documentElement;
        
        const canvasBg = themeData.canvasBg || "#0d0f12";
        const panelBg = themeData.panelBg || "#161b22";
        const topbarBg = themeData.topbarBg || panelBg;
        const cardBg = themeData.cardBg || "#181d24";
        const inputBg = themeData.inputBg || canvasBg;
        const textMain = themeData.textMain || "#ffffff";
        const textMuted = themeData.textMuted || "#d1d5db";

        root.style.setProperty("--bg-canvas", canvasBg);
        root.style.setProperty("--bg-panel", panelBg);
        root.style.setProperty("--bg-topbar", topbarBg);
        root.style.setProperty("--bg-card", cardBg);
        root.style.setProperty("--bg-input", inputBg);
        root.style.setProperty("--text-main", textMain);
        root.style.setProperty("--text-muted", textMuted);

        const priStart = themeData.accentPrimary || "#10b981";
        const priEnd = themeData.accentPrimaryEnd || themeData.accentSecondary || "#3b82f6";
        root.style.setProperty("--accent-primary", priStart);
        root.style.setProperty("--accent-primary-hover", priStart);
        root.style.setProperty("--accent-primary-end", priEnd);
        root.style.setProperty("--accent-gradient", `linear-gradient(135deg, ${priStart} 0%, ${priEnd} 100%)`);
        root.style.setProperty("--accent-glow", priStart + "66");
        root.style.setProperty("--border-highlight", priStart + "80");
        root.style.setProperty("--border-subtle", "rgba(255, 255, 255, 0.12)");

        // Theme variable aliases for broad CSS compatibility
        root.style.setProperty("--panel-bg", panelBg);
        root.style.setProperty("--card-bg", cardBg);
        root.style.setProperty("--border-color", priStart + "80");
        root.style.setProperty("--text-primary", textMain);
        root.style.setProperty("--text-secondary", textMuted);

        const secStart = themeData.accentSecondary || "#6366f1";
        const secGlow = themeData.accentSecondaryGlow || themeData.accentSecondaryEnd || themeData.accentSecondary || "#818cf8";
        root.style.setProperty("--accent-secondary", secStart);
        root.style.setProperty("--accent-secondary-glow", secGlow);
        root.style.setProperty("--accent-secondary-end", secGlow);
        root.style.setProperty("--accent-secondary-gradient", `linear-gradient(135deg, ${secStart} 0%, ${secGlow} 100%)`);

        // Compute brightened accent for high-legibility manual elements (formula: shift lightness towards ~0.76-0.82 while preserving hue)
        const [hp, sp, lp] = hexToHsl(priStart);
        const docAccentBright = hslToHex(hp, Math.min(Math.max(sp, 0.60), 0.88), Math.max(0.74, lp + (1 - lp) * 0.50));
        root.style.setProperty("--accent-light", docAccentBright);
        root.style.setProperty("--doc-accent-bright", docAccentBright);
        root.style.setProperty("--doc-text-amber", "#f5edd6");
        root.style.setProperty("--doc-text-amber-bright", "#fff9ed");
        root.style.setProperty("--doc-text-amber-muted", "#ded3be");

        const [h1, s1] = hexToHsl(priStart);
        const [h2, s2] = hexToHsl(secGlow);

        const cLead = hslToHex(h1, Math.max(s1, 0.88), 0.58);
        let diffH = h2 - h1;
        if (diffH > 180) diffH -= 360;
        else if (diffH < -180) diffH += 360;
        const hMid = h1 + diffH * 0.5;
        const cCore = hslToHex(hMid, 0.94, 0.74);
        const cBody = hslToHex(h2, Math.max(s2, 0.90), 0.64);
        const cTail = hslToHex(h2 + 15, Math.max(s2, 0.85), 0.52);
        root.style.setProperty("--theme-shimmer-1", cLead);
        root.style.setProperty("--theme-shimmer-2", cCore);
        root.style.setProperty("--theme-shimmer-3", cBody);
        root.style.setProperty("--theme-shimmer-4", cTail);

        const centerDark = hslToHex(h1, 0.40, 0.07);
        const edgeSaturated = hslToHex(h1, 0.96, 0.36);
        const finishRadial = `radial-gradient(ellipse at center, ${centerDark} 25%, ${edgeSaturated} 100%)`;
        root.style.setProperty("--btn-finish-radial", finishRadial);

        const catColors = {};
        const catGradients = {};
        if (themeData.categories) {
            Object.keys(themeData.categories).forEach(cat => {
                const entry = themeData.categories[cat];
                if (typeof entry === "object" && entry !== null) {
                    catColors[cat] = entry.color || "#3b82f6";
                    catGradients[cat] = { color: entry.color || "#3b82f6", gradientEnd: entry.gradientEnd || entry.color || "#1d4ed8" };
                } else {
                    catColors[cat] = entry || "#3b82f6";
                    catGradients[cat] = { color: entry || "#3b82f6", gradientEnd: entry || "#1d4ed8" };
                }
            });
        }
        if (!catColors["Basics"]) {
            const fallbackCat = themeData.categories && (themeData.categories["Math"] || themeData.categories["Text"] || themeData.categories["String"]);
            if (fallbackCat) {
                const col = (typeof fallbackCat === "object" ? fallbackCat.color : fallbackCat) || themeData.accentPrimary || "#548C87";
                const grad = (typeof fallbackCat === "object" ? (fallbackCat.gradientEnd || fallbackCat.color) : fallbackCat) || themeData.accentPrimaryEnd || "#67aba5";
                catColors["Basics"] = col;
                catGradients["Basics"] = { color: col, gradientEnd: grad };
            } else {
                catColors["Basics"] = themeData.accentPrimary || "#548C87";
                catGradients["Basics"] = { color: themeData.accentPrimary || "#548C87", gradientEnd: themeData.accentPrimaryEnd || "#67aba5" };
            }
        }
        ["Math", "Text", "String"].forEach(legacyCat => {
            if (!catColors[legacyCat] && catColors["Basics"]) {
                catColors[legacyCat] = catColors["Basics"];
                catGradients[legacyCat] = catGradients["Basics"];
            }
        });
        window.CATEGORY_COLORS = catColors;
        window.CATEGORY_GRADIENTS = catGradients;

        if (window.canvas) {
            window.canvas.background_color = canvasBg;

            window.canvas.default_link_color = secStart;
            window.canvas.link_glow_color = secGlow;

            if (window.LiteGraph) {
                window.LiteGraph.LINK_COLOR = secStart;
                window.LiteGraph.CONNECTING_LINK_COLOR = priStart || "#10b981";
            }

            if (window.canvas.default_connection_color) {
                window.canvas.default_connection_color.input_on = priStart || "#10b981";
                window.canvas.default_connection_color.input_off = "#6b7280";
                window.canvas.default_connection_color.output_on = secStart || "#6366f1";
                window.canvas.default_connection_color.output_off = "#6b7280";
            }

            if (window.graph && window.graph._nodes) {
                const nodeBgStart = (themeData.nodeBgGradient && typeof themeData.nodeBgGradient === "object" ? themeData.nodeBgGradient.start : themeData.nodeBgGradient) || cardBg;
                const mutedColor = themeData.textMuted || "#94a3b8";
                window.graph._nodes.forEach(node => {
                    const category = typeof window.getNodeCategory === "function" ? window.getNodeCategory(node) : (node.type ? node.type.split('/')[0] : "");
                    if (category && catColors[category]) {
                        node.color = catColors[category];
                        node.bgcolor = nodeBgStart;
                        node.boxcolor = mutedColor;
                    }
                });
            }

            window.canvas.setDirty(true, true);
            if (typeof window.canvas.draw === "function") {
                window.canvas.draw(true, true);
            }
        }

        if (window.PyxisTelemetry && typeof window.PyxisTelemetry.refreshTheme === "function") {
            try { window.PyxisTelemetry.refreshTheme(); } catch (e) {}
        }
    }

    function saveConfig(removeBg = false) {
        if (window.pywebview && window.pywebview.api) {
            const hasBg = !!(window.backgroundImageSettings && (window.backgroundImageSettings.dataUrl || window.backgroundImageSettings.videoUrl || window.backgroundImageSettings.hasBg));
            const isDaemon = window.pyxisDaemonMode !== undefined ? window.pyxisDaemonMode : true;
            const config = {
                theme: currentTheme,
                grid_mode: window.gridMode !== undefined ? window.gridMode : 1,
                undo_steps: window.PyxisUndoManager ? window.PyxisUndoManager.getMaxSteps() : 30,
                has_bg_image: removeBg ? false : hasBg,
                remove_bg_image: !!removeBg,
                remove_bg_media: !!removeBg,
                no_bg: removeBg ? true : !hasBg,
                bg_media_type: removeBg ? "none" : (window.backgroundImageSettings ? window.backgroundImageSettings.mediaType || "image" : "none"),
                bg_image_mode: window.backgroundImageSettings ? window.backgroundImageSettings.mode : "cover",
                bg_image_opacity: window.backgroundImageSettings ? window.backgroundImageSettings.opacity : 0.85,
                convert_video: window.convertVideoSetting !== undefined ? !!window.convertVideoSetting : true,
                daemon_mode: isDaemon,
                language: window.PyxisI18n ? window.PyxisI18n.currentLang : "es"
            };
            window.pywebview.api.save_user_config(config);
        }
    }

    async function saveCustomTheme(themeObj, shouldApply = true) {
        if (!themeObj || !themeObj.id) return false;
        themeObj.isCustom = true;
        customThemes[themeObj.id] = themeObj;
        THEMES[themeObj.id] = themeObj;
        try {
            localStorage.setItem("pyxis_custom_themes", JSON.stringify(customThemes));
        } catch (e) {}

        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_custom_theme === "function") {
            try {
                await window.pywebview.api.save_custom_theme(themeObj);
            } catch (e) {
                console.warn("Pyxis: Error saving theme to backend", e);
            }
        }
        if (shouldApply) {
            applyTheme(themeObj.id);
        }
        saveConfig();
        return true;
    }

    async function deleteCustomTheme(themeId) {
        if (customThemes[themeId]) {
            delete customThemes[themeId];
        }
        if (THEMES[themeId]) {
            delete THEMES[themeId];
        }
        try {
            localStorage.setItem("pyxis_custom_themes", JSON.stringify(customThemes));
        } catch(e) {}

        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.delete_custom_theme === "function") {
            try {
                await window.pywebview.api.delete_custom_theme(themeId);
            } catch(e) {
                console.warn("Pyxis: Error deleting theme from backend", e);
            }
        }
        if (currentTheme === themeId) {
            applyTheme("teal");
        }
        saveConfig();
        return true;
    }

    function openThemeEditorModal(themeIdToEdit) {
        const existing = document.getElementById("pyxis-theme-editor-modal");
        if (existing) existing.remove();

        const activeThemeBeforeEdit = currentTheme;

        let editingTheme;
        if (themeIdToEdit && customThemes[themeIdToEdit]) {
            editingTheme = JSON.parse(JSON.stringify(customThemes[themeIdToEdit]));
        } else if (themeIdToEdit && DEFAULT_THEMES[themeIdToEdit]) {
            const basePreset = DEFAULT_THEMES[themeIdToEdit];
            editingTheme = JSON.parse(JSON.stringify(basePreset));
            editingTheme.id = "custom_" + Date.now();
            editingTheme.name = (basePreset.name || "Theme") + " (Copy)";
            editingTheme.desc = "Custom theme based on " + (basePreset.name || "Theme");
            editingTheme.isCustom = true;
            delete editingTheme.isDefault;
        } else {
            const defaultBase = DEFAULT_THEMES.teal || Object.values(DEFAULT_THEMES)[0];
            editingTheme = JSON.parse(JSON.stringify(defaultBase));
            editingTheme.id = "custom_" + Date.now();
            editingTheme.name = window.t ? window.t("theme_editor.new_theme_default_name") : "My Custom Theme";
            editingTheme.desc = window.t ? window.t("theme_editor.new_theme_desc") : "Custom theme";
            editingTheme.isCustom = true;
            delete editingTheme.isDefault;
        }

        const modal = document.createElement("div");
        modal.id = "pyxis-theme-editor-modal";
        modal.className = "pyxis-modal-overlay";

        const categoryList = ["Basics", "Loops", "System", "Variables", "String", "Text", "Math", "Functions", "Shape", "Time", "Audio", "Particles", "Meta"];

        function createColorFieldHtml(fieldId, currentHex, dataCat = "", dataProp = "", title = "Color") {
            const hex = (currentHex || "#10B981").toUpperCase();
            const dataAttrs = dataCat ? `data-cat="${dataCat}" data-prop="${dataProp}"` : `data-field-id="${fieldId}"`;
            const baseId = dataCat ? `pyxis-col-${dataCat}-${dataProp}` : `pyxis-col-${fieldId || "field"}`;
            return `
                <div class="pyxis-color-field" title="${title}">
                    <div class="pyxis-color-chip" style="background-color: ${hex};" ${dataAttrs}>
                        <input type="color" id="${baseId}-native" name="${baseId}-native" class="pyxis-color-native-input" value="${hex}" ${dataAttrs}>
                    </div>
                    <input type="text" id="${baseId}-hex" name="${baseId}-hex" class="pyxis-color-hex-text" value="${hex}" maxlength="7" ${dataAttrs} spellcheck="false">
                    <button type="button" class="pyxis-color-pro-btn" title="${window.t ? window.t("theme_editor.pro_picker_tooltip") : "Selector avanzado HSV/RGB"}" ${dataAttrs}>
                        <svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/></svg>
                    </button>
                </div>
            `;
        }

        const priStartVal = editingTheme.accentPrimary || "#10b981";
        const priEndVal = editingTheme.accentPrimaryEnd || editingTheme.accentSecondary || "#3b82f6";
        const secStartVal = editingTheme.accentSecondary || "#6366f1";
        const secGlowVal = editingTheme.accentSecondaryGlow || editingTheme.accentSecondaryEnd || editingTheme.accentSecondary || "#818cf8";
        const nodeBgStartVal = (editingTheme.nodeBgGradient && typeof editingTheme.nodeBgGradient === "object" ? editingTheme.nodeBgGradient.start : editingTheme.nodeBgGradient) || editingTheme.cardBg || "#141a17";
        const nodeBgEndVal = (editingTheme.nodeBgGradient && typeof editingTheme.nodeBgGradient === "object" ? editingTheme.nodeBgGradient.end : editingTheme.canvasBg) || "#0c100e";
        const canvasBgVal = editingTheme.canvasBg || "#0d0f12";
        const panelBgVal = editingTheme.panelBg || "#161b22";
        const topbarBgVal = editingTheme.topbarBg || editingTheme.panelBg || "#12161c";
        const inputBgVal = editingTheme.inputBg || editingTheme.canvasBg || "#12151b";
        const textMainVal = editingTheme.textMain || "#ffffff";
        const textMutedVal = editingTheme.textMuted || "#d1d5db";

        let uiPickersHtml = `
            <div class="theme-editor-cat-card" style="grid-column: 1 / -1;">
                <div class="theme-editor-cat-header">
                    <span class="theme-editor-cat-title">${window.t ? window.t("theme_editor.accent_primary_title") : "Acento Primario (Botones, Resplandores y Destacados)"}</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-pri" style="background: linear-gradient(135deg, ${priStartVal} 0%, ${priEndVal} 100%);">
                        <span class="cat-badge-dot" style="background:#ffffff;"></span>
                        <span>${window.t ? window.t("theme_editor.badge_btn_accent") : "Button / Accent"}</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.start_color") : "Inicio:"}</span>
                        ${createColorFieldHtml("accentPrimary", priStartVal, "", "", window.t ? window.t("theme_editor.field_pri_start") : "Acento Primario (Inicio)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-pri" title="${window.t ? window.t("theme_editor.swap_colors") : "Intercambiar inicio y fin"}">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.end_gradient") : "Fin (Degradado):"}</span>
                        ${createColorFieldHtml("accentPrimaryEnd", priEndVal, "", "", window.t ? window.t("theme_editor.field_pri_end") : "Acento Primario (Fin / Degradado)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-cat-card" style="grid-column: 1 / -1;">
                <div class="theme-editor-cat-header">
                    <span class="theme-editor-cat-title">${window.t ? window.t("theme_editor.wires_title") : "Wires and Node Connections"}</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-sec" style="background: ${secStartVal}; box-shadow: 0 0 10px ${secGlowVal};">
                        <span class="cat-badge-dot" style="background:#ffffff; box-shadow: 0 0 4px ${secGlowVal};"></span>
                        <span>${window.t ? window.t("theme_editor.badge_wires") : "Cables / Enlaces"}</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.wire_color") : "Color del Cable:"}</span>
                        ${createColorFieldHtml("accentSecondary", secStartVal, "", "", window.t ? window.t("theme_editor.field_wire") : "Wire Color (Main Line)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-sec" title="${window.t ? window.t("theme_editor.swap_sec_tooltip") : "Intercambiar color del cable y resplandor"}">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.glow_color") : "Resplandor (Glow):"}</span>
                        ${createColorFieldHtml("accentSecondaryGlow", secGlowVal, "", "", window.t ? window.t("theme_editor.field_glow") : "Color del Resplandor (Glow)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-cat-card" style="grid-column: 1 / -1;">
                <div class="theme-editor-cat-header">
                    <span class="theme-editor-cat-title">${window.t ? window.t("theme_editor.node_bg_title") : "Node and Card Body Background"}</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-nodebg" style="background: linear-gradient(180deg, ${nodeBgStartVal} 0%, ${nodeBgEndVal} 100%);">
                        <span class="cat-badge-dot" style="background:#ffffff;"></span>
                        <span>${window.t ? window.t("theme_editor.badge_node_body") : "Node Body"}</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.top_start") : "Inicio (Superior):"}</span>
                        ${createColorFieldHtml("nodeStart", nodeBgStartVal, "", "", window.t ? window.t("theme_editor.field_node_start") : "Card Background (Start)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-nodebg" title="${window.t ? window.t("theme_editor.swap_colors") : "Intercambiar inicio y fin"}">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.bottom_end") : "Fin (Inferior):"}</span>
                        ${createColorFieldHtml("nodeEnd", nodeBgEndVal, "", "", window.t ? window.t("theme_editor.field_node_end") : "Card Background (End)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.canvas_bg") : "Canvas Background"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.canvas_bg_sub") : "Working surface"}</span>
                </div>
                ${createColorFieldHtml("canvasBg", canvasBgVal, "", "", window.t ? window.t("theme_editor.canvas_bg") : "Canvas Background")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.panel_bg") : "Panel Background"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.panel_bg_sub") : "Sidebars and modals"}</span>
                </div>
                ${createColorFieldHtml("panelBg", panelBgVal, "", "", window.t ? window.t("theme_editor.panel_bg") : "Panel Background")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.topbar_bg") : "Top Toolbar"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.topbar_bg_sub") : "Top toolbar"}</span>
                </div>
                ${createColorFieldHtml("topbarBg", topbarBgVal, "", "", window.t ? window.t("theme_editor.topbar_bg") : "Topbar Background Color")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.input_bg") : "Input Background"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.input_bg_sub") : "Inputs and text boxes"}</span>
                </div>
                ${createColorFieldHtml("inputBg", inputBgVal, "", "", window.t ? window.t("theme_editor.input_bg") : "Inputs Background")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.text_main") : "Main Text"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.text_main_sub") : "Headings and values"}</span>
                </div>
                ${createColorFieldHtml("textMain", textMainVal, "", "", window.t ? window.t("theme_editor.text_main") : "Main Text")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">${window.t ? window.t("theme_editor.text_muted") : "Muted Text"}</span>
                    <span class="theme-editor-item-sub">${window.t ? window.t("theme_editor.text_muted_sub") : "Labels and notes"}</span>
                </div>
                ${createColorFieldHtml("textMuted", textMutedVal, "", "", window.t ? window.t("theme_editor.text_muted") : "Muted Text")}
            </div>
        `;

        let categoryPickersHtml = `
            <div class="theme-editor-global-cat-banner">
                <div class="global-cat-info">
                    <span class="global-cat-title">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:15px;height:15px;color:var(--accent-primary);"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                        ${window.t ? window.t("theme_editor.homogenize_title") : "Homogenize All Nodes"}
                    </span>
                    <span class="global-cat-desc">${window.t ? window.t("theme_editor.homogenize_desc") : "Assigns the same color or gradient to all 13 node types with a single click."}</span>
                </div>
                <div class="global-cat-controls">
                    <div class="pyxis-color-field" title="${window.t ? window.t("theme_editor.global_cat_start_tooltip") : "Global Start Color"}">
                        <div class="pyxis-color-chip" id="global-cat-chip-col" style="background-color: #8B5CF6;">
                            <input type="color" class="pyxis-color-native-input" id="global-cat-native-col" name="global-cat-native-col" value="#8B5CF6">
                        </div>
                        <input type="text" class="pyxis-color-hex-text" id="global-cat-col-inp" name="global-cat-col-inp" value="#8B5CF6" maxlength="7" spellcheck="false">
                    </div>
                    <div class="pyxis-color-field" title="${window.t ? window.t("theme_editor.global_cat_end_tooltip") : "Global End / Gradient Color"}">
                        <div class="pyxis-color-chip" id="global-cat-chip-grad" style="background-color: #6366F1;">
                            <input type="color" class="pyxis-color-native-input" id="global-cat-native-grad" name="global-cat-native-grad" value="#6366F1">
                        </div>
                        <input type="text" class="pyxis-color-hex-text" id="global-cat-grad-inp" name="global-cat-grad-inp" value="#6366F1" maxlength="7" spellcheck="false">
                    </div>
                    <button type="button" class="pyxis-btn pyxis-btn-primary" id="btn-apply-all-categories" title="${window.t ? window.t("theme_editor.apply_all_tooltip") : "Apply to all categories"}">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:14px;height:14px;stroke-width:2.5;fill:none;"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>${window.t ? window.t("theme_editor.apply_all") : "Apply to All"}</span>
                    </button>
                </div>
            </div>
        `;

        categoryList.forEach(cat => {
            const catData = (editingTheme.categories && editingTheme.categories[cat]) || { color: "#3b82f6", gradientEnd: "#1d4ed8" };
            const col = (typeof catData === "object" ? catData.color : catData) || "#3b82f6";
            const grad = (typeof catData === "object" ? (catData.gradientEnd || col) : col) || "#1d4ed8";
            const catTitle = window.PyxisI18n ? window.PyxisI18n.getCategoryTitle(cat) : cat;
            const startTooltip = window.t ? window.t("theme_editor.cat_start_tooltip", { cat: catTitle }) : `Start color for ${catTitle}`;
            const endTooltip = window.t ? window.t("theme_editor.cat_end_tooltip", { cat: catTitle }) : `Gradient/Border color for ${catTitle}`;
            categoryPickersHtml += `
                <div class="theme-editor-cat-card" data-cat="${cat}">
                    <div class="theme-editor-cat-header">
                        <span class="theme-editor-cat-title">${catTitle}</span>
                        <div class="theme-editor-cat-badge" id="cat-badge-${cat}" style="background: linear-gradient(90deg, ${col} 0%, ${grad} 100%);">
                            <span class="cat-badge-dot"></span>
                            <span>${catTitle}</span>
                        </div>
                    </div>
                    <div class="theme-editor-cat-body">
                        <div class="theme-editor-cat-col">
                            <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.start_color") : "Start:"}</span>
                            ${createColorFieldHtml(`cat_${cat}_col`, col, cat, "color", startTooltip)}
                        </div>
                        <button type="button" class="pyxis-cat-swap-btn" data-swap-cat="${cat}" title="${window.t ? window.t("theme_editor.swap_cat_tooltip") : "Swap colors"}">
                            <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                        </button>
                        <div class="theme-editor-cat-col">
                            <span class="theme-editor-col-lbl">${window.t ? window.t("theme_editor.bottom_end") : "End:"}</span>
                            ${createColorFieldHtml(`cat_${cat}_grad`, grad, cat, "gradientEnd", endTooltip)}
                        </div>
                    </div>
                </div>
            `;
        });

        modal.innerHTML = `
            <div class="pyxis-modal-dialog pyxis-theme-editor-dialog">
                <div class="pyxis-modal-header">
                    <div class="pyxis-modal-title">
                        <svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/></svg>
                        <span>${window.t ? window.t("theme_editor.modal_title") : "Custom Themes and Colors Editor"}</span>
                    </div>
                    <button class="pyxis-modal-close" id="btn-close-theme-editor">
                        <svg class="svg-icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>

                <!-- Theme Name and Base Preset -->
                <div style="display: flex; gap: 12px; margin-bottom: 14px;">
                    <div style="flex: 1;">
                        <label style="font-size: 11.5px; font-weight: 500; color: var(--text-muted); display: block; margin-bottom: 4px;">${window.t ? window.t("theme_editor.name") : "Theme Name:"}</label>
                        <input type="text" id="theme-edit-name" name="theme-edit-name" value="${editingTheme.name}" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 100%; box-sizing: border-box; outline: none;">
                    </div>
                    <div style="width: 210px;">
                        <label style="font-size: 11.5px; font-weight: 500; color: var(--text-muted); display: block; margin-bottom: 4px;">${window.t ? window.t("theme_editor.load_base_preset") : "Load Base Preset:"}</label>
                        <select id="theme-edit-preset-select" name="theme-edit-preset-select" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 100%; outline: none; cursor: pointer;">
                            <option value="">${window.t ? window.t("theme_editor.select_base") : "-- Select Base --"}</option>
                            ${Object.keys(DEFAULT_THEMES).map(k => `<option value="${k}">${DEFAULT_THEMES[k].name}</option>`).join('')}
                        </select>
                    </div>
                </div>

                <!-- Node & Canvas Preview -->
                <div class="theme-editor-mock-container">
                    <div class="theme-editor-mock-title">
                        <svg class="svg-icon" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        <span>${window.t ? window.t("theme_editor.preview") : "PREVIEW"}</span>
                    </div>
                    <div class="theme-editor-mock-canvas" id="theme-mock-canvas" style="background-color: ${editingTheme.canvasBg || '#0d0f12'};">
                        <div class="theme-mock-node" id="theme-mock-node" style="background-color: ${editingTheme.nodeBgGradient ? editingTheme.nodeBgGradient.start : '#141a17'};">
                            <div class="theme-mock-node-header" id="theme-mock-header" style="background: linear-gradient(90deg, #3b82f6, #1d4ed8);">
                                <div style="display: flex; align-items: center; gap: 6px;">
                                    <span class="mock-slot-dot" id="theme-mock-title-dot" style="background: ${textMutedVal}; box-shadow: none;"></span>
                                    <span id="theme-mock-title">Transform Node</span>
                                </div>
                                <span class="theme-mock-node-cat" id="theme-mock-cat-tag">Math</span>
                            </div>
                            <div class="theme-mock-node-body" id="theme-mock-body" style="color: ${textMainVal};">
                                <div class="mock-slot-row">
                                    <span style="display: inline-flex; align-items: center; gap: 4px;"><span class="mock-slot-dot" style="background: ${priStartVal}; box-shadow: 0 0 8px ${priStartVal};"></span> ${window.t ? window.t("theme_editor.preview_input") : "ASS Input"}</span>
                                    <span style="display: inline-flex; align-items: center; gap: 4px;">${window.t ? window.t("theme_editor.preview_output") : "Output"} <span class="mock-slot-dot out" id="theme-mock-slot-out" style="background: ${secStartVal}; box-shadow: 0 0 8px ${secGlowVal};"></span></span>
                                </div>
                                <button type="button" class="mock-widget-btn" id="theme-mock-widget-btn" style="background: linear-gradient(135deg, ${priStartVal} 0%, ${priEndVal} 100%);">${window.t ? window.t("theme_editor.preview_action") : "Execute Action"}</button>
                            </div>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg viewBox="0 0 160 40" style="width: 160px; height: 40px; overflow: visible;">
                                    <path id="theme-mock-wire" d="M 0 20 C 70 20, 90 20, 160 20" fill="none" stroke="${secStartVal}" stroke-width="3.5" stroke-linecap="round" style="filter: drop-shadow(0 0 6px ${secGlowVal});"/>
                                </svg>
                            </div>
                            <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("theme_editor.preview_hint") : "Changes are reflected in real time on this card, canvas, and Pyxis buttons."}</span>
                        </div>
                    </div>
                </div>

                <div class="pyxis-theme-tabs">
                    <button class="pyxis-theme-tab active" data-tab="tab-ui-colors">${window.t ? window.t("theme_editor.tab_ui") : "Interface & Canvas Colors (UI)"}</button>
                    <button class="pyxis-theme-tab" data-tab="tab-cat-colors">${window.t ? window.t("theme_editor.tab_categories") : "Node Headers & Categories"}</button>
                </div>

                <div class="pyxis-theme-editor-content">
                    <div id="tab-ui-colors" class="pyxis-theme-tab-pane active">
                        <div class="theme-editor-grid">
                            ${uiPickersHtml}
                        </div>
                    </div>

                    <div id="tab-cat-colors" class="pyxis-theme-tab-pane">
                        <div class="theme-editor-grid">
                            ${categoryPickersHtml}
                        </div>
                    </div>
                </div>

                <div class="pyxis-modal-actions" style="margin-top: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; gap: 8px;">
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-export" title="${window.t ? window.t("theme_editor.export_tooltip") : "Export theme file to disk"}">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                            <span>${window.t ? window.t("theme_editor.export_btn") : "Export File"}</span>
                        </button>
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-import" title="${window.t ? window.t("theme_editor.import_tooltip") : "Import theme file from disk"}">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                            <span>${window.t ? window.t("theme_editor.import_btn") : "Import File"}</span>
                        </button>
                        ${editingTheme.isCustom ? `
                            <button class="pyxis-btn pyxis-btn-danger" id="btn-theme-delete" title="${window.t ? window.t("theme_editor.delete_tooltip") : "Delete custom theme"}">
                                <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                <span>${window.t ? window.t("theme_editor.delete_btn") : "Delete"}</span>
                            </button>
                        ` : ''}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-cancel">${window.t ? window.t("theme_editor.cancel") : "Cancel"}</button>
                        <button class="pyxis-btn pyxis-btn-primary" id="btn-theme-save">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                            <span>${window.t ? window.t("theme_editor.save") : "Save Theme"}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        function updateLivePreview() {
            editingTheme.name = modal.querySelector("#theme-edit-name").value || "Custom Theme";
            
            const getVal = (id, fallback) => {
                const inp = modal.querySelector(`.pyxis-color-hex-text[data-field-id="${id}"]`);
                return inp ? inp.value : fallback;
            };

            const priStart = getVal("accentPrimary", "#10b981");
            const priEnd = getVal("accentPrimaryEnd", "#3b82f6");
            editingTheme.accentPrimary = priStart;
            editingTheme.accentPrimaryEnd = priEnd;

            const secStart = getVal("accentSecondary", "#6366f1");
            const secGlow = getVal("accentSecondaryGlow", "#818cf8");
            editingTheme.accentSecondary = secStart;
            editingTheme.accentSecondaryGlow = secGlow;
            editingTheme.accentSecondaryEnd = secGlow;

            editingTheme.canvasBg = getVal("canvasBg", "#0d0f12");
            editingTheme.panelBg = getVal("panelBg", "#161b22");
            editingTheme.topbarBg = getVal("topbarBg", editingTheme.panelBg);
            editingTheme.cardBg = getVal("nodeStart", "#181d24");
            editingTheme.inputBg = getVal("inputBg", editingTheme.canvasBg);
            editingTheme.textMain = getVal("textMain", "#ffffff");
            editingTheme.textMuted = getVal("textMuted", "#d1d5db");

            const nodeStart = getVal("nodeStart", "#141a17");
            const nodeEnd = getVal("nodeEnd", editingTheme.canvasBg);
            editingTheme.nodeBgGradient = { start: nodeStart, end: nodeEnd };

            editingTheme.categories = editingTheme.categories || {};
            categoryList.forEach(cat => {
                const colInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="color"]`);
                const gradInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="gradientEnd"]`);
                if (!editingTheme.categories[cat]) editingTheme.categories[cat] = {};
                editingTheme.categories[cat].color = colInp ? colInp.value : "#3b82f6";
                editingTheme.categories[cat].gradientEnd = gradInp ? gradInp.value : (colInp ? colInp.value : "#1d4ed8");
            });

            editingTheme.colors = [editingTheme.canvasBg, editingTheme.panelBg, priStart, secStart];

            const mockCanvas = modal.querySelector("#theme-mock-canvas");
            if (mockCanvas) mockCanvas.style.backgroundColor = editingTheme.canvasBg;

            const mockNode = modal.querySelector("#theme-mock-node");
            if (mockNode) mockNode.style.backgroundColor = nodeStart;

            const mockBody = modal.querySelector("#theme-mock-body");
            if (mockBody) mockBody.style.color = editingTheme.textMain;

            const mathCat = (editingTheme.categories && editingTheme.categories["Math"]) || { color: "#3b82f6", gradientEnd: "#1d4ed8" };
            const c1 = (typeof mathCat === "object" ? mathCat.color : mathCat) || "#3b82f6";
            const c2 = (typeof mathCat === "object" ? (mathCat.gradientEnd || mathCat.color) : mathCat) || "#1d4ed8";
            const mockHeader = modal.querySelector("#theme-mock-header");
            if (mockHeader) mockHeader.style.background = `linear-gradient(90deg, ${c1} 0%, ${c2} 100%)`;

            const mockBtn = modal.querySelector("#theme-mock-widget-btn");
            if (mockBtn) {
                mockBtn.style.background = `linear-gradient(135deg, ${priStart} 0%, ${priEnd} 100%)`;
                mockBtn.style.boxShadow = `0 0 10px ${priStart}55`;
            }

            const mockTitleDot = modal.querySelector("#theme-mock-title-dot");
            if (mockTitleDot) {
                mockTitleDot.style.background = editingTheme.textMuted || "#d1d5db";
                mockTitleDot.style.boxShadow = "none";
            }

            const mockSlotDot = modal.querySelector(".mock-slot-dot");
            if (mockSlotDot && mockSlotDot !== mockTitleDot) {
                mockSlotDot.style.background = priStart;
                mockSlotDot.style.boxShadow = `0 0 8px ${priStart}`;
            }

            const mockSlotOut = modal.querySelector("#theme-mock-slot-out");
            if (mockSlotOut) {
                mockSlotOut.style.background = secStart;
                mockSlotOut.style.boxShadow = `0 0 8px ${secGlow}`;
            }

            const mockWire = modal.querySelector("#theme-mock-wire");
            if (mockWire) {
                mockWire.setAttribute("stroke", secStart);
                mockWire.style.filter = `drop-shadow(0 0 6px ${secGlow})`;
            }

            THEMES[editingTheme.id] = editingTheme;
            applyTheme(editingTheme.id);
        }

        function setFieldColor(targetElem, newHex) {
            let hex = (newHex || "#10B981").toUpperCase();
            if (!hex.startsWith("#")) hex = "#" + hex;

            const container = targetElem.closest(".pyxis-color-field") || targetElem.closest(".theme-editor-cat-card");
            if (!container) return;

            const isCat = targetElem.hasAttribute("data-cat");
            const cat = targetElem.getAttribute("data-cat");
            const prop = targetElem.getAttribute("data-prop");
            const fieldId = targetElem.getAttribute("data-field-id");

            let selector = isCat ? `[data-cat="${cat}"][data-prop="${prop}"]` : `[data-field-id="${fieldId}"]`;
            modal.querySelectorAll(selector).forEach(el => {
                if (el.classList.contains("pyxis-color-chip")) {
                    el.style.backgroundColor = hex;
                } else if (el.classList.contains("pyxis-color-native-input") || el.classList.contains("pyxis-color-hex-text")) {
                    el.value = hex;
                }
            });

            if (isCat) {
                const badge = modal.querySelector(`#cat-badge-${cat}`);
                if (badge) {
                    const colInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="color"]`);
                    const gradInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="gradientEnd"]`);
                    const c1 = colInp ? colInp.value : hex;
                    const c2 = gradInp ? gradInp.value : hex;
                    badge.style.background = `linear-gradient(90deg, ${c1} 0%, ${c2} 100%)`;
                }
            } else if (fieldId === "accentPrimary" || fieldId === "accentPrimaryEnd") {
                const b = modal.querySelector("#ui-badge-pri");
                if (b) {
                    const inp1 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentPrimary"]`);
                    const inp2 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentPrimaryEnd"]`);
                    const v1 = inp1 ? inp1.value : hex;
                    const v2 = inp2 ? inp2.value : hex;
                    b.style.background = `linear-gradient(135deg, ${v1} 0%, ${v2} 100%)`;
                }
            } else if (fieldId === "accentSecondary" || fieldId === "accentSecondaryGlow") {
                const b = modal.querySelector("#ui-badge-sec");
                if (b) {
                    const inp1 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentSecondary"]`);
                    const inp2 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentSecondaryGlow"]`);
                    const v1 = inp1 ? inp1.value : hex;
                    const v2 = inp2 ? inp2.value : hex;
                    b.style.background = v1;
                    b.style.boxShadow = `0 0 10px ${v2}`;
                }
            }

            updateLivePreview();
        }

        modal.querySelectorAll(".pyxis-color-native-input").forEach(inp => {
            inp.addEventListener("input", function() {
                setFieldColor(this, this.value);
            });
        });

        modal.querySelectorAll(".pyxis-color-hex-text").forEach(txt => {
            txt.addEventListener("input", function() {
                let v = this.value.trim();
                if (/^#?[0-9A-Fa-f]{6}$/.test(v)) {
                    if (!v.startsWith("#")) v = "#" + v;
                    setFieldColor(this, v);
                }
            });
            txt.addEventListener("blur", function() {
                let v = this.value.trim();
                if (!/^#?[0-9A-Fa-f]{6}$/.test(v)) {
                    const nativeInp = this.closest(".pyxis-color-field").querySelector(".pyxis-color-native-input");
                    this.value = nativeInp ? nativeInp.value.toUpperCase() : "#FFFFFF";
                }
            });
        });

        modal.querySelectorAll("input[type='text'], input[type='number']").forEach(inp => {
            inp.addEventListener("focus", function() {
                this.select();
            });
            inp.addEventListener("click", function() {
                this.select();
            });
        });

        modal.querySelectorAll(".pyxis-color-pro-btn").forEach(btn => {
            btn.addEventListener("click", function(e) {
                const field = this.closest(".pyxis-color-field");
                const hexInp = field.querySelector(".pyxis-color-hex-text");
                const currentHex = hexInp ? hexInp.value : "#10B981";
                const isCat = this.hasAttribute("data-cat");
                const cat = this.getAttribute("data-cat");
                const title = isCat ? `Color de ${cat}` : (this.getAttribute("data-field-id") || "Selector de Color");

                if (typeof window.showProColorPickerModal === "function") {
                    window.showProColorPickerModal(
                        currentHex,
                        null,
                        title,
                        (savedHex) => setFieldColor(btn, savedHex),
                        e,
                        (liveHex) => setFieldColor(btn, liveHex)
                    );
                } else {
                    const nativeInp = field.querySelector(".pyxis-color-native-input");
                    if (nativeInp) nativeInp.click();
                }
            });
        });

        modal.querySelectorAll(".pyxis-cat-swap-btn").forEach(btn => {
            btn.addEventListener("click", function() {
                const cat = this.getAttribute("data-swap-cat");
                if (cat) {
                    const colInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="color"]`);
                    const gradInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="gradientEnd"]`);
                    if (colInp && gradInp) {
                        const v1 = colInp.value;
                        const v2 = gradInp.value;
                        setFieldColor(colInp, v2);
                        setFieldColor(gradInp, v1);
                    }
                }
            });
        });

        const swapPri = modal.querySelector("#btn-swap-pri");
        if (swapPri) {
            swapPri.onclick = function() {
                const inp1 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentPrimary"]`);
                const inp2 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentPrimaryEnd"]`);
                if (inp1 && inp2) {
                    const v1 = inp1.value;
                    const v2 = inp2.value;
                    setFieldColor(inp1, v2);
                    setFieldColor(inp2, v1);
                }
            };
        }

        const swapSec = modal.querySelector("#btn-swap-sec");
        if (swapSec) {
            swapSec.onclick = function() {
                const inp1 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentSecondary"]`);
                const inp2 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="accentSecondaryGlow"]`);
                if (inp1 && inp2) {
                    const v1 = inp1.value;
                    const v2 = inp2.value;
                    setFieldColor(inp1, v2);
                    setFieldColor(inp2, v1);
                }
            };
        }

        const swapNodeBg = modal.querySelector("#btn-swap-nodebg");
        if (swapNodeBg) {
            swapNodeBg.onclick = function() {
                const inp1 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="nodeStart"]`);
                const inp2 = modal.querySelector(`.pyxis-color-hex-text[data-field-id="nodeEnd"]`);
                if (inp1 && inp2) {
                    const v1 = inp1.value;
                    const v2 = inp2.value;
                    setFieldColor(inp1, v2);
                    setFieldColor(inp2, v1);
                }
            };
        }

        const btnApplyAll = modal.querySelector("#btn-apply-all-categories");
        if (btnApplyAll) {
            btnApplyAll.onclick = function() {
                const globCol = (modal.querySelector("#global-cat-col-inp").value || "#8b5cf6").trim();
                const globGrad = (modal.querySelector("#global-cat-grad-inp").value || globCol).trim();
                categoryList.forEach(cat => {
                    const colInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="color"]`);
                    const gradInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="gradientEnd"]`);
                    if (colInp) setFieldColor(colInp, globCol);
                    if (gradInp) setFieldColor(gradInp, globGrad);
                });
                updateLivePreview();
                if (window.showPyxisToast) window.showPyxisToast("toast.color_applied_all_categories", "success", 2000);
            };
        }

        const globNativeCol = modal.querySelector("#global-cat-native-col");
        const globColInp = modal.querySelector("#global-cat-col-inp");
        const globChipCol = modal.querySelector("#global-cat-chip-col");
        if (globNativeCol && globColInp && globChipCol) {
            globNativeCol.oninput = function() {
                globColInp.value = this.value.toUpperCase();
                globChipCol.style.backgroundColor = this.value;
            };
            globColInp.oninput = function() {
                let v = this.value.trim();
                if (/^#?[0-9A-Fa-f]{6}$/.test(v)) {
                    if (!v.startsWith("#")) v = "#" + v;
                    globNativeCol.value = v;
                    globChipCol.style.backgroundColor = v;
                }
            };
        }

        const globNativeGrad = modal.querySelector("#global-cat-native-grad");
        const globGradInp = modal.querySelector("#global-cat-grad-inp");
        const globChipGrad = modal.querySelector("#global-cat-chip-grad");
        if (globNativeGrad && globGradInp && globChipGrad) {
            globNativeGrad.oninput = function() {
                globGradInp.value = this.value.toUpperCase();
                globChipGrad.style.backgroundColor = this.value;
            };
            globGradInp.oninput = function() {
                let v = this.value.trim();
                if (/^#?[0-9A-Fa-f]{6}$/.test(v)) {
                    if (!v.startsWith("#")) v = "#" + v;
                    globNativeGrad.value = v;
                    globChipGrad.style.backgroundColor = v;
                }
            };
        }

        modal.querySelectorAll(".pyxis-theme-tab").forEach(tabBtn => {
            tabBtn.onclick = function() {
                modal.querySelectorAll(".pyxis-theme-tab").forEach(b => b.classList.remove("active"));
                modal.querySelectorAll(".pyxis-theme-tab-pane").forEach(p => p.classList.remove("active"));
                this.classList.add("active");
                const targetId = this.getAttribute("data-tab");
                const targetPane = modal.querySelector(`#${targetId}`);
                if (targetPane) targetPane.classList.add("active");
            };
        });

        modal.querySelector("#theme-edit-name").addEventListener("input", updateLivePreview);

        modal.querySelector("#theme-edit-preset-select").onchange = function() {
            const baseId = this.value;
            if (DEFAULT_THEMES[baseId]) {
                const preset = DEFAULT_THEMES[baseId];
                
                const setUi = (id, val) => {
                    const el = modal.querySelector(`[data-field-id="${id}"]`);
                    if (el) setFieldColor(el, val);
                };

                setUi("canvasBg", preset.canvasBg);
                setUi("accentPrimary", preset.accentPrimary);
                setUi("accentPrimaryEnd", preset.accentPrimaryEnd || preset.accentSecondary || "#3b82f6");
                setUi("accentSecondary", preset.accentSecondary);
                setUi("accentSecondaryGlow", preset.accentSecondaryGlow || preset.accentSecondary || "#818cf8");
                setUi("panelBg", preset.panelBg);
                setUi("topbarBg", preset.topbarBg || preset.panelBg || "#12161c");
                setUi("inputBg", preset.inputBg || preset.canvasBg || "#12151b");
                setUi("nodeStart", preset.nodeBgGradient ? (preset.nodeBgGradient.start || preset.cardBg) : (preset.cardBg || "#141a17"));
                setUi("nodeEnd", preset.nodeBgGradient ? (preset.nodeBgGradient.end || preset.canvasBg) : "#0c100e");
                setUi("textMain", preset.textMain || "#ffffff");
                setUi("textMuted", preset.textMuted || "#d1d5db");

                categoryList.forEach(cat => {
                    const catData = preset.categories[cat] || { color: "#3b82f6", gradientEnd: "#1d4ed8" };
                    const col = typeof catData === "object" ? catData.color : catData;
                    const grad = typeof catData === "object" ? (catData.gradientEnd || col) : col;

                    const colInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="color"]`);
                    const gradInp = modal.querySelector(`.pyxis-color-hex-text[data-cat="${cat}"][data-prop="gradientEnd"]`);
                    if (colInp) setFieldColor(colInp, col);
                    if (gradInp) setFieldColor(gradInp, grad);
                });

                updateLivePreview();
            }
        };

        modal.querySelector("#btn-theme-export").onclick = function() {
            updateLivePreview();
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.export_theme_dialog === "function") {
                window.pywebview.api.export_theme_dialog(editingTheme).then(res => {
                    if (res && res.success) {
                        if (window.showPyxisToast) window.showPyxisToast("toast.theme_exported", "success", 2600);
                    } else if (res && res.error) {
                        if (window.showPyxisToast) window.showPyxisToast(res.error, "error", 3000);
                    }
                }).catch(err => console.warn("Pyxis: Error exporting theme", err));
            } else {
                const jsonStr = JSON.stringify(editingTheme, null, 2);
                navigator.clipboard.writeText(jsonStr).then(() => {
                    if (window.showPyxisToast) window.showPyxisToast("toast.theme_copied_clipboard", "success", 2400);
                }).catch(() => {
                    if (window.showPyxisToast) window.showPyxisToast("toast.clipboard_copy_error", "error", 2400);
                });
            }
        };

        modal.querySelector("#btn-theme-import").onclick = function() {
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.import_theme_dialog === "function") {
                window.pywebview.api.import_theme_dialog().then(res => {
                    if (res && res.success && res.theme) {
                        saveCustomTheme(res.theme);
                        if (window.showPyxisToast) {
                            const name = res.theme.name || "";
                            const msg = window.t ? window.t("toast.theme_imported_activated", { name }) : `Theme "${name}" imported and activated`;
                            window.showPyxisToast(msg, "success", 2600);
                        }
                        modal.remove();
                        openSettingsModal();
                    } else if (res && res.error) {
                        if (window.showPyxisToast) window.showPyxisToast(res.error, "error", 3000);
                    }
                }).catch(err => console.warn("Pyxis: Error importing theme", err));
            } else {
                if (window.showPyxisToast) window.showPyxisToast("toast.import_requires_api", "warning", 3000);
            }
        };

        const delBtn = modal.querySelector("#btn-theme-delete");
        if (delBtn) {
            delBtn.onclick = function() {
                const themeName = editingTheme.name || "";
                showPyxisConfirm({
                    title: window.t ? window.t("theme_editor.delete_confirm_title") : "Delete Custom Theme",
                    message: window.t ? window.t("theme_editor.delete_confirm_msg", { name: themeName }) : `Are you sure you want to permanently delete theme <strong>"${themeName}"</strong>? This action cannot be undone.`,
                    confirmText: window.t ? window.t("theme_editor.delete_theme_btn") : "Delete Theme",
                    cancelText: window.t ? window.t("common.cancel") : "Cancel",
                    isDanger: true,
                    onConfirm: async () => {
                        await deleteCustomTheme(editingTheme.id);
                        modal.remove();
                        await openSettingsModal();
                        if (window.showPyxisToast) {
                            const name = editingTheme.name || "";
                            const msg = window.t ? window.t("toast.theme_deleted", { name }) : `Theme "${name}" deleted`;
                            window.showPyxisToast(msg, "info", 2400);
                        }
                    }
                });
            };
        }

        modal.querySelector("#btn-theme-cancel").onclick = async function() {
            applyTheme(activeThemeBeforeEdit);
            modal.remove();
            await openSettingsModal();
        };
        modal.querySelector("#btn-close-theme-editor").onclick = async function() {
            applyTheme(activeThemeBeforeEdit);
            modal.remove();
            await openSettingsModal();
        };

        modal.querySelector("#btn-theme-save").onclick = async function() {
            updateLivePreview();
            await saveCustomTheme(editingTheme, true);
            modal.remove();
            await openSettingsModal();
            if (window.showPyxisToast) {
                const toastMsg = window.t
                    ? window.t("toast.theme_saved_applied", { name: editingTheme.name })
                    : `Theme "${editingTheme.name}" saved and applied`;
                window.showPyxisToast(toastMsg, "success", 2600);
            }
        };

        updateLivePreview();
    }

    async function openSettingsModal() {
        if (window.LiteGraph && typeof window.LiteGraph.closeAllContextMenus === "function") {
            window.LiteGraph.closeAllContextMenus();
        }
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_custom_themes === "function") {
            try {
                await syncCustomThemesWithBackend();
            } catch(e) {}
        }

        const existing = document.getElementById("pyxis-settings-modal");
        if (existing) existing.remove();

        const modal = document.createElement("div");
        modal.id = "pyxis-settings-modal";
        modal.className = "pyxis-modal-overlay";

        const customThemeKeys = Object.keys(customThemes);
        let customListHtml = "";
        if (customThemeKeys.length > 0) {
            customListHtml = customThemeKeys.map(key => {
                const t = customThemes[key];
                const isActive = t.id === currentTheme;
                const swatches = (t.colors || [t.canvasBg || "#0d0f12", t.panelBg || "#161b22", t.accentPrimary || "#10b981", t.accentSecondary || "#6366f1"]).slice(0, 4);
                return `
                    <div class="pyxis-theme-list-row ${isActive ? 'active' : ''}" data-theme-id="${t.id}">
                        <div class="pyxis-theme-row-left">
                            <div class="pyxis-theme-radio"><span class="pyxis-theme-radio-inner"></span></div>
                            <div class="pyxis-theme-row-info">
                                <div class="pyxis-theme-row-name">
                                    <span>${t.name}</span>
                                    <span class="pyxis-theme-badge-custom">${window.t ? window.t("settings.badge_custom") : "Custom"}</span>
                                </div>
                                <div class="pyxis-theme-row-desc">${t.desc || (window.t ? window.t("settings.empty_custom_desc") : 'Saved custom theme')}</div>
                            </div>
                        </div>
                        <div class="pyxis-theme-row-right">
                            <div class="pyxis-theme-swatches">
                                ${swatches.map(c => `<div class="pyxis-theme-swatch" style="background:${c}"></div>`).join('')}
                            </div>
                            <div class="pyxis-theme-row-actions">
                                <button type="button" class="pyxis-theme-action-btn btn-edit-theme" data-theme-id="${t.id}" title="${window.t ? window.t("settings.edit_theme") : "Edit this theme"}">
                                    <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                                    <span>${window.t ? window.t("common.edit") : "Edit"}</span>
                                </button>
                                <button type="button" class="pyxis-theme-action-btn delete btn-delete-theme" data-theme-id="${t.id}" title="${window.t ? window.t("settings.delete_theme") : "Delete this theme"}">
                                    <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            customListHtml = `<div class="pyxis-theme-empty-state">${window.t ? window.t("settings.empty_custom_themes") : "No custom themes saved yet. Click \"+ Create New Theme\" to design your own."}</div>`;
        }

        let defaultListHtml = Object.keys(DEFAULT_THEMES).map(key => {
            const t = DEFAULT_THEMES[key];
            const isActive = t.id === currentTheme;
            const swatches = (t.colors || [t.canvasBg || "#0d0f12", t.panelBg || "#161b22", t.accentPrimary || "#10b981", t.accentSecondary || "#6366f1"]).slice(0, 4);
            return `
                <div class="pyxis-theme-list-row ${isActive ? 'active' : ''}" data-theme-id="${t.id}">
                    <div class="pyxis-theme-row-left">
                        <div class="pyxis-theme-radio"><span class="pyxis-theme-radio-inner"></span></div>
                        <div class="pyxis-theme-row-info">
                            <div class="pyxis-theme-row-name">
                                <span>${t.name}</span>
                            </div>
                            <div class="pyxis-theme-row-desc">${t.desc || (window.t ? window.t("settings.official_theme") : 'Official Pyxis Theme')}</div>
                        </div>
                    </div>
                    <div class="pyxis-theme-row-right">
                        <div class="pyxis-theme-swatches">
                            ${swatches.map(c => `<div class="pyxis-theme-swatch" style="background:${c}"></div>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        const bgSettings = window.backgroundImageSettings || {};
        const hasBg = !!(bgSettings.dataUrl || bgSettings.videoUrl || bgSettings.hasBg);
        let bgPathDisplay = window.t ? window.t("settings.bg_none") : 'None selected';
        if (hasBg) {
            if (bgSettings.mediaType === 'video' || bgSettings.videoUrl) {
                bgPathDisplay = window.t ? window.t("settings.bg_video") : 'Active looping video (GPU Accelerated)';
            } else if (bgSettings.isDefault) {
                bgPathDisplay = window.t ? window.t("settings.bg_default") : 'Default background (default_back.webp)';
            } else {
                bgPathDisplay = window.t ? window.t("settings.bg_image") : 'Loaded image';
            }
        }

        modal.innerHTML = `
            <div class="pyxis-modal-dialog pyxis-settings-dialog">
                <div class="pyxis-modal-header" style="display: flex; align-items: center; justify-content: space-between;">
                    <div class="pyxis-modal-title">
                        <svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        <span>${window.t ? window.t("settings.title") : "Settings & Visual Themes"}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button type="button" class="pyxis-btn pyxis-btn-lang" id="btn-settings-lang-toggle" title="${window.t ? window.t('topbar.lang_tooltip') : 'Switch language (Español / English)'}" style="display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; background: var(--bg-input, #1e293b); border: 1px solid var(--border-subtle, #334155); color: var(--text-main, #f8fafc); cursor: pointer; font-size: 11px; font-weight: 600;">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width: 14px; height: 14px; stroke: currentColor;"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                            <span class="pyxis-lang-pill ${(window.PyxisI18n && window.PyxisI18n.currentLang === 'es') ? 'active' : ''}" data-lang="es" style="padding: 1px 4px; border-radius: 3px; ${(window.PyxisI18n && window.PyxisI18n.currentLang === 'es') ? 'background: var(--accent-primary, #10b981); color: #fff;' : 'opacity: 0.6;'}">ES</span>
                            <span style="opacity: 0.35; font-size: 10px;">|</span>
                            <span class="pyxis-lang-pill ${(window.PyxisI18n && window.PyxisI18n.currentLang === 'en') ? 'active' : ''}" data-lang="en" style="padding: 1px 4px; border-radius: 3px; ${(window.PyxisI18n && window.PyxisI18n.currentLang === 'en') ? 'background: var(--accent-primary, #10b981); color: #fff;' : 'opacity: 0.6;'}">EN</span>
                        </button>
                        <button class="pyxis-modal-close" id="btn-close-settings">
                            <svg class="svg-icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                </div>
                
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <div style="font-size: 13px; font-weight: 600; color: var(--text-main);">${window.t ? window.t("settings.themes_section") : "Interface Visual Themes:"}</div>
                    <button class="pyxis-btn pyxis-btn-primary" id="btn-open-theme-editor" style="padding: 4px 10px; font-size: 12px; display: flex; align-items: center; gap: 5px;">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:13px; height:13px;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        <span>${window.t ? window.t("settings.create_theme") : "Create New Theme"}</span>
                    </button>
                </div>

                <div class="pyxis-theme-list-wrapper">
                    <!-- Saved by you -->
                    <div class="pyxis-theme-list-section">
                        <div class="pyxis-theme-list-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;stroke:var(--accent-primary);"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                            <span>${window.t ? window.t("settings.saved_by_you") : "Saved by you"}</span>
                        </div>
                        ${customListHtml}
                    </div>

                    <!-- Preset Themes -->
                    <div class="pyxis-theme-list-section" style="margin-top: 6px;">
                        <div class="pyxis-theme-list-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
                            <span>${window.t ? window.t("settings.presets") : "Preset Themes"}</span>
                        </div>
                        ${defaultListHtml}
                    </div>
                </div>

                <!-- Canvas Customization Section -->
                <div style="margin-top: 15px; border-top: 1px solid var(--border-subtle); padding-top: 15px;">
                    <div style="font-weight: 600; font-size: 14px; color: var(--text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: var(--accent-primary); width:18px; height:18px;"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                        <span>${window.t ? window.t("settings.canvas_section") : "Canvas & Background Media Customization"}</span>
                    </div>

                    <!-- Persistencia en Segundo Plano (Daemon) -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;" title="${window.t ? window.t("settings.daemon_tooltip") : "Keeps Python server in background (~60MB RAM) for instant Pyxis launch (0ms) from Aegisub."}">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: 13px; color: var(--text-main); font-weight: 500;">${window.t ? window.t("settings.daemon") : "Background Persistence:"}</span>
                            <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.daemon_desc") : "Instant launch (0ms) after first start"}</span>
                        </div>
                        <input type="checkbox" id="setting-daemon-mode" name="setting-daemon-mode" ${window.pyxisDaemonMode !== false ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--accent-primary);">
                    </div>

                    <!-- Estilo de Rejilla -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.grid_style") : "Grid Style:"}</span>
                        <select id="setting-grid-mode" name="setting-grid-mode" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 160px;">
                            <option value="0" ${window.gridMode === 0 ? 'selected' : ''}>${window.t ? window.t("settings.grid_lines") : "Lines"}</option>
                            <option value="1" ${window.gridMode === 1 ? 'selected' : ''}>${window.t ? window.t("settings.grid_dots") : "Puntos (Defecto)"}</option>
                            <option value="2" ${window.gridMode === 2 ? 'selected' : ''}>${window.t ? window.t("settings.grid_disabled") : "Desactivado"}</option>
                        </select>
                    </div>

                    <!-- Pasos de Deshacer / Rehacer -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.undo_steps") : "Undo / Redo steps:"}</span>
                        <input type="number" id="setting-undo-steps" name="setting-undo-steps" min="5" max="100" value="${window.PyxisUndoManager ? window.PyxisUndoManager.getMaxSteps() : 30}" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 80px; text-align: center;">
                    </div>

                    <!-- Media Background (Images and Cyclic Videos) -->
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <div style="display: flex; flex-direction: column;">
                                <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.canvas_bg") : "Canvas Background (Image or Cyclic Video):"}</span>
                                <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.canvas_bg_formats") : "Supports MP4, WebM, MOV, MKV, PNG, JPG, WebP"}</span>
                            </div>
                            <div style="display: gap: 6px;">
                                <button class="pyxis-btn" id="btn-browse-bg" style="padding: 4px 10px; font-size: 12px; display: inline-flex; align-items: center;">${window.t ? window.t("settings.browse") : "Browse..."}</button>
                                <button class="pyxis-btn pyxis-btn-danger" id="btn-clear-bg" style="padding: 4px 10px; font-size: 12px; display: ${hasBg ? 'inline-block' : 'none'};">${window.t ? window.t("settings.remove") : "Remove"}</button>
                            </div>
                        </div>
                        <input type="text" id="setting-bg-path" name="setting-bg-path" readonly value="${bgPathDisplay}" style="background: var(--bg-input); color: var(--text-muted); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 11px; width: 100%; box-sizing: border-box; font-family: var(--font-mono); outline: none;">
                    </div>

                    <!-- Convert / Optimize Video with FFmpeg -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;" title="${window.t ? window.t("settings.optimize_video_tooltip") : "Optimizes video to lightweight H.264/MP4 without audio for maximum smoothness and minimal GPU/CPU load."}">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: 13px; color: var(--text-main); font-weight: 500;">${window.t ? window.t("settings.optimize_video") : "Convert / Optimize Video with FFmpeg"}</span>
                            <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.daemon_desc") : "Recommended for optimal smoothness"}</span>
                        </div>
                        <input type="checkbox" id="setting-convert-video" name="setting-convert-video" ${window.convertVideoSetting !== false ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--accent-primary);">
                    </div>

                    <!-- Fit Mode & Opacity -->
                    <div id="bg-options-panel" style="display: ${hasBg ? 'block' : 'none'};">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.fit_mode") : "Fit Mode:"}</span>
                            <select id="setting-bg-mode" name="setting-bg-mode" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 160px;">
                                <option value="cover" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'cover') ? 'selected' : ''}>${window.t ? window.t("settings.fit_cover") : "Cover"}</option>
                                <option value="contain" ${(window.backgroundImageSettings && (window.backgroundImageSettings.mode === 'contain' || !window.backgroundImageSettings.mode)) ? 'selected' : ''}>${window.t ? window.t("settings.fit_contain") : "Contain"}</option>
                                <option value="stretch" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'stretch') ? 'selected' : ''}>${window.t ? window.t("settings.fit_stretch") : "Stretch"}</option>
                                <option value="tile" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'tile') ? 'selected' : ''}>${window.t ? window.t("settings.fit_tile") : "Tile"}</option>
                                <option value="center" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'center') ? 'selected' : ''}>${window.t ? window.t("settings.fit_center") : "Center"}</option>
                            </select>
                        </div>

                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.opacity") : "Background Opacity:"}</span>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="range" id="setting-bg-opacity" name="setting-bg-opacity" min="0" max="100" value="${window.backgroundImageSettings ? Math.round(window.backgroundImageSettings.opacity * 100) : 85}" style="width: 110px; cursor: pointer; accent-color: var(--accent-primary);">
                                <span id="bg-opacity-label" style="font-size: 12px; color: var(--text-main); font-family: var(--font-mono); min-width: 32px; text-align: right;">${window.backgroundImageSettings ? Math.round(window.backgroundImageSettings.opacity * 100) : 85}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                    <button class="pyxis-btn pyxis-btn-secondary" id="btn-clean-temp-cache" style="font-size: 12px; padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px;" title="${window.t ? window.t("settings.clean_temp_tooltip") : "Cleans temporary files and cache fragments older than 72 hours without affecting backgrounds or settings"}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                        <span>${window.t ? window.t("settings.clean_temp") : "Clean Temp Files (> 72h)"}</span>
                    </button>
                    <button class="pyxis-btn pyxis-btn-primary" id="btn-done-settings">${window.t ? window.t("common.confirm") : "Done"}</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelectorAll(".pyxis-theme-list-row").forEach(row => {
            row.onclick = function(e) {
                if (e.target.closest(".pyxis-theme-action-btn")) return;
                const selected = this.getAttribute("data-theme-id");
                applyTheme(selected);
                saveConfig();
                openSettingsModal();
            };
        });

        modal.querySelectorAll(".btn-edit-theme").forEach(btn => {
            btn.onclick = function(e) {
                e.stopPropagation();
                const themeId = this.getAttribute("data-theme-id");
                modal.remove();
                openThemeEditorModal(themeId);
            };
        });

        modal.querySelectorAll(".btn-delete-theme").forEach(btn => {
            btn.onclick = function(e) {
                e.stopPropagation();
                const themeId = this.getAttribute("data-theme-id");
                const tName = customThemes[themeId] ? customThemes[themeId].name : "this theme";
                showPyxisConfirm({
                    title: window.t ? window.t("theme_editor.delete_confirm_title") : "Delete Custom Theme",
                    message: window.t ? window.t("theme_editor.delete_confirm_msg", { name: tName }) : `Are you sure you want to permanently delete theme <strong>"${tName}"</strong>? This action cannot be undone.`,
                    confirmText: window.t ? window.t("theme_editor.delete_theme_btn") : "Delete Theme",
                    cancelText: window.t ? window.t("common.cancel") : "Cancel",
                    isDanger: true,
                    onConfirm: async () => {
                        await deleteCustomTheme(themeId);
                        await openSettingsModal();
                        if (window.showPyxisToast) {
                            const msg = window.t ? window.t("toast.theme_deleted", { name: tName }) : `Theme "${tName}" deleted`;
                            window.showPyxisToast(msg, "info", 2400);
                        }
                    }
                });
            };
        });

        const openEditorBtn = modal.querySelector("#btn-open-theme-editor");
        if (openEditorBtn) {
            openEditorBtn.onclick = function() {
                modal.remove();
                openThemeEditorModal();
            };
        }

        const langToggleBtn = modal.querySelector("#btn-settings-lang-toggle");
        if (langToggleBtn) {
            langToggleBtn.onclick = function(e) {
                e.stopPropagation();
                if (window.PyxisI18n) {
                    window.PyxisI18n.toggleLanguage();
                    modal.remove();
                    openSettingsModal();
                }
            };
        }

        const daemonCheck = modal.querySelector("#setting-daemon-mode");
        if (daemonCheck) {
            daemonCheck.onchange = function() {
                window.pyxisDaemonMode = this.checked;
                saveConfig();
            };
        }

        const convertVideoCheck = modal.querySelector("#setting-convert-video");
        if (convertVideoCheck) {
            convertVideoCheck.onchange = function() {
                window.convertVideoSetting = this.checked;
                saveConfig();
            };
        }

        const gridSelect = modal.querySelector("#setting-grid-mode");
        gridSelect.onchange = function() {
            window.gridMode = parseInt(this.value);
            if (window.canvas) {
                window.canvas.setDirty(true, true);
            }
            saveConfig();
        };

        const undoStepsInput = modal.querySelector("#setting-undo-steps");
        if (undoStepsInput) {
            undoStepsInput.onchange = function() {
                if (window.PyxisUndoManager) {
                    window.PyxisUndoManager.setMaxSteps(this.value);
                }
                saveConfig();
            };
        }

        const bgModeSelect = modal.querySelector("#setting-bg-mode");
        bgModeSelect.onchange = function() {
            if (window.backgroundImageSettings) {
                window.backgroundImageSettings.mode = this.value;
                if (window.updateBgMediaElement) window.updateBgMediaElement();
                if (window.canvas) window.canvas.setDirty(true, true);
            }
            saveConfig();
        };

        const bgOpacitySlider = modal.querySelector("#setting-bg-opacity");
        const bgOpacityLabel = modal.querySelector("#bg-opacity-label");
        bgOpacitySlider.oninput = function() {
            const val = parseInt(this.value) / 100;
            bgOpacityLabel.innerText = this.value + "%";
            if (window.backgroundImageSettings) {
                window.backgroundImageSettings.opacity = val;
                if (window.updateBgMediaElement) window.updateBgMediaElement();
                if (window.canvas) window.canvas.setDirty(true, true);
            }
            saveConfig();
        };

        const browseBtn = modal.querySelector("#btn-browse-bg");
        browseBtn.onclick = function() {
            if (window.pywebview && window.pywebview.api) {
                const shouldConvert = window.convertVideoSetting !== false;
                const origBtnHtml = browseBtn.innerHTML;
                const pathInput = modal.querySelector("#setting-bg-path");
                const prevPathVal = pathInput ? pathInput.value : "";

                browseBtn.disabled = true;
                browseBtn.style.opacity = "0.75";
                browseBtn.innerHTML = `<svg class="svg-icon pyxis-spin" viewBox="0 0 24 24" style="width:13px;height:13px;margin-right:4px;"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> ${window.t ? window.t("common.loading") : "Processing..."}`;
                if (pathInput) pathInput.value = shouldConvert ? (window.t ? window.t("settings.converting_video") : "Converting and optimizing video with FFmpeg...") : (window.t ? window.t("settings.loading_media") : "Loading background media...");

                let loadingToast = null;
                if (window.showPyxisToast) {
                    loadingToast = window.showPyxisToast(
                        shouldConvert ? "toast.converting_bg_video" : "toast.loading_bg_media",
                        "loading",
                        0
                    );
                }

                const selectFn = typeof window.pywebview.api.select_bg_media === "function" 
                    ? () => window.pywebview.api.select_bg_media(shouldConvert)
                    : () => window.pywebview.api.select_bg_image();

                selectFn().then(res => {
                    if (loadingToast && typeof loadingToast.close === "function") {
                        loadingToast.close();
                    }
                    browseBtn.disabled = false;
                    browseBtn.style.opacity = "1";
                    browseBtn.innerHTML = origBtnHtml;

                    if (res && (res.success || (typeof res === "string" && res.length > 0))) {
                        window.backgroundImageSettings = window.backgroundImageSettings || {};
                        if (typeof res === "object") {
                            window.backgroundImageSettings.hasBg = !!res.has_bg;
                            window.backgroundImageSettings.mediaType = res.media_type || "image";
                            window.backgroundImageSettings.videoUrl = res.video_url || "";
                            window.backgroundImageSettings.posterUrl = res.poster_url || "";
                            window.backgroundImageSettings.dataUrl = res.data_url || "";
                        } else {
                            window.backgroundImageSettings.hasBg = true;
                            window.backgroundImageSettings.mediaType = res.startsWith("http") ? "video" : "image";
                            if (res.startsWith("http")) {
                                window.backgroundImageSettings.videoUrl = res;
                            } else {
                                window.backgroundImageSettings.dataUrl = res;
                            }
                        }

                        window.backgroundImageSettings.mode = window.backgroundImageSettings.mode || "cover";
                        window.backgroundImageSettings.opacity = window.backgroundImageSettings.opacity !== undefined ? window.backgroundImageSettings.opacity : 0.5;

                        const isVideo = window.backgroundImageSettings.mediaType === "video";
                        if (pathInput) {
                            pathInput.value = isVideo 
                                ? (window.t ? window.t("settings.bg_video") : "Active looping video (GPU Accelerated)") 
                                : (window.t ? window.t("settings.bg_image") : "Loaded image");
                        }
                        const clearBtnEl = modal.querySelector("#btn-clear-bg");
                        if (clearBtnEl) clearBtnEl.style.display = "inline-block";
                        const optsPanel = modal.querySelector("#bg-options-panel");
                        if (optsPanel) optsPanel.style.display = "block";

                        if (window.updateBgMediaElement) window.updateBgMediaElement();
                        if (window.canvas) window.canvas.setDirty(true, true);
                        saveConfig();

                        if (window.showPyxisToast) {
                            if (isVideo) {
                                const isConverted = (typeof res === "object" && res.converted);
                                const msgKey = isConverted ? "toast.bg_video_converted_applied" : "toast.bg_video_applied";
                                const fallback = isConverted ? "Background video converted and applied successfully" : "Background video applied successfully";
                                const msg = window.t ? window.t(msgKey) : fallback;
                                window.showPyxisToast(msg, "success", 2800);
                            } else {
                                window.showPyxisToast("toast.bg_image_applied", "success", 2800);
                            }
                        }
                    } else if (res && res.cancelled) {
                        if (pathInput) pathInput.value = prevPathVal;
                    } else {
                        if (pathInput) pathInput.value = prevPathVal;
                        if (window.showPyxisToast) window.showPyxisToast("toast.bg_select_error", "error", 2800);
                    }
                }).catch(err => {
                    if (loadingToast && typeof loadingToast.close === "function") {
                        loadingToast.close();
                    }
                    browseBtn.disabled = false;
                    browseBtn.style.opacity = "1";
                    browseBtn.innerHTML = origBtnHtml;
                    if (pathInput) pathInput.value = prevPathVal;
                    console.error("Pyxis error selecting media:", err);
                    if (window.showPyxisToast) window.showPyxisToast("toast.bg_process_error", "error", 2800);
                });
            }
        };

        const clearBtn = modal.querySelector("#btn-clear-bg");
        clearBtn.onclick = function() {
            if (window.backgroundImageSettings) {
                window.backgroundImageSettings.dataUrl = "";
                window.backgroundImageSettings.videoUrl = "";
                window.backgroundImageSettings.posterUrl = "";
                window.backgroundImageSettings.hasBg = false;
                window.backgroundImageSettings.mediaType = "none";
                window.backgroundImageSettings.isDefault = false;
                modal.querySelector("#setting-bg-path").value = window.t ? window.t("settings.bg_none") : "None selected";
                this.style.display = "none";
                modal.querySelector("#bg-options-panel").style.display = "none";

                if (window.updateBgMediaElement) window.updateBgMediaElement();
                if (window.canvas) window.canvas.setDirty(true, true);
                saveConfig(true);
            }
        };

        const cleanTempBtn = modal.querySelector("#btn-clean-temp-cache");
        if (cleanTempBtn) {
            cleanTempBtn.onclick = async function() {
                try {
                    cleanTempBtn.disabled = true;
                    cleanTempBtn.style.opacity = "0.5";
                    if (window.pywebview && window.pywebview.api && window.pywebview.api.clean_temp_cache) {
                        const res = await window.pywebview.api.clean_temp_cache(72, false);
                        const count = (res && res.cleaned_files) || 0;
                        const mb = (res && res.freed_bytes) ? (res.freed_bytes / (1024 * 1024)).toFixed(2) : "0.00";
                        if (window.showPyxisToast) {
                            const msg = count > 0 
                                ? (window.t ? window.t("toast.temp_clean_summary", { count, mb }) : `Cleanup completed: ${count} file(s) deleted (${mb} MB freed)`)
                                : (window.t ? window.t("toast.temp_clean_none") : "No temporary files older than 72 hours to purge");
                            window.showPyxisToast(msg, "info", 3000);
                        }
                    } else {
                        if (window.showPyxisToast) window.showPyxisToast("toast.clean_completed", "info", 2000);
                    }
                } catch (e) {
                    console.error("Pyxis: Error cleaning temporary cache:", e);
                } finally {
                    cleanTempBtn.disabled = false;
                    cleanTempBtn.style.opacity = "1";
                }
            };
        }

        modal.querySelectorAll("input[type='text'], input[type='number']").forEach(inp => {
            inp.addEventListener("focus", function() {
                this.select();
            });
            inp.addEventListener("click", function() {
                this.select();
            });
        });

        modal.querySelector("#btn-close-settings").onclick = () => modal.remove();
        modal.querySelector("#btn-done-settings").onclick = () => modal.remove();
    }

    window.addEventListener("pyxis:languageChanged", function() {
        const modal = document.getElementById("pyxis-settings-modal");
        if (modal && window.PyxisI18n && typeof window.PyxisI18n.applyToDOM === "function") {
            window.PyxisI18n.applyToDOM(modal);
        }
    });

    applyTheme(currentTheme);
    syncCustomThemesWithBackend();

    window.PyxisThemeManager = {
        THEMES: THEMES,
        DEFAULT_THEMES: DEFAULT_THEMES,
        getAllThemes: getAllThemes,
        applyTheme: applyTheme,
        openSettingsModal: openSettingsModal,
        openThemeEditorModal: openThemeEditorModal,
        saveCustomTheme: saveCustomTheme,
        deleteCustomTheme: deleteCustomTheme,
        getCurrentTheme: () => currentTheme,
        saveConfig: saveConfig,
        syncCustomThemesWithBackend: syncCustomThemesWithBackend
    };
})(window);
