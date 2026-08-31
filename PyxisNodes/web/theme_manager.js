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

/* =============================================================================
   Pyxis Theme Manager & Dynamic Node Palette Engine - v1.0.5
   Includes: Theme Engine, Interactive Custom Theme Editor & Media Backgrounds
   ============================================================================= */
(function (window) {
    "use strict";

    // Helper universal para resolver la categoría estándar de cualquier nodo
    window.getNodeCategory = function(nodeOrType) {
        if (!nodeOrType) return "Functions";
        const typeStr = typeof nodeOrType === "string" ? nodeOrType : (nodeOrType.type || nodeOrType.title || "");
        if (typeStr.includes("/")) {
            const cat = typeStr.split("/")[0].trim();
            if (cat) return cat;
        }
        const name = typeStr.trim();
        if (name === "Main Loop" || name === "MaxLoop" || name === "Module") return "Loops";
        if (name === "Output" || name === "Previewer" || name === "Benchmark Math" || name === "Script Code" || name === "Cód Script") return "System";
        if (name === "Define Vars" || name === "Get Var" || name === "Memory" || name === "Sys Var") return "Variables";
        if (name === "Text on Path" || name === "Texto en trazado" || name === "Bezier Curve" || name === "Interpolator" || name === "Conditioner" || name === "Color Gradient") return "Functions";
        if (name === "String" || name === "Concatenate" || name === "Dynamic Format") return "String";
        if (name === "Text" || (name.startsWith("Text ") && name !== "Text on Path")) return "Text";
        if (name === "MultiTag" || name === "Tag Oscillator") return "Tags";
        if (name === "Math" || name === "Number" || name === "Number" || name === "Color Picker" || name === "MultiRandom") return "Math";
        if (name === "Shapes Library" || name === "Shape Slicer" || name === "Shape Transform" || name === "Shape Stroke" || name === "Concentric Borders" || name === "IMG to Shape") return "Shape";
        if (name === "Audio Modulator" || name === "Audio Waveform") return "Audio";
        if (name === "Lead In" || name === "Lead Out" || name === "Middle 1" || name === "Middle 2" || name === "Loop 1" || name === "Loop 2" || name === "Time Ipol" || name === "Synced Time" || name === "Offset" || name === "Duración" || name === "Parse ASS Time" || name === "Format ASS Time") return "Time";
        if (name === "Particles" || name === "IMG to pixels") return "Particles";
        return "Functions";
    };

    const DEFAULT_THEMES = {
        teal: {
            id: "teal",
            name: "Oceanic Teal",
            desc: "Paleta verde azulado, pizarra y azul marino",
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
                "Loops": { color: "#22858C", gradientEnd: "#2ba6af" },
                "System": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Variables": { color: "#3A628C", gradientEnd: "#497bb0" },
                "String": { color: "#6A778C", gradientEnd: "#8492aa" },
                "Text": { color: "#6A778C", gradientEnd: "#8492aa" },
                "Math": { color: "#548C87", gradientEnd: "#67aba5" },
                "Functions": { color: "#22858C", gradientEnd: "#2ba6af" },
                "Shape": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Time": { color: "#3A628C", gradientEnd: "#497bb0" },
                "Tags": { color: "#548C87", gradientEnd: "#67aba5" },
                "Audio": { color: "#22858C", gradientEnd: "#2ba6af" },
                "Particles": { color: "#105A8C", gradientEnd: "#1775b3" },
                "Meta": { color: "#548C87", gradientEnd: "#67aba5" }
            }
        },
        violet: {
            id: "violet",
            name: "Twilight Violet",
            desc: "Paleta amatista, violeta e índigo profundo",
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
                "Loops": { color: "#67298C", gradientEnd: "#8439b0" },
                "System": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Variables": { color: "#83558C", gradientEnd: "#9e6ba8" },
                "String": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Text": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Math": { color: "#663F8C", gradientEnd: "#8052ad" },
                "Functions": { color: "#67298C", gradientEnd: "#8439b0" },
                "Shape": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Time": { color: "#83558C", gradientEnd: "#9e6ba8" },
                "Tags": { color: "#663F8C", gradientEnd: "#8052ad" },
                "Audio": { color: "#6F6A8C", gradientEnd: "#8782a6" },
                "Particles": { color: "#452E8C", gradientEnd: "#5d3fb8" },
                "Meta": { color: "#83558C", gradientEnd: "#9e6ba8" }
            }
        },
        crimson: {
            id: "crimson",
            name: "Crimson Ember",
            desc: "Paleta carmesí, vino, ámbar y terracota",
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
                "Loops": { color: "#8C3B19", gradientEnd: "#a64d24" },
                "System": { color: "#8C1B0D", gradientEnd: "#b02615" },
                "Variables": { color: "#8C0E5B", gradientEnd: "#ad1774" },
                "String": { color: "#8C3742", gradientEnd: "#a84754" },
                "Text": { color: "#8C3742", gradientEnd: "#a84754" },
                "Math": { color: "#8C5C3C", gradientEnd: "#a8714c" },
                "Functions": { color: "#8C0E5B", gradientEnd: "#ad1774" },
                "Shape": { color: "#8C3742", gradientEnd: "#a84754" },
                "Time": { color: "#8C3B19", gradientEnd: "#a64d24" },
                "Tags": { color: "#8C1B0D", gradientEnd: "#b02615" },
                "Audio": { color: "#8C5C3C", gradientEnd: "#a8714c" },
                "Particles": { color: "#8C1B0D", gradientEnd: "#b02615" },
                "Meta": { color: "#8C3B19", gradientEnd: "#a64d24" }
            }
        }
    };

    function showPyxisConfirm(options = {}) {
        const {
            title = (window.t ? window.t("common.confirm") : "Confirmación"),
            message = (window.t ? window.t("common.confirm_question", null, "¿Estás seguro de realizar esta acción?") : "¿Estás seguro de realizar esta acción?"),
            confirmText = (window.t ? window.t("common.confirm") : "Aceptar"),
            cancelText = (window.t ? window.t("common.cancel") : "Cancelar"),
            isDanger = true,
            onConfirm = null,
            onCancel = null
        } = options;

        const existing = document.getElementById("pyxis-confirm-modal");
        if (existing) existing.remove();

        const overlay = document.createElement("div");
        overlay.id = "pyxis-confirm-modal";
        overlay.className = "pyxis-modal-overlay";
        overlay.style.setProperty("z-index", "100000000", "important");

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

    function applyTheme(themeId) {
        if (!THEMES[themeId]) themeId = "teal";
        currentTheme = themeId;
        localStorage.setItem("pyxis_theme", themeId);
        document.documentElement.setAttribute("data-theme", themeId);

        const themeData = THEMES[themeId];
        window.PYXIS_THEME = themeData;

        const root = document.documentElement;
        
        // Aplicar variables CSS completas tanto para temas oficiales como personalizados
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

        // Acentos y Degradados de Botones e Interfaz
        const priStart = themeData.accentPrimary || "#10b981";
        const priEnd = themeData.accentPrimaryEnd || themeData.accentSecondary || "#3b82f6";
        root.style.setProperty("--accent-primary", priStart);
        root.style.setProperty("--accent-primary-hover", priStart);
        root.style.setProperty("--accent-primary-end", priEnd);
        root.style.setProperty("--accent-gradient", `linear-gradient(135deg, ${priStart} 0%, ${priEnd} 100%)`);
        root.style.setProperty("--accent-glow", priStart + "66");
        root.style.setProperty("--border-highlight", priStart + "80");
        root.style.setProperty("--border-subtle", "rgba(255, 255, 255, 0.12)");

        const secStart = themeData.accentSecondary || "#6366f1";
        const secGlow = themeData.accentSecondaryGlow || themeData.accentSecondaryEnd || themeData.accentSecondary || "#818cf8";
        root.style.setProperty("--accent-secondary", secStart);
        root.style.setProperty("--accent-secondary-glow", secGlow);
        root.style.setProperty("--accent-secondary-end", secGlow);
        root.style.setProperty("--accent-secondary-gradient", `linear-gradient(135deg, ${secStart} 0%, ${secGlow} 100%)`);

        // Sincronizar colores globales de categoría
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
        window.CATEGORY_COLORS = catColors;
        window.CATEGORY_GRADIENTS = catGradients;

        // Actualizar canvas y nodos de LiteGraph si están presentes
        if (window.canvas) {
            window.canvas.background_color = canvasBg;

            // Configurar colores y resplandor (glow) de cables en LiteGraph
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
                console.warn("Pyxis: Error al guardar tema en backend", e);
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
                console.warn("Pyxis: Error al borrar tema en backend", e);
            }
        }
        if (currentTheme === themeId) {
            applyTheme("teal");
        }
        saveConfig();
        return true;
    }

    // Modal de Edición de Temas Personalizados
    function openThemeEditorModal(themeIdToEdit) {
        const existing = document.getElementById("pyxis-theme-editor-modal");
        if (existing) existing.remove();

        const activeThemeBeforeEdit = currentTheme;
        const isEditingActiveTheme = Boolean(themeIdToEdit && themeIdToEdit === currentTheme);

        const baseTheme = THEMES[themeIdToEdit] || THEMES[currentTheme] || DEFAULT_THEMES.teal;
        let editingTheme = JSON.parse(JSON.stringify(baseTheme));
        if (editingTheme.isDefault) {
            editingTheme.id = "custom_" + Date.now();
            editingTheme.name = baseTheme.name + " (Copia)";
            editingTheme.desc = "Tema personalizado basado en " + baseTheme.name;
            editingTheme.isCustom = true;
            delete editingTheme.isDefault;
        }

        const modal = document.createElement("div");
        modal.id = "pyxis-theme-editor-modal";
        modal.className = "pyxis-modal-overlay";

        const categoryList = ["Loops", "System", "Variables", "String", "Text", "Math", "Functions", "Shape", "Time", "Tags", "Audio", "Particles", "Meta"];

        function createColorFieldHtml(fieldId, currentHex, dataCat = "", dataProp = "", title = "Color") {
            const hex = (currentHex || "#10B981").toUpperCase();
            const dataAttrs = dataCat ? `data-cat="${dataCat}" data-prop="${dataProp}"` : `data-field-id="${fieldId}"`;
            return `
                <div class="pyxis-color-field" title="${title}">
                    <div class="pyxis-color-chip" style="background-color: ${hex};" ${dataAttrs}>
                        <input type="color" class="pyxis-color-native-input" value="${hex}" ${dataAttrs}>
                    </div>
                    <input type="text" class="pyxis-color-hex-text" value="${hex}" maxlength="7" ${dataAttrs} spellcheck="false">
                    <button type="button" class="pyxis-color-pro-btn" title="Selector avanzado HSV/RGB" ${dataAttrs}>
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
                    <span class="theme-editor-cat-title">Acento Primario (Botones, Resplandores y Destacados)</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-pri" style="background: linear-gradient(135deg, ${priStartVal} 0%, ${priEndVal} 100%);">
                        <span class="cat-badge-dot" style="background:#ffffff;"></span>
                        <span>Botón / Acento</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Inicio:</span>
                        ${createColorFieldHtml("accentPrimary", priStartVal, "", "", "Acento Primario (Inicio)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-pri" title="Intercambiar inicio y fin">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Fin (Degradado):</span>
                        ${createColorFieldHtml("accentPrimaryEnd", priEndVal, "", "", "Acento Primario (Fin / Degradado)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-cat-card" style="grid-column: 1 / -1;">
                <div class="theme-editor-cat-header">
                    <span class="theme-editor-cat-title">Cables y Conexiones de Nodos</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-sec" style="background: ${secStartVal}; box-shadow: 0 0 10px ${secGlowVal};">
                        <span class="cat-badge-dot" style="background:#ffffff; box-shadow: 0 0 4px ${secGlowVal};"></span>
                        <span>Cables / Enlaces</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Color del Cable:</span>
                        ${createColorFieldHtml("accentSecondary", secStartVal, "", "", "Color del Cable (Línea Principal)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-sec" title="Intercambiar color del cable y resplandor">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Resplandor (Glow):</span>
                        ${createColorFieldHtml("accentSecondaryGlow", secGlowVal, "", "", "Color del Resplandor (Glow)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-cat-card" style="grid-column: 1 / -1;">
                <div class="theme-editor-cat-header">
                    <span class="theme-editor-cat-title">Fondo del Cuerpo de Tarjetas y Nodos</span>
                    <div class="theme-editor-cat-badge" id="ui-badge-nodebg" style="background: linear-gradient(180deg, ${nodeBgStartVal} 0%, ${nodeBgEndVal} 100%);">
                        <span class="cat-badge-dot" style="background:#ffffff;"></span>
                        <span>Cuerpo de Nodo</span>
                    </div>
                </div>
                <div class="theme-editor-cat-body">
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Inicio (Superior):</span>
                        ${createColorFieldHtml("nodeStart", nodeBgStartVal, "", "", "Fondo de Tarjeta (Inicio)")}
                    </div>
                    <button type="button" class="pyxis-cat-swap-btn" id="btn-swap-nodebg" title="Intercambiar inicio y fin">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                    </button>
                    <div class="theme-editor-cat-col">
                        <span class="theme-editor-col-lbl">Fin (Inferior):</span>
                        ${createColorFieldHtml("nodeEnd", nodeBgEndVal, "", "", "Fondo de Tarjeta (Fin)")}
                    </div>
                </div>
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Fondo del Canvas</span>
                    <span class="theme-editor-item-sub">Superficie de trabajo</span>
                </div>
                ${createColorFieldHtml("canvasBg", canvasBgVal, "", "", "Fondo del Canvas")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Fondo de Paneles</span>
                    <span class="theme-editor-item-sub">Barras laterales y modales</span>
                </div>
                ${createColorFieldHtml("panelBg", panelBgVal, "", "", "Fondo de Paneles")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Barra Superior</span>
                    <span class="theme-editor-item-sub">Top bar de herramientas</span>
                </div>
                ${createColorFieldHtml("topbarBg", topbarBgVal, "", "", "Fondo de Barra Superior")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Fondo de Entradas</span>
                    <span class="theme-editor-item-sub">Inputs y cajas de texto</span>
                </div>
                ${createColorFieldHtml("inputBg", inputBgVal, "", "", "Fondo de Entradas e Inputs")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Texto Principal</span>
                    <span class="theme-editor-item-sub">Títulos y valores</span>
                </div>
                ${createColorFieldHtml("textMain", textMainVal, "", "", "Texto Principal")}
            </div>

            <div class="theme-editor-item">
                <div class="theme-editor-item-info">
                    <span class="theme-editor-item-label">Texto Secundario</span>
                    <span class="theme-editor-item-sub">Etiquetas y notas</span>
                </div>
                ${createColorFieldHtml("textMuted", textMutedVal, "", "", "Texto Secundario")}
            </div>
        `;

        let categoryPickersHtml = `
            <div class="theme-editor-global-cat-banner">
                <div class="global-cat-info">
                    <span class="global-cat-title">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:15px;height:15px;color:var(--accent-primary);"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                        Homogeneizar Todos los Nodos
                    </span>
                    <span class="global-cat-desc">Asigna el mismo color o degradado a todos los 13 tipos de nodos con un solo clic.</span>
                </div>
                <div class="global-cat-controls">
                    <div class="pyxis-color-field" title="Color Inicio Global">
                        <div class="pyxis-color-chip" id="global-cat-chip-col" style="background-color: #8B5CF6;">
                            <input type="color" class="pyxis-color-native-input" id="global-cat-native-col" value="#8B5CF6">
                        </div>
                        <input type="text" class="pyxis-color-hex-text" id="global-cat-col-inp" value="#8B5CF6" maxlength="7" spellcheck="false">
                    </div>
                    <div class="pyxis-color-field" title="Color Fin / Degradado Global">
                        <div class="pyxis-color-chip" id="global-cat-chip-grad" style="background-color: #6366F1;">
                            <input type="color" class="pyxis-color-native-input" id="global-cat-native-grad" value="#6366F1">
                        </div>
                        <input type="text" class="pyxis-color-hex-text" id="global-cat-grad-inp" value="#6366F1" maxlength="7" spellcheck="false">
                    </div>
                    <button type="button" class="pyxis-btn pyxis-btn-primary" id="btn-apply-all-categories" title="Aplicar a todas las categorías">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:14px;height:14px;stroke-width:2.5;fill:none;"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Aplicar a Todos</span>
                    </button>
                </div>
            </div>
        `;

        categoryList.forEach(cat => {
            const catData = (editingTheme.categories && editingTheme.categories[cat]) || { color: "#3b82f6", gradientEnd: "#1d4ed8" };
            const col = (typeof catData === "object" ? catData.color : catData) || "#3b82f6";
            const grad = (typeof catData === "object" ? (catData.gradientEnd || col) : col) || "#1d4ed8";
            categoryPickersHtml += `
                <div class="theme-editor-cat-card" data-cat="${cat}">
                    <div class="theme-editor-cat-header">
                        <span class="theme-editor-cat-title">${cat}</span>
                        <div class="theme-editor-cat-badge" id="cat-badge-${cat}" style="background: linear-gradient(90deg, ${col} 0%, ${grad} 100%);">
                            <span class="cat-badge-dot"></span>
                            <span>${cat}</span>
                        </div>
                    </div>
                    <div class="theme-editor-cat-body">
                        <div class="theme-editor-cat-col">
                            <span class="theme-editor-col-lbl">Inicio:</span>
                            ${createColorFieldHtml(`cat_${cat}_col`, col, cat, "color", `Color inicial para ${cat}`)}
                        </div>
                        <button type="button" class="pyxis-cat-swap-btn" data-swap-cat="${cat}" title="Intercambiar colores">
                            <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                        </button>
                        <div class="theme-editor-cat-col">
                            <span class="theme-editor-col-lbl">Fin:</span>
                            ${createColorFieldHtml(`cat_${cat}_grad`, grad, cat, "gradientEnd", `Gradiente/Borde para ${cat}`)}
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
                        <span>Editor de Colores & Temas Personalizados</span>
                    </div>
                    <button class="pyxis-modal-close" id="btn-close-theme-editor">
                        <svg class="svg-icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>

                <!-- Nombre y Plantilla Base -->
                <div style="display: flex; gap: 12px; margin-bottom: 14px;">
                    <div style="flex: 1;">
                        <label style="font-size: 11.5px; font-weight: 500; color: var(--text-muted); display: block; margin-bottom: 4px;">Nombre del Tema:</label>
                        <input type="text" id="theme-edit-name" value="${editingTheme.name}" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 100%; box-sizing: border-box; outline: none;">
                    </div>
                    <div style="width: 210px;">
                        <label style="font-size: 11.5px; font-weight: 500; color: var(--text-muted); display: block; margin-bottom: 4px;">Cargar Plantilla Base:</label>
                        <select id="theme-edit-preset-select" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 100%; outline: none; cursor: pointer;">
                            <option value="">-- Seleccionar Base --</option>
                            ${Object.keys(DEFAULT_THEMES).map(k => `<option value="${k}">${DEFAULT_THEMES[k].name}</option>`).join('')}
                        </select>
                    </div>
                </div>

                <!-- Previsualización de Nodos & Canvas -->
                <div class="theme-editor-mock-container">
                    <div class="theme-editor-mock-title">
                        <svg class="svg-icon" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        <span>VISTA PREVIA</span>
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
                                    <span style="display: inline-flex; align-items: center; gap: 4px;"><span class="mock-slot-dot" style="background: ${priStartVal}; box-shadow: 0 0 8px ${priStartVal};"></span> Entrada ASS</span>
                                    <span style="display: inline-flex; align-items: center; gap: 4px;">Salida <span class="mock-slot-dot out" id="theme-mock-slot-out" style="background: ${secStartVal}; box-shadow: 0 0 8px ${secGlowVal};"></span></span>
                                </div>
                                <button type="button" class="mock-widget-btn" id="theme-mock-widget-btn" style="background: linear-gradient(135deg, ${priStartVal} 0%, ${priEndVal} 100%);">Ejecutar Acción</button>
                            </div>
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg viewBox="0 0 160 40" style="width: 160px; height: 40px; overflow: visible;">
                                    <path id="theme-mock-wire" d="M 0 20 C 70 20, 90 20, 160 20" fill="none" stroke="${secStartVal}" stroke-width="3.5" stroke-linecap="round" style="filter: drop-shadow(0 0 6px ${secGlowVal});"/>
                                </svg>
                            </div>
                            <span style="font-size: 11px; color: var(--text-muted);">Los cambios se reflejan en tiempo real tanto en esta tarjeta como en el canvas y los botones de Pyxis.</span>
                        </div>
                    </div>
                </div>

                <div class="pyxis-theme-tabs">
                    <button class="pyxis-theme-tab active" data-tab="tab-ui-colors">Colores de Interfaz & Canvas (UI)</button>
                    <button class="pyxis-theme-tab" data-tab="tab-cat-colors">Cabeceras y Categorías de Nodos</button>
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
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-export" title="Exportar archivo de tema a disco">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                            <span>Exportar Archivo</span>
                        </button>
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-import" title="Importar archivo de tema desde disco">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                            <span>Importar Archivo</span>
                        </button>
                        ${editingTheme.isCustom ? `
                            <button class="pyxis-btn pyxis-btn-danger" id="btn-theme-delete" title="Eliminar tema personalizado">
                                <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                <span>Eliminar</span>
                            </button>
                        ` : ''}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="pyxis-btn pyxis-btn-secondary" id="btn-theme-cancel">Cancelar</button>
                        <button class="pyxis-btn pyxis-btn-primary" id="btn-theme-save">
                            <svg class="svg-icon" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                            <span>Guardar Tema</span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        function updateLivePreview() {
            editingTheme.name = modal.querySelector("#theme-edit-name").value || "Tema Personalizado";
            
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

            // Actualizar vista previa interactiva interna
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

            // Aplicar tema en vivo en LiteGraph
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

        // Conectar inputs de color nativos y textos HEX
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

        // Auto-seleccionar texto al hacer clic o foco en cajas de texto y números
        modal.querySelectorAll("input[type='text'], input[type='number']").forEach(inp => {
            inp.addEventListener("focus", function() {
                this.select();
            });
            inp.addEventListener("click", function() {
                this.select();
            });
        });

        // Conectar botones Pro Color Picker
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

        // Conectar botones de intercambio de gradiente
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

        // Homogeneizar Categorías (Global Category Color Applicator)
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

        // Pestañas UI vs Categorías
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

        // Nombre del tema
        modal.querySelector("#theme-edit-name").addEventListener("input", updateLivePreview);

        // Cambiar plantilla base
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

        // Exportar Archivo
        modal.querySelector("#btn-theme-export").onclick = function() {
            updateLivePreview();
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.export_theme_dialog === "function") {
                window.pywebview.api.export_theme_dialog(editingTheme).then(res => {
                    if (res && res.success) {
                        if (window.showPyxisToast) window.showPyxisToast("toast.theme_exported", "success", 2600);
                    } else if (res && res.error) {
                        if (window.showPyxisToast) window.showPyxisToast(res.error, "error", 3000);
                    }
                }).catch(err => console.warn("Pyxis: Error al exportar tema", err));
            } else {
                const jsonStr = JSON.stringify(editingTheme, null, 2);
                navigator.clipboard.writeText(jsonStr).then(() => {
                    if (window.showPyxisToast) window.showPyxisToast("toast.theme_copied_clipboard", "success", 2400);
                }).catch(() => {
                    if (window.showPyxisToast) window.showPyxisToast("toast.clipboard_copy_error", "error", 2400);
                });
            }
        };

        // Importar Archivo
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
                }).catch(err => console.warn("Pyxis: Error al importar tema", err));
            } else {
                if (window.showPyxisToast) window.showPyxisToast("toast.import_requires_api", "warning", 3000);
            }
        };

        // Eliminar
        const delBtn = modal.querySelector("#btn-theme-delete");
        if (delBtn) {
            delBtn.onclick = function() {
                showPyxisConfirm({
                    title: "Eliminar Tema Personalizado",
                    message: `¿Estás seguro de que deseas eliminar permanentemente el tema <strong>"${editingTheme.name}"</strong>? Esta acción no se puede deshacer.`,
                    confirmText: "Eliminar Tema",
                    cancelText: "Cancelar",
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

        // Cancelar y Cerrar
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

        // Guardar
        modal.querySelector("#btn-theme-save").onclick = async function() {
            updateLivePreview();
            const shouldApply = isEditingActiveTheme;
            await saveCustomTheme(editingTheme, shouldApply);
            if (!shouldApply) {
                applyTheme(activeThemeBeforeEdit);
            }
            modal.remove();
            await openSettingsModal();
            if (window.showPyxisToast) {
                const toastKey = shouldApply ? "toast.theme_saved_applied" : "toast.theme_saved";
                const fallbackMsg = shouldApply
                    ? `Theme "${editingTheme.name}" saved and applied`
                    : `Theme "${editingTheme.name}" saved to list`;
                const toastMsg = window.t ? window.t(toastKey, { name: editingTheme.name }) : fallbackMsg;
                window.showPyxisToast(toastMsg, "success", 2600);
            }
        };

        // Inicializar vista previa inmediatamente
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

        // 1. Temas Guardados por ti (Personalizados)
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
                                    <span class="pyxis-theme-badge-custom">Personalizado</span>
                                </div>
                                <div class="pyxis-theme-row-desc">${t.desc || 'Tema personalizado guardado'}</div>
                            </div>
                        </div>
                        <div class="pyxis-theme-row-right">
                            <div class="pyxis-theme-swatches">
                                ${swatches.map(c => `<div class="pyxis-theme-swatch" style="background:${c}"></div>`).join('')}
                            </div>
                            <div class="pyxis-theme-row-actions">
                                <button type="button" class="pyxis-theme-action-btn btn-edit-theme" data-theme-id="${t.id}" title="Editar este tema">
                                    <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                                    <span>Editar</span>
                                </button>
                                <button type="button" class="pyxis-theme-action-btn delete btn-delete-theme" data-theme-id="${t.id}" title="Eliminar este tema">
                                    <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            customListHtml = `<div class="pyxis-theme-empty-state">No tienes temas personalizados guardados todavía. Pulsa "+ Crear Nuevo Tema" para diseñar el tuyo.</div>`;
        }

        // 2. Temas Predefinidos (Oficiales)
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
                            <div class="pyxis-theme-row-desc">${t.desc || 'Tema oficial de Pyxis'}</div>
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
        let bgPathDisplay = window.t ? window.t("settings.bg_none") : 'Ninguno seleccionado';
        if (hasBg) {
            if (bgSettings.mediaType === 'video' || bgSettings.videoUrl) {
                bgPathDisplay = window.t ? window.t("settings.bg_video") : 'Video en bucle activo (Acelerado por GPU)';
            } else if (bgSettings.isDefault) {
                bgPathDisplay = window.t ? window.t("settings.bg_default") : 'Fondo por defecto (default_back.webp)';
            } else {
                bgPathDisplay = window.t ? window.t("settings.bg_image") : 'Imagen cargada';
            }
        }

        modal.innerHTML = `
            <div class="pyxis-modal-dialog pyxis-settings-dialog">
                <div class="pyxis-modal-header" style="display: flex; align-items: center; justify-content: space-between;">
                    <div class="pyxis-modal-title">
                        <svg class="svg-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                        <span>${window.t ? window.t("settings.title") : "Ajustes & Temas Visuales"}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button type="button" class="pyxis-btn pyxis-btn-lang" id="btn-settings-lang-toggle" title="${window.t ? window.t('topbar.lang_tooltip') : 'Cambiar idioma (Español / English)'}" style="display: flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 6px; background: var(--bg-input, #1e293b); border: 1px solid var(--border-subtle, #334155); color: var(--text-main, #f8fafc); cursor: pointer; font-size: 11px; font-weight: 600;">
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
                    <div style="font-size: 13px; font-weight: 600; color: var(--text-main);">${window.t ? window.t("settings.themes_section") : "Temas Visuales de la Interfaz:"}</div>
                    <button class="pyxis-btn pyxis-btn-primary" id="btn-open-theme-editor" style="padding: 4px 10px; font-size: 12px; display: flex; align-items: center; gap: 5px;">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:13px; height:13px;"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        <span>${window.t ? window.t("settings.create_theme") : "Crear Nuevo Tema"}</span>
                    </button>
                </div>

                <div class="pyxis-theme-list-wrapper">
                    <!-- Guardados por ti -->
                    <div class="pyxis-theme-list-section">
                        <div class="pyxis-theme-list-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;stroke:var(--accent-primary);"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                            <span>${window.t ? window.t("settings.saved_by_you") : "Guardados por ti"}</span>
                        </div>
                        ${customListHtml}
                    </div>

                    <!-- Temas Predefinidos -->
                    <div class="pyxis-theme-list-section" style="margin-top: 6px;">
                        <div class="pyxis-theme-list-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:12px;height:12px;"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/></svg>
                            <span>${window.t ? window.t("settings.presets") : "Temas Predefinidos"}</span>
                        </div>
                        ${defaultListHtml}
                    </div>
                </div>

                <!-- Canvas Customization Section -->
                <div style="margin-top: 15px; border-top: 1px solid var(--border-subtle); padding-top: 15px;">
                    <div style="font-weight: 600; font-size: 14px; color: var(--text-main); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: var(--accent-primary); width:18px; height:18px;"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                        <span>${window.t ? window.t("settings.canvas_section") : "Personalización del Canvas & Medios de Fondo"}</span>
                    </div>

                    <!-- Persistencia en Segundo Plano (Daemon) -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;" title="${window.t ? window.t("settings.daemon_tooltip") : "Mantiene el servidor Python en segundo plano (~60MB RAM) para que Pyxis abra de forma instantánea (0ms) desde Aegisub."}">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: 13px; color: var(--text-main); font-weight: 500;">${window.t ? window.t("settings.daemon") : "Persistencia en Segundo Plano:"}</span>
                            <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.daemon_desc") : "Apertura instantánea (0ms) tras la primera vez"}</span>
                        </div>
                        <input type="checkbox" id="setting-daemon-mode" ${window.pyxisDaemonMode !== false ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--accent-primary);">
                    </div>

                    <!-- Estilo de Rejilla -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.grid_style") : "Estilo de Rejilla:"}</span>
                        <select id="setting-grid-mode" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 160px;">
                            <option value="0" ${window.gridMode === 0 ? 'selected' : ''}>${window.t ? window.t("settings.grid_lines") : "Líneas"}</option>
                            <option value="1" ${window.gridMode === 1 ? 'selected' : ''}>${window.t ? window.t("settings.grid_dots") : "Puntos (Defecto)"}</option>
                            <option value="2" ${window.gridMode === 2 ? 'selected' : ''}>${window.t ? window.t("settings.grid_disabled") : "Desactivado"}</option>
                        </select>
                    </div>

                    <!-- Pasos de Deshacer / Rehacer -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.undo_steps") : "Pasos de Deshacer / Rehacer (Undo/Redo):"}</span>
                        <input type="number" id="setting-undo-steps" min="5" max="100" value="${window.PyxisUndoManager ? window.PyxisUndoManager.getMaxSteps() : 30}" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 80px; text-align: center;">
                    </div>

                    <!-- Fondo Multimedia (Imágenes y Videos Cíclicos) -->
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <div style="display: flex; flex-direction: column;">
                                <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.canvas_bg") : "Fondo del Canvas (Imagen o Video Cíclico):"}</span>
                                <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.canvas_bg_formats") : "Soporta MP4, WebM, MOV, MKV, PNG, JPG, WebP"}</span>
                            </div>
                            <div style="display: flex; gap: 6px;">
                                <button class="pyxis-btn" id="btn-browse-bg" style="padding: 4px 10px; font-size: 12px; display: inline-flex; align-items: center;">${window.t ? window.t("settings.browse") : "Examinar..."}</button>
                                <button class="pyxis-btn pyxis-btn-danger" id="btn-clear-bg" style="padding: 4px 10px; font-size: 12px; display: ${hasBg ? 'inline-block' : 'none'};">${window.t ? window.t("settings.remove") : "Quitar"}</button>
                            </div>
                        </div>
                        <input type="text" id="setting-bg-path" readonly value="${bgPathDisplay}" style="background: var(--bg-input); color: var(--text-muted); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 6px 10px; font-size: 11px; width: 100%; box-sizing: border-box; font-family: var(--font-mono); outline: none;">
                    </div>

                    <!-- Casilla: Convertir / Optimizar Video con FFmpeg -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;" title="${window.t ? window.t("settings.optimize_video_tooltip") : "Optimiza el video a formato H.264/MP4 ligero sin audio para máxima fluidez y mínimo consumo de GPU/CPU."}">
                        <div style="display: flex; flex-direction: column;">
                            <span style="font-size: 13px; color: var(--text-main); font-weight: 500;">${window.t ? window.t("settings.optimize_video") : "Convertir / Optimizar Video con FFmpeg"}</span>
                            <span style="font-size: 11px; color: var(--text-muted);">${window.t ? window.t("settings.daemon_desc") : "Recomendado para fluidez óptima"}</span>
                        </div>
                        <input type="checkbox" id="setting-convert-video" ${window.convertVideoSetting !== false ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--accent-primary);">
                    </div>

                    <!-- Modo de Ajuste & Opacidad -->
                    <div id="bg-options-panel" style="display: ${hasBg ? 'block' : 'none'};">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.fit_mode") : "Modo de Ajuste:"}</span>
                            <select id="setting-bg-mode" style="background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: 6px; padding: 5px 10px; font-size: 13px; outline: none; width: 160px;">
                                <option value="cover" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'cover') ? 'selected' : ''}>${window.t ? window.t("settings.fit_cover") : "Rellenar"}</option>
                                <option value="contain" ${(window.backgroundImageSettings && (window.backgroundImageSettings.mode === 'contain' || !window.backgroundImageSettings.mode)) ? 'selected' : ''}>${window.t ? window.t("settings.fit_contain") : "Ajustar"}</option>
                                <option value="stretch" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'stretch') ? 'selected' : ''}>${window.t ? window.t("settings.fit_stretch") : "Estirar"}</option>
                                <option value="tile" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'tile') ? 'selected' : ''}>${window.t ? window.t("settings.fit_tile") : "Mosaico"}</option>
                                <option value="center" ${(window.backgroundImageSettings && window.backgroundImageSettings.mode === 'center') ? 'selected' : ''}>${window.t ? window.t("settings.fit_center") : "Centro"}</option>
                            </select>
                        </div>

                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 13px; color: var(--text-main)">${window.t ? window.t("settings.opacity") : "Opacidad del Fondo:"}</span>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <input type="range" id="setting-bg-opacity" min="0" max="100" value="${window.backgroundImageSettings ? Math.round(window.backgroundImageSettings.opacity * 100) : 85}" style="width: 110px; cursor: pointer; accent-color: var(--accent-primary);">
                                <span id="bg-opacity-label" style="font-size: 12px; color: var(--text-main); font-family: var(--font-mono); min-width: 32px; text-align: right;">${window.backgroundImageSettings ? Math.round(window.backgroundImageSettings.opacity * 100) : 85}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                    <button class="pyxis-btn pyxis-btn-secondary" id="btn-clean-temp-cache" style="font-size: 12px; padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px;" title="Elimina archivos temporales y fragmentos de caché con más de 72 horas sin afectar fondos ni configuraciones">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                        <span>${window.t ? window.t("settings.clean_temp") : "Limpiar Temporales (> 72h)"}</span>
                    </button>
                    <button class="pyxis-btn pyxis-btn-primary" id="btn-done-settings">${window.t ? window.t("common.confirm") : "Listo"}</button>
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
                const tName = customThemes[themeId] ? customThemes[themeId].name : "este tema";
                showPyxisConfirm({
                    title: "Eliminar Tema Personalizado",
                    message: `¿Estás seguro de que deseas eliminar permanentemente el tema <strong>"${tName}"</strong>? Esta acción no se puede deshacer.`,
                    confirmText: "Eliminar Tema",
                    cancelText: "Cancelar",
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
                openThemeEditorModal(currentTheme);
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

                // 1. Mostrar animación y estado de procesamiento en el modal de ajustes
                browseBtn.disabled = true;
                browseBtn.style.opacity = "0.75";
                browseBtn.innerHTML = `<svg class="svg-icon pyxis-spin" viewBox="0 0 24 24" style="width:13px;height:13px;margin-right:4px;"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Procesando...`;
                if (pathInput) pathInput.value = shouldConvert ? "Convirtiendo y optimizando video con FFmpeg..." : "Cargando medio de fondo...";

                // 2. Mostrar toast con animación de carga en el Canvas
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
                                ? "Video en bucle activo (Acelerado por GPU)" 
                                : "Imagen cargada";
                        }
                        const clearBtnEl = modal.querySelector("#btn-clear-bg");
                        if (clearBtnEl) clearBtnEl.style.display = "inline-block";
                        const optsPanel = modal.querySelector("#bg-options-panel");
                        if (optsPanel) optsPanel.style.display = "block";

                        if (window.updateBgMediaElement) window.updateBgMediaElement();
                        if (window.canvas) window.canvas.setDirty(true, true);
                        saveConfig();

                        // 3. Mostrar toast de confirmación al terminar
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
                modal.querySelector("#setting-bg-path").value = window.t ? window.t("settings.bg_none") : "Ninguno seleccionado";
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
                    console.error("Error al limpiar temporales:", e);
                } finally {
                    cleanTempBtn.disabled = false;
                    cleanTempBtn.style.opacity = "1";
                }
            };
        }

        // Auto-seleccionar texto al hacer clic o foco en cajas de texto y números
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
