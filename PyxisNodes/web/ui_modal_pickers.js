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
 * For any question you can visit: https://discord.gg/fsxRESeQZN
 */

/**
 * @file ui_modal_pickers.js
 * @description Interactive visual pickers and modal dialogues for Pyxis Effector.
 * Provides modal selectors for ASS colour palettes (HSV/RGB/ASS HEX), vector shape libraries,
 * ASS subtitle override tags, system context variables, and multi-line script editors.
 * @module PyxisModalPickers
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        function showMultilineEditor(node, propertyName, titleName) {
            const overlay = document.createElement("div");
            overlay.className = "pyxis-modal-overlay";
            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };

            const container = document.createElement("div");
            container.className = "pyxis-modal-dialog";
            container.style.width = "560px";

            const header = document.createElement("div");
            header.className = "pyxis-modal-header";
            header.innerHTML = `
                <div class="pyxis-modal-title">
                    <svg class="svg-icon" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    <span>${window.PyxisI18n && window.PyxisI18n.currentLang === "es" ? "Editor Multilínea: " + (titleName || "Propiedad") : "Multiline Editor: " + (titleName || "Property")}</span>
                </div>
            `;

            const textarea = document.createElement("textarea");
            textarea.id = "pyxis-multiline-editor-textarea";
            textarea.name = "pyxis-multiline-editor-textarea";
            textarea.style.width = "100%";
            textarea.style.height = "240px";
            textarea.style.backgroundColor = "var(--bg-input)";
            textarea.style.color = "var(--text-main)";
            textarea.style.border = "1px solid var(--border-subtle)";
            textarea.style.borderRadius = "8px";
            textarea.style.padding = "12px";
            textarea.style.fontFamily = "var(--font-mono)";
            textarea.style.fontSize = "13px";
            textarea.style.lineHeight = "1.5";
            textarea.style.resize = "vertical";
            textarea.value = node.properties[propertyName] || "";

            const btnRow = document.createElement("div");
            btnRow.style.display = "flex";
            btnRow.style.justifyContent = "flex-end";
            btnRow.style.gap = "10px";

            const btnCancel = document.createElement("button");
            btnCancel.className = "pyxis-btn";
            btnCancel.innerText = window.PyxisI18n ? PyxisI18n.t("ui.buttons.cancel") : "Cancel";
            btnCancel.onclick = () => overlay.remove();

            const btnSave = document.createElement("button");
            btnSave.className = "pyxis-btn pyxis-btn-primary";
            btnSave.style.minWidth = "110px";
            btnSave.innerText = window.PyxisI18n ? PyxisI18n.t("ui.buttons.save") : "Save";
            btnSave.onclick = () => {
                node.properties[propertyName] = textarea.value;
                if (typeof node.updateMultilineSize === "function") {
                    node.updateMultilineSize();
                }
                node.setDirtyCanvas(true, true);
                if (window.PyxisUndoManager) {
                    window.PyxisUndoManager.recordState("multiline-editor");
                }
                overlay.remove();
            };

            textarea.addEventListener("keydown", (e) => {
                if (e.key === "Escape") {
                    overlay.remove();
                } else if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    btnSave.click();
                }
            });

            btnRow.appendChild(btnCancel);
            btnRow.appendChild(btnSave);
            container.appendChild(header);
            container.appendChild(textarea);
            container.appendChild(btnRow);
            overlay.appendChild(container);
            document.body.appendChild(overlay);
            textarea.focus();
        }

        function openInlineMultilineEditor(node, propertyName, titleName) {
            const canvasEl = LGraphCanvas.active_canvas ? LGraphCanvas.active_canvas.canvas : null;
            if (!canvasEl) { showMultilineEditor(node, propertyName, titleName); return; }
            
            const canvasObj = LGraphCanvas.active_canvas;
            const rect = canvasEl.getBoundingClientRect();
            const scale = canvasObj.ds.scale || 1.0;
            const offset = canvasObj.ds.offset || [0, 0];

            const curVal = String(node.properties[propertyName] || "");
            const lines = curVal.split('\n');
            const lineCount = Math.max(1, lines.length);

            const nodeScreenX = rect.left + (node.pos[0] + offset[0]) * scale;
            const nodeScreenY = rect.top + (node.pos[1] + offset[1]) * scale;

            const wX = 10 * scale;
            const wY = 62 * scale;
            const wW = Math.max(200 * scale, (node.size[0] - 20) * scale);
            const initialH = Math.max(26 * scale, (lineCount * 18 + 12) * scale);

            let overlay = document.getElementById("pyxis-inline-textarea-overlay");
            if (!overlay) {
                overlay = document.createElement("textarea");
                overlay.id = "pyxis-inline-textarea-overlay";
                overlay.name = "pyxis-inline-textarea-overlay";
                document.body.appendChild(overlay);
            }

            overlay.style.boxSizing = "border-box";
            overlay.style.margin = "0";
            overlay.style.position = "fixed";
            overlay.style.left = Math.max(0, nodeScreenX + wX) + "px";
            overlay.style.top = Math.max(0, nodeScreenY + wY) + "px";
            overlay.style.width = wW + "px";
            overlay.style.height = initialH + "px";
            overlay.style.zIndex = "2000100";
            overlay.style.background = "#12161f";
            overlay.style.color = "#a7f3d0";
            overlay.style.border = "1.5px solid #8b5cf6";
            overlay.style.borderRadius = "8px";
            overlay.style.padding = "4px 8px";
            overlay.style.fontFamily = "monospace";
            overlay.style.fontSize = Math.max(11, Math.min(15, 12 * scale)) + "px";
            overlay.style.fontWeight = "bold";
            overlay.style.boxShadow = "0 0 16px rgba(139, 92, 246, 0.8)";
            overlay.style.outline = "none";
            overlay.style.resize = "none";
            overlay.style.display = "block";

            overlay.value = curVal;

            const syncOverlayHeight = () => {
                const lCount = Math.max(1, overlay.value.split('\n').length);
                const newH = (lCount * 18 + 12) * scale;
                overlay.style.height = Math.max(26 * scale, newH) + "px";
                node.properties[propertyName] = overlay.value;
                if (node.computeSize) node.size = node.computeSize();
                if (canvasObj.setDirtyCanvas) canvasObj.setDirtyCanvas(true, true);
            };

            overlay.oninput = syncOverlayHeight;

            let isMounting = true;
            setTimeout(() => {
                isMounting = false;
                overlay.focus();
                const len = overlay.value ? overlay.value.length : 0;
                if (typeof overlay.setSelectionRange === "function") {
                    overlay.setSelectionRange(len, len);
                }
            }, 30);

            let submitted = false;
            const finish = (save) => {
                if (submitted) return;
                submitted = true;
                overlay.style.display = "none";
                overlay.onkeydown = null;
                overlay.onblur = null;
                overlay.oninput = null;
                overlay._finish = null;

                if (save) {
                    node.properties[propertyName] = overlay.value;
                    if (node.computeSize) node.size = node.computeSize();
                    if (canvasObj.setDirtyCanvas) canvasObj.setDirtyCanvas(true, true);
                }
            };
            overlay._finish = finish;

            overlay.onkeydown = function(e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    finish(true);
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    finish(false);
                }
            };

            overlay.onblur = function() {
                if (isMounting) {
                    overlay.focus();
                    return;
                }
                finish(true);
            };
        }

        function cpHsvToRgb(h, s, v) {
            let r, g, b;
            let i = Math.floor(h * 6);
            let f = h * 6 - i;
            let p = v * (1 - s);
            let q = v * (1 - f * s);
            let t = v * (1 - (1 - f) * s);
            switch (i % 6) {
                case 0: r = v; g = t; b = p; break;
                case 1: r = q; g = v; b = p; break;
                case 2: r = p; g = v; b = t; break;
                case 3: r = p; g = q; b = v; break;
                case 4: r = t; g = p; b = v; break;
                case 5: r = v; g = p; b = q; break;
            }
            return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
        }

        function cpRgbToHsv(r, g, b) {
            r /= 255; g /= 255; b /= 255;
            let max = Math.max(r, g, b), min = Math.min(r, g, b);
            let h, s, v = max;
            let d = max - min;
            s = max === 0 ? 0 : d / max;
            if (max === min) {
                h = 0;
            } else {
                switch (max) {
                    case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                    case g: h = (b - r) / d + 2; break;
                    case b: h = (r - g) / d + 4; break;
                }
                h /= 6;
            }
            return [Math.round(h * 360), Math.round(s * 100), Math.round(v * 100)];
        }

        // Memoria de colores recientes para la sesión activa de Aegisub (12 muestras en gris neutro)
        if (!window.__pyxis_color_history || !Array.isArray(window.__pyxis_color_history) || window.__pyxis_color_history.length !== 12) {
            window.__pyxis_color_history = [
                "#808080", "#808080", "#808080", "#808080", "#808080", "#808080",
                "#808080", "#808080", "#808080", "#808080", "#808080", "#808080"
            ];
        }

        function intVal(str, s, e) {
            return parseInt(str.substring(s, e), 16) || 0;
        }

        function cpAssToRgb(assStr) {
            let clean = String(assStr).replace(/&[hH]?/g, "").replace(/&/g, "").trim();
            if (!clean) return [255, 255, 255];
            if (clean.length === 3) {
                const b = parseInt(clean[0] + clean[0], 16) || 0;
                const g = parseInt(clean[1] + clean[1], 16) || 0;
                const r = parseInt(clean[2] + clean[2], 16) || 0;
                return [r, g, b];
            }
            if (clean.length === 8) {
                const b = intVal(clean, 2, 4);
                const g = intVal(clean, 4, 6);
                const r = intVal(clean, 6, 8);
                return [r, g, b];
            }
            const padded = clean.padStart(6, "0");
            const b = intVal(padded, 0, 2);
            const g = intVal(padded, 2, 4);
            const r = intVal(padded, 4, 6);
            return [r, g, b];
        }

        function cpHexToRgb(hexStr) {
            let clean = String(hexStr).replace("#", "").trim();
            if (clean.startsWith("&H") || clean.startsWith("&h") || clean.endsWith("&")) {
                return cpAssToRgb(clean);
            }
            if (!clean) return [255, 255, 255];
            if (clean.length === 3) {
                const r = parseInt(clean[0] + clean[0], 16) || 0;
                const g = parseInt(clean[1] + clean[1], 16) || 0;
                const b = parseInt(clean[2] + clean[2], 16) || 0;
                return [r, g, b];
            }
            if (clean.length === 8) {
                return [intVal(clean, 2, 4), intVal(clean, 4, 6), intVal(clean, 6, 8)];
            }
            const padded = clean.padStart(6, "0");
            return [intVal(padded, 0, 2), intVal(padded, 2, 4), intVal(padded, 4, 6)];
        }

        function cpRgbToHex(r, g, b) {
            const hex = (v) => ("0" + Math.max(0, Math.min(255, Math.round(v))).toString(16)).slice(-2).toUpperCase();
            return `#${hex(r)}${hex(g)}${hex(b)}`;
        }

        function cpRgbToAss(r, g, b) {
            const hex = (v) => ("0" + Math.max(0, Math.min(255, Math.round(v))).toString(16)).slice(-2).toUpperCase();
            return `&H${hex(b)}${hex(g)}${hex(r)}&`;
        }

        function showProColorPickerModal(node, propertyName, titleName, onSaveCallback, clickEvent, onLiveCallback) {
            let initialColorHex = "#FFFFFF";
            if (typeof node === "string") {
                initialColorHex = node;
            } else if (node && typeof propertyName === "number" && node.properties && Array.isArray(node.properties.colors)) {
                initialColorHex = node.properties.colors[propertyName] || "#FFFFFF";
            } else if (node && node.properties && node.properties[propertyName]) {
                initialColorHex = node.properties[propertyName];
            } else if (typeof propertyName === "string" && (propertyName.startsWith("#") || propertyName.startsWith("&H") || propertyName.startsWith("&h"))) {
                initialColorHex = propertyName;
            }

            const initTrim = String(initialColorHex).trim();
            const [initR, initG, initB] = (initTrim.startsWith("&H") || initTrim.startsWith("&h") || initTrim.endsWith("&")) 
                ? cpAssToRgb(initTrim) 
                : cpHexToRgb(initTrim);
            const [initH, initS, initV] = cpRgbToHsv(initR, initG, initB);
            const initCleanHex = cpRgbToHex(initR, initG, initB);
            const initCleanAss = cpRgbToAss(initR, initG, initB);
            
            let curH = initH, curS = initS / 100, curV = initV / 100;

            const overlay = document.createElement("div");
            overlay.className = "pyxis-modal-overlay pyxis-color-picker-overlay";
            overlay.onclick = (ev) => {
                if (ev.target === overlay) cleanupModal(true);
            };

            const container = document.createElement("div");
            container.className = "pyxis-color-picker-dialog pyxis-color-picker-floating";

            let clientX = null;
            let clientY = null;
            if (clickEvent) {
                if (typeof clickEvent.clientX === "number" && clickEvent.clientX > 0) {
                    clientX = clickEvent.clientX;
                    clientY = clickEvent.clientY;
                } else if (clickEvent.evt && typeof clickEvent.evt.clientX === "number" && clickEvent.evt.clientX > 0) {
                    clientX = clickEvent.evt.clientX;
                    clientY = clickEvent.evt.clientY;
                } else if (typeof clickEvent.pageX === "number" && clickEvent.pageX > 0) {
                    clientX = clickEvent.pageX - window.scrollX;
                    clientY = clickEvent.pageY - window.scrollY;
                }
            }

            const pickerW = 490;
            const pickerH = 430;
            let left, top;

            if (clientX !== null && clientY !== null) {
                left = clientX + 8;
                top = clientY + 8;
                if (left + pickerW > window.innerWidth - 16) {
                    left = Math.max(16, clientX - pickerW - 8);
                }
                if (top + pickerH > window.innerHeight - 16) {
                    top = Math.max(16, window.innerHeight - pickerH - 16);
                }
            } else {
                left = Math.max(16, Math.floor((window.innerWidth - pickerW) / 2));
                top = Math.max(16, Math.floor((window.innerHeight - pickerH) / 2));
            }

            container.style.position = "fixed";
            container.style.left = `${left}px`;
            container.style.top = `${top}px`;
            container.style.zIndex = "2000500";

            const header = document.createElement("div");
            header.className = "pyxis-modal-header";
            header.innerHTML = `
                <div class="pyxis-modal-title">
                    <svg class="svg-icon" viewBox="0 0 24 24"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                    <span>${titleName || "Pyxis Color Picker"}</span>
                </div>
            `;
            const closeBtn = document.createElement("button");
            closeBtn.className = "pyxis-modal-close";
            closeBtn.innerHTML = `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px;height:14px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
            closeBtn.onclick = () => cleanupModal(true);
            header.appendChild(closeBtn);

            const mainLayout = document.createElement("div");
            mainLayout.className = "cp-main-layout";

            const leftCol = document.createElement("div");
            leftCol.className = "cp-left-column";

            const visualRow = document.createElement("div");
            visualRow.className = "cp-visual-column";

            const satValBox = document.createElement("div");
            satValBox.className = "cp-satval-box";
            satValBox.innerHTML = `
                <div class="cp-satval-white"></div>
                <div class="cp-satval-black"></div>
                <div class="cp-satval-cursor" id="cp_cursor"></div>
            `;

            const hueBar = document.createElement("div");
            hueBar.className = "cp-slider-bar cp-hue-bar";
            hueBar.innerHTML = `<div class="cp-slider-handle" id="cp_hue_handle"></div>`;

            visualRow.appendChild(satValBox);
            visualRow.appendChild(hueBar);
            leftCol.appendChild(visualRow);

            const presetsGrid = document.createElement("div");
            presetsGrid.className = "cp-presets-grid";
            const currentSwatches = (window.__pyxis_color_history && Array.isArray(window.__pyxis_color_history) && window.__pyxis_color_history.length === 12)
                ? window.__pyxis_color_history
                : ["#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080", "#808080"];
            currentSwatches.forEach((hex, idx) => {
                const chip = document.createElement("div");
                chip.className = "cp-preset-chip";
                chip.style.backgroundColor = hex;
                chip.title = hex;
                chip.onclick = () => {
                    const [r, g, b] = cpHexToRgb(hex);
                    const [h, s, v] = cpRgbToHsv(r, g, b);
                    curH = h; curS = s / 100; curV = v / 100;
                    updateUI();
                };
                presetsGrid.appendChild(chip);
            });
            leftCol.appendChild(presetsGrid);

            const controlsCol = document.createElement("div");
            controlsCol.className = "cp-controls-column";

            const compareBox = document.createElement("div");
            compareBox.className = "cp-preview-compare";
            compareBox.innerHTML = `
                <div class="cp-preview-half" id="cp_prev_new" style="background:${initCleanHex}">Nuevo</div>
                <div class="cp-preview-half" id="cp_prev_old" style="background:${initCleanHex}; cursor:pointer;" title="${window.PyxisI18n ? PyxisI18n.t("ui.color_picker.restore_prev") : "Click to restore previous color"}">Anterior</div>
            `;
            compareBox.querySelector("#cp_prev_old").onclick = () => {
                curH = initH; curS = initS / 100; curV = initV / 100;
                updateUI();
            };

            const fieldGroup = document.createElement("div");
            fieldGroup.className = "cp-field-group";
            fieldGroup.innerHTML = `
                <div class="cp-field-row"><span class="cp-field-label">HEX:</span><input type="text" class="cp-field-input" id="cp_inp_hex" name="cp_inp_hex" value="${initCleanHex}"></div>
                <div class="cp-field-row"><span class="cp-field-label">ASS:</span><input type="text" class="cp-field-input" id="cp_inp_ass" name="cp_inp_ass" value="${initCleanAss}"></div>
                <div class="cp-field-row"><span class="cp-field-label">R:</span><input type="number" min="0" max="255" class="cp-field-input" id="cp_inp_r" name="cp_inp_r"></div>
                <div class="cp-field-row"><span class="cp-field-label">G:</span><input type="number" min="0" max="255" class="cp-field-input" id="cp_inp_g" name="cp_inp_g"></div>
                <div class="cp-field-row"><span class="cp-field-label">B:</span><input type="number" min="0" max="255" class="cp-field-input" id="cp_inp_b" name="cp_inp_b"></div>
                <div class="cp-field-row"><span class="cp-field-label">H:</span><input type="number" min="0" max="360" class="cp-field-input" id="cp_inp_h" name="cp_inp_h"></div>
                <div class="cp-field-row"><span class="cp-field-label">S:</span><input type="number" min="0" max="100" class="cp-field-input" id="cp_inp_s" name="cp_inp_s"></div>
                <div class="cp-field-row"><span class="cp-field-label">V:</span><input type="number" min="0" max="100" class="cp-field-input" id="cp_inp_v" name="cp_inp_v"></div>
            `;

            const btnRow = document.createElement("div");
            btnRow.className = "cp-btn-row";

            const btnCancel = document.createElement("button");
            btnCancel.className = "pyxis-btn cp-btn";
            btnCancel.innerText = window.PyxisI18n ? PyxisI18n.t("ui.buttons.cancel") : "Cancel";
            btnCancel.onclick = () => cleanupModal(true);

            const btnSave = document.createElement("button");
            btnSave.className = "pyxis-btn pyxis-btn-primary cp-btn";
            btnSave.innerText = window.PyxisI18n ? PyxisI18n.t("ui.buttons.accept") : "Accept";
            btnSave.onclick = () => {
                const [r, g, b] = cpHsvToRgb(curH / 360, curS, curV);
                const finalHex = cpRgbToHex(r, g, b);

                // Guardar en la memoria de colores de la sesión:
                // Si el color ya existía en las muestras, reorganizar trayéndolo al primer lugar (arriba a la izquierda)
                // Si es un color nuevo, insertarlo al inicio y descartar el último.
                if (!window.__pyxis_color_history || !Array.isArray(window.__pyxis_color_history)) {
                    window.__pyxis_color_history = [
                        "#808080", "#808080", "#808080", "#808080", "#808080", "#808080",
                        "#808080", "#808080", "#808080", "#808080", "#808080", "#808080"
                    ];
                }
                const targetHexUpper = String(finalHex).trim().toUpperCase();
                const existingIndex = window.__pyxis_color_history.findIndex(
                    c => String(c).trim().toUpperCase() === targetHexUpper
                );

                if (existingIndex >= 0) {
                    window.__pyxis_color_history.splice(existingIndex, 1);
                }
                window.__pyxis_color_history.unshift(finalHex);
                if (window.__pyxis_color_history.length > 12) {
                    window.__pyxis_color_history.length = 12;
                }

                if (node && typeof propertyName === "number" && node.properties && Array.isArray(node.properties.colors)) {
                    node.properties.colors[propertyName] = finalHex;
                } else if (node && node.properties && typeof propertyName === "string") {
                    node.properties[propertyName] = finalHex;
                }
                if (onSaveCallback) onSaveCallback(finalHex);
                if (node && typeof node.setDirtyCanvas === "function") node.setDirtyCanvas(true, true);
                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                cleanupModal(false);
            };

            btnRow.appendChild(btnCancel);
            btnRow.appendChild(btnSave);

            controlsCol.appendChild(compareBox);
            controlsCol.appendChild(fieldGroup);
            controlsCol.appendChild(btnRow);

            mainLayout.appendChild(leftCol);
            mainLayout.appendChild(controlsCol);

            container.appendChild(header);
            container.appendChild(mainLayout);
            overlay.appendChild(container);
            document.body.appendChild(overlay);

            function cleanupModal(revert) {
                window.removeEventListener("mousemove", onMouseMove);
                window.removeEventListener("mouseup", onMouseUp);
                if (revert && typeof onLiveCallback === "function") {
                    onLiveCallback(initCleanHex);
                }
                overlay.remove();
            }

            function updateUI(skipInputId) {
                const [r, g, b] = cpHsvToRgb(curH / 360, curS, curV);
                const hex = cpRgbToHex(r, g, b);
                const ass = cpRgbToAss(r, g, b);

                container.querySelector("#cp_prev_new").style.backgroundColor = hex;
                container.querySelector("#cp_cursor").style.left = `${curS * 100}%`;
                container.querySelector("#cp_cursor").style.top = `${(1 - curV) * 100}%`;

                satValBox.style.backgroundColor = `hsl(${curH}, 100%, 50%)`;
                container.querySelector("#cp_hue_handle").style.top = `${(curH / 360) * 100}%`;

                if (skipInputId !== "cp_inp_hex") container.querySelector("#cp_inp_hex").value = hex;
                if (skipInputId !== "cp_inp_ass") container.querySelector("#cp_inp_ass").value = ass;
                if (skipInputId !== "cp_inp_r") container.querySelector("#cp_inp_r").value = r;
                if (skipInputId !== "cp_inp_g") container.querySelector("#cp_inp_g").value = g;
                if (skipInputId !== "cp_inp_b") container.querySelector("#cp_inp_b").value = b;
                if (skipInputId !== "cp_inp_h") container.querySelector("#cp_inp_h").value = Math.round(curH);
                if (skipInputId !== "cp_inp_s") container.querySelector("#cp_inp_s").value = Math.round(curS * 100);
                if (skipInputId !== "cp_inp_v") container.querySelector("#cp_inp_v").value = Math.round(curV * 100);

                if (typeof onLiveCallback === "function") {
                    onLiveCallback(hex);
                }
            }

            let isDraggingBox = false, isDraggingHue = false;

            const handleBoxDrag = (e) => {
                const rect = satValBox.getBoundingClientRect();
                let x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
                let y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));
                curS = x / rect.width;
                curV = 1 - (y / rect.height);
                updateUI();
            };

            const handleHueDrag = (e) => {
                const rect = hueBar.getBoundingClientRect();
                let y = Math.max(0, Math.min(rect.height, e.clientY - rect.top));
                curH = (y / rect.height) * 360;
                updateUI();
            };

            satValBox.onmousedown = (e) => { isDraggingBox = true; handleBoxDrag(e); };
            hueBar.onmousedown = (e) => { isDraggingHue = true; handleHueDrag(e); };

            const onMouseMove = (e) => {
                if (isDraggingBox) handleBoxDrag(e);
                else if (isDraggingHue) handleHueDrag(e);
            };

            const onMouseUp = () => {
                isDraggingBox = false; isDraggingHue = false;
            };

            window.addEventListener("mousemove", onMouseMove);
            window.addEventListener("mouseup", onMouseUp);

            container.querySelector("#cp_inp_hex").oninput = (e) => {
                let val = e.target.value.trim();
                let clean = val.replace("#", "").trim();
                if (clean.length === 6 || clean.length === 8 || clean.length === 3) {
                    const [r, g, b] = cpHexToRgb(val);
                    const [h, s, v] = cpRgbToHsv(r, g, b);
                    curH = h; curS = s / 100; curV = v / 100;
                    updateUI("cp_inp_hex");
                }
            };
            container.querySelector("#cp_inp_hex").onblur = () => {
                const [r, g, b] = cpHsvToRgb(curH / 360, curS, curV);
                container.querySelector("#cp_inp_hex").value = cpRgbToHex(r, g, b);
            };

            container.querySelector("#cp_inp_ass").oninput = (e) => {
                const val = e.target.value.trim();
                let clean = val.replace(/&[hH]?/g, "").replace(/&/g, "").trim();
                if (clean.length === 6 || clean.length === 8 || clean.length === 3) {
                    const [r, g, b] = cpAssToRgb(val);
                    const [h, s, v] = cpRgbToHsv(r, g, b);
                    curH = h; curS = s / 100; curV = v / 100;
                    updateUI("cp_inp_ass");
                }
            };
            container.querySelector("#cp_inp_ass").onblur = () => {
                const [r, g, b] = cpHsvToRgb(curH / 360, curS, curV);
                container.querySelector("#cp_inp_ass").value = cpRgbToAss(r, g, b);
            };

            const handleRgbInp = () => {
                let r = Math.max(0, Math.min(255, parseInt(container.querySelector("#cp_inp_r").value) || 0));
                let g = Math.max(0, Math.min(255, parseInt(container.querySelector("#cp_inp_g").value) || 0));
                let b = Math.max(0, Math.min(255, parseInt(container.querySelector("#cp_inp_b").value) || 0));
                const [h, s, v] = cpRgbToHsv(r, g, b);
                curH = h; curS = s / 100; curV = v / 100;
                updateUI();
            };
            container.querySelector("#cp_inp_r").oninput = handleRgbInp;
            container.querySelector("#cp_inp_g").oninput = handleRgbInp;
            container.querySelector("#cp_inp_b").oninput = handleRgbInp;

            const handleHsvInp = () => {
                curH = Math.max(0, Math.min(360, parseFloat(container.querySelector("#cp_inp_h").value) || 0));
                curS = Math.max(0, Math.min(100, parseFloat(container.querySelector("#cp_inp_s").value) || 0)) / 100;
                curV = Math.max(0, Math.min(100, parseFloat(container.querySelector("#cp_inp_v").value) || 0)) / 100;
                updateUI();
            };
            container.querySelector("#cp_inp_h").oninput = handleHsvInp;
            container.querySelector("#cp_inp_s").oninput = handleHsvInp;
            container.querySelector("#cp_inp_v").oninput = handleHsvInp;

            container.querySelectorAll("input").forEach(inp => {
                inp.addEventListener("focus", function() {
                    this.select();
                });
                inp.addEventListener("click", function() {
                    this.select();
                });
            });

            updateUI();
        }
        window.showProColorPickerModal = showProColorPickerModal;

        function setupColorPickerNode(node) {
            if (!node) return;
            node.resizable = false;
            if (!node.properties) node.properties = {};
            if (Array.isArray(node.properties.colors)) {
                node.properties.colors = [...node.properties.colors];
            } else {
                node.properties.colors = [node.properties.color || "#FFFFFF"];
            }
            if (Array.isArray(node.properties.formats)) {
                node.properties.formats = [...node.properties.formats];
            } else {
                node.properties.formats = ["ASS"];
            }
            
            node.widgets_up = false;

            node.updateColorPickerUI = function() {
                if (!this.properties.colors || !Array.isArray(this.properties.colors) || this.properties.colors.length === 0) {
                    this.properties.colors = ["#FFFFFF"];
                }
                if (!this.properties.formats || !Array.isArray(this.properties.formats)) {
                    this.properties.formats = ["ASS"];
                }
                while (this.properties.formats.length < this.properties.colors.length) {
                    this.properties.formats.push("ASS");
                }

                const count = this.properties.colors.length;
                const totalOutputs = count + 1;

                if (!this.outputs) this.outputs = [];
                while (this.outputs.length < totalOutputs) {
                    this.addOutput("", "data");
                }
                while (this.outputs.length > totalOutputs) {
                    this.removeOutput(this.outputs.length - 1);
                }

                this.outputs[0].name = "Color List";
                this.outputs[0].label = " ";
                this.outputs[0].type = "data";

                for (let i = 0; i < count; i++) {
                    this.outputs[i + 1].name = `Color ${i + 1}`;
                    this.outputs[i + 1].label = " ";
                    this.outputs[i + 1].type = "data";
                }

                this.widgets = [];

                if (this.computeSize) {
                    const sz = this.computeSize();
                    if (!this.flags || !this.flags.collapsed) {
                        this.size = [210, sz[1]];
                    }
                }
            };

            node.computeSize = function(out) {
                out = out || new Float32Array([0, 0]);
                const count = (this.properties && this.properties.colors && this.properties.colors.length) || 1;
                out[0] = 210;
                out[1] = 30 + count * 22 + 28;
                return out;
            };

            node.getConnectionPos = function(is_input, slot_number, out) {
                out = out || new Float32Array(2);
                if (this.flags && this.flags.collapsed) {
                    var w = this._collapsed_width || LiteGraph.NODE_COLLAPSED_WIDTH;
                    if (is_input) {
                        out[0] = this.pos[0] + 10;
                    } else {
                        out[0] = this.pos[0] + w - 10;
                    }
                    out[1] = this.pos[1] - LiteGraph.NODE_TITLE_HEIGHT * 0.5;
                    return out;
                }
                if (!is_input && this.outputs && slot_number < this.outputs.length) {
                    out[0] = this.pos[0] + this.size[0] - 10;
                    if (slot_number === 0) {
                        out[1] = this.pos[1] + 16;
                    } else {
                        const swatchIdx = slot_number - 1;
                        out[1] = this.pos[1] + 30 + swatchIdx * 22 + 11;
                    }
                } else {
                    out[0] = this.pos[0] + 10;
                    out[1] = this.pos[1] + 26;
                }
                return out;
            };

            node.onDrawForeground = function(ctx) {
                if (this.flags && this.flags.collapsed) return;
                
                const count = this.properties.colors ? this.properties.colors.length : 0;
                const nodeW = this.size[0];

                const btnY = 6;
                const btnW = 30;
                const btnH = 20;
                const centerX = nodeW / 2;
                const btnPlusX = centerX - btnW - 4;
                const btnMinusX = centerX + 4;
                const canMinus = count > 1;

                ctx.fillStyle = "#1e293b";
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnPlusX, btnY, btnW, btnH, 4);
                else ctx.rect(btnPlusX, btnY, btnW, btnH);
                ctx.fill();
                ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.fillStyle = "#38bdf8";
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("+", btnPlusX + btnW / 2, btnY + btnH / 2 + 4);

                ctx.fillStyle = canMinus ? "#1e293b" : "#0f172a";
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(btnMinusX, btnY, btnW, btnH, 4);
                else ctx.rect(btnMinusX, btnY, btnW, btnH);
                ctx.fill();
                ctx.strokeStyle = canMinus ? "rgba(255, 255, 255, 0.25)" : "rgba(255, 255, 255, 0.1)";
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.fillStyle = canMinus ? "#f43f5e" : "#475569";
                ctx.font = "bold 14px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText("-", btnMinusX + btnW / 2, btnY + btnH / 2 + 4);

                const isEs = (window.i18n && window.i18n.currentLang === "es");
                const listLabel = isEs ? "Lista" : "List";
                ctx.fillStyle = "#94a3b8";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "right";
                ctx.fillText(listLabel, nodeW - 18, btnY + btnH / 2 + 4);

                const startY = 30; 
                const margin = 12;
                
                for (let i = 0; i < count; i++) {
                    const colorIdx = i;
                    const widgetName = `Color ${i + 1}`;
                    const currentHex = (this.properties.colors[colorIdx] || "#FFFFFF").toUpperCase();
                    const rawFmt = (this.properties.formats[colorIdx] || "ASS").toUpperCase();
                    const isHtml = (rawFmt === "HTML" || rawFmt === "HEX");
                    const fmtLabel = isHtml ? "HTML" : "ASS";
                    
                    const y = startY + i * 22;
                    const h = 22;
                    
                    const swatchW = 20;
                    const swatchH = 15;
                    const swatchY = y + Math.floor((h - swatchH) / 2);
                    
                    ctx.fillStyle = currentHex;
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(margin, swatchY, swatchW, swatchH, 3);
                    else ctx.rect(margin, swatchY, swatchW, swatchH);
                    ctx.fill();
                    ctx.strokeStyle = "#ffffff";
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    
                    let currentX = margin + swatchW + 6;
                    ctx.fillStyle = "#cbd5e1";
                    ctx.font = "bold 11px sans-serif";
                    ctx.textAlign = "left";
                    ctx.fillText(widgetName, currentX, y + h / 2 + 4);
                    
                    currentX += ctx.measureText(widgetName).width + 6;
                    ctx.fillStyle = "#38bdf8";
                    ctx.font = "bold 10px monospace";
                    ctx.fillText(currentHex, currentX, y + h / 2 + 3);
                    
                    const fmtBtnW = 44;
                    const fmtBtnH = 16;
                    const fmtBtnX = 142; 
                    const fmtBtnY = y + Math.floor((h - fmtBtnH) / 2);
                    
                    ctx.fillStyle = "#1e293b";
                    ctx.beginPath();
                    if (ctx.roundRect) ctx.roundRect(fmtBtnX, fmtBtnY, fmtBtnW, fmtBtnH, 3);
                    else ctx.rect(fmtBtnX, fmtBtnY, fmtBtnW, fmtBtnH);
                    ctx.fill();
                    ctx.strokeStyle = isHtml ? "#f43f5e" : "#38bdf8";
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    ctx.fillStyle = isHtml ? "#f43f5e" : "#38bdf8";
                    ctx.font = "bold 10px sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(fmtLabel, fmtBtnX + fmtBtnW / 2, y + h / 2 + 4);
                }
            };

            node.onMouseDown = function(e, pos, canvas) {
                if (this.flags && this.flags.collapsed) return false;
                const x = pos[0];
                const y = pos[1];
                const count = this.properties.colors ? this.properties.colors.length : 0;
                const nodeW = this.size[0];
                const centerX = nodeW / 2;

                if (y >= 0 && y < 30) {
                    const btnW = 30;
                    const btnPlusX = centerX - btnW - 4;
                    const btnMinusX = centerX + 4;

                    if (x >= btnPlusX && x <= btnPlusX + btnW) {
                        this.properties.colors.push("#FFFFFF");
                        this.properties.formats.push("ASS");
                        this.updateColorPickerUI();
                        this.setDirtyCanvas(true, true);
                        if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        return true;
                    }
                    if (x >= btnMinusX && x <= btnMinusX + btnW) {
                        if (count > 1) {
                            this.properties.colors.pop();
                            this.properties.formats.pop();
                            this.updateColorPickerUI();
                            this.setDirtyCanvas(true, true);
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                        }
                        return true;
                    }
                    return false;
                }

                const startY = 30;
                if (y >= startY && y < startY + count * 22) {
                    const i = Math.floor((y - startY) / 22);
                    if (i >= 0 && i < count) {
                        const widgetName = `Color ${i + 1}`;
                        const fmtBtnX = 142;
                        const fmtBtnW = 44;
                        
                        if (x >= fmtBtnX - 2 && x <= fmtBtnX + fmtBtnW + 4) {
                            const curr = (this.properties.formats[i] || "ASS").toUpperCase();
                            this.properties.formats[i] = (curr === "ASS") ? "HTML" : "ASS";
                            this.updateColorPickerUI();
                            this.setDirtyCanvas(true, true);
                            if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            return true;
                        } else if (x < fmtBtnX - 2) {
                            showProColorPickerModal(this, i, widgetName, (hexVal) => {
                                this.properties.colors[i] = hexVal;
                                this.setDirtyCanvas(true, true);
                                if (window.__pyxis_schedule_save) window.__pyxis_schedule_save(50);
                            }, e, (liveHex) => {
                                this.properties.colors[i] = liveHex;
                                this.setDirtyCanvas(true, true);
                            });
                            return true;
                        }
                    }
                }
                return false;
            };

            const oldConfig = node.onConfigure;
            node.onConfigure = function(info) {
                if (oldConfig) oldConfig.call(this, info);
                if (this.updateColorPickerUI) this.updateColorPickerUI();
            };

            node.updateColorPickerUI();
        }

        const TAG_DEFINITIONS = {
            "pos": { name: "pos (Position)", desc: "position", params: ["x", "y"], defaults: { x: "fx.pos_x", y: "fx.pos_y" } },
            "move": { name: "move (Movement)", desc: "movement", params: ["x1", "y1", "x2", "y2", "t1", "t2"], defaults: { x1: "0", y1: "0", x2: "100", y2: "100", t1: "", t2: "" } },
            "org": { name: "org (Rotation Origin)", desc: "rotation origin", params: ["x", "y"], defaults: { x: "fx.pos_x", y: "fx.pos_y" } },
            "fad": { name: "fad (Fade In/Out)", desc: "fade in / fade out", params: ["in", "out"], defaults: { in: "0", out: "0" } },
            "fade": { name: "fade (Complex Fade)", desc: "complex fade", params: ["a1", "a2", "a3", "t1", "t2", "t3", "t4"], defaults: { a1: "255", a2: "0", a3: "255", t1: "0", t2: "100", t3: "200", t4: "300" } },
            "clip": { name: "clip (Mask/Drawing)", desc: "mask / drawing", params: ["value"], defaults: { value: "" } },
            "iclip": { name: "iclip (Inverse Mask)", desc: "inverse mask", params: ["value"], defaults: { value: "" } },
            "c": { name: "c (Primary Color)", desc: "primary color", params: ["value"], defaults: { value: "&HFFFFFF&" } },
            "1c": { name: "1c (Primary Color)", desc: "primary color", params: ["value"], defaults: { value: "&HFFFFFF&" } },
            "2c": { name: "2c (Secondary Color)", desc: "secondary color", params: ["value"], defaults: { value: "&HFFFFFF&" } },
            "3c": { name: "3c (Border Color)", desc: "border color", params: ["value"], defaults: { value: "&H000000&" } },
            "4c": { name: "4c (Shadow Color)", desc: "shadow color", params: ["value"], defaults: { value: "&H000000&" } },
            "alpha": { name: "alpha (Transparency)", desc: "general transparency", params: ["value"], defaults: { value: "0" } },
            "1a": { name: "1a (Primary Alpha)", desc: "primary transparency", params: ["value"], defaults: { value: "0" } },
            "2a": { name: "2a (Secondary Alpha)", desc: "secondary transparency", params: ["value"], defaults: { value: "0" } },
            "3a": { name: "3a (Border Alpha)", desc: "border transparency", params: ["value"], defaults: { value: "0" } },
            "4a": { name: "4a (Shadow Alpha)", desc: "shadow transparency", params: ["value"], defaults: { value: "0" } },
            "fscx": { name: "fscx (Scale X)", desc: "horizontal scale X", params: ["value"], defaults: { value: "100" } },
            "fscy": { name: "fscy (Scale Y)", desc: "vertical scale Y", params: ["value"], defaults: { value: "100" } },
            "frz": { name: "frz (Rotation Z)", desc: "rotation along Z axis", params: ["value"], defaults: { value: "0" } },
            "frx": { name: "frx (Rotation X)", desc: "rotation along X axis", params: ["value"], defaults: { value: "0" } },
            "fry": { name: "fry (Rotation Y)", desc: "rotation along Y axis", params: ["value"], defaults: { value: "0" } },
            "fax": { name: "fax (Shear X)", desc: "shear along X axis", params: ["value"], defaults: { value: "0" } },
            "fay": { name: "fay (Shear Y)", desc: "shear along Y axis", params: ["value"], defaults: { value: "0" } },
            "an": { name: "an (Alignment 1-9)", desc: "numeric alignment", params: ["value"], defaults: { value: "5" } },
            "b": { name: "b (Bold)", desc: "bold", params: ["value"], defaults: { value: "1" } },
            "i": { name: "i (Italic)", desc: "italic", params: ["value"], defaults: { value: "1" } },
            "u": { name: "u (Underline)", desc: "underline", params: ["value"], defaults: { value: "1" } },
            "s": { name: "s (Strikeout)", desc: "strikeout", params: ["value"], defaults: { value: "1" } },
            "bord": { name: "bord (Border Width)", desc: "border width", params: ["value"], defaults: { value: "1" } },
            "xbord": { name: "xbord (Border Width X)", desc: "border width X", params: ["value"], defaults: { value: "1" } },
            "ybord": { name: "ybord (Border Width Y)", desc: "border width Y", params: ["value"], defaults: { value: "1" } },
            "shad": { name: "shad (Shadow)", desc: "shadow distance", params: ["value"], defaults: { value: "0" } },
            "xshad": { name: "xshad (Shadow X)", desc: "shadow in X", params: ["value"], defaults: { value: "0" } },
            "yshad": { name: "yshad (Shadow Y)", desc: "shadow in Y", params: ["value"], defaults: { value: "0" } },
            "blur": { name: "blur (Soft Edge)", desc: "soft edge", params: ["value"], defaults: { value: "1" } },
            "be": { name: "be (Edge Blur)", desc: "edge blur", params: ["value"], defaults: { value: "1" } },
            "fs": { name: "fs (Font Size)", desc: "font size", params: ["value"], defaults: { value: "20" } },
            "fsp": { name: "fsp (Letter Spacing)", desc: "letter spacing", params: ["value"], defaults: { value: "0" } },
            "fn": { name: "fn (Font Name)", desc: "font name", params: ["value"], defaults: { value: "Arial" } },
            "r": { name: "r (Reset Style)", desc: "reset style", params: ["value"], defaults: { value: "" } },
            "q": { name: "q (Wrap Style)", desc: "wrap style mode", params: ["value"], defaults: { value: "0" } },
            "k": { name: "k (Karaoke cs)", desc: "karaoke (centiseconds)", params: ["value"], defaults: { value: "0" } },
            "kf": { name: "kf (Smooth Karaoke)", desc: "smooth karaoke", params: ["value"], defaults: { value: "0" } },
            "ko": { name: "ko (Border Karaoke)", desc: "border karaoke", params: ["value"], defaults: { value: "0" } },
            "p": { name: "p (Vector Drawing)", desc: "vector drawing", params: ["value"], defaults: { value: "1" } },
            "pbo": { name: "pbo (Baseline)", desc: "drawing baseline", params: ["value"], defaults: { value: "0" } },
            "t": { name: "t (Animate Tags)", desc: "tag animation", params: ["tags", "t1", "t2", "accel"], defaults: { tags: "", t1: "", t2: "", accel: "" } }
        };

        function getParamValueForPreview(node, paramName, visited) {
            visited = visited || new Set();
            if (visited.has(node.id)) return String(node.properties ? (node.properties[paramName] || "") : "");
            visited.add(node.id);

            if (!node.inputs) return String(node.properties ? (node.properties[paramName] || "") : "");
            const inp = node.inputs.find(i => i.name === paramName);
            if (inp && inp.link !== null && inp.link !== undefined && node.graph && node.graph.links) {
                const link = node.graph.links[inp.link];
                if (link) {
                    const originNode = node.graph.getNodeById(link.origin_id);
                    if (originNode) {
                        const typeName = String(originNode.type || originNode.title || "").toLowerCase();
                        if (typeName.includes("condicionador")) {
                            return getParamValueForPreview(originNode, "If True", visited);
                        }
                        if (typeName.includes("color picker") || originNode.updateColorPickerUI) {
                            if (originNode.properties && Array.isArray(originNode.properties.colors) && originNode.properties.colors.length > 0) {
                                const slotIdx = (link.origin_slot !== undefined && link.origin_slot !== null) ? link.origin_slot : 0;
                                const col = originNode.properties.colors[slotIdx] || originNode.properties.colors[0];
                                return String(col);
                            }
                        }
                        if (originNode.properties) {
                            if (originNode.properties.value !== undefined && originNode.properties.value !== "") {
                                return String(originNode.properties.value);
                            }
                            if (originNode.properties.format !== undefined && originNode.properties.format !== "") {
                                return String(originNode.properties.format);
                            }
                        }
                        if (originNode.widgets && originNode.widgets.length > 0) {
                            const firstW = originNode.widgets[0];
                            if (firstW && firstW.value !== undefined && firstW.value !== null && firstW.value !== "") {
                                return String(firstW.value);
                            }
                        }
                    }
                }
            }
            return String(node.properties && node.properties[paramName] !== undefined ? node.properties[paramName] : "");
        }

        function formatPreviewVal(tagKey, val) {
            val = String(val).trim();
            if (!val) return "";
            if (["c", "1c", "2c", "3c", "4c"].includes(tagKey)) {
                if (val.startsWith("#") && val.length === 7) {
                    const r = val.substring(1, 3);
                    const g = val.substring(3, 5);
                    const b = val.substring(5, 7);
                    return "&H" + (b + g + r).toUpperCase() + "&";
                }
            } else if (["alpha", "1a", "2a", "3a", "4a"].includes(tagKey)) {
                const num = parseInt(val, 10);
                if (!isNaN(num) && !val.includes("&H")) {
                    const hex = Math.max(0, Math.min(255, num)).toString(16).toUpperCase().padStart(2, "0");
                    return "&H" + hex + "&";
                }
            }
            return val;
        }

        const TAG_CATEGORIES = [
            {
                title: "Position & Alignment",
                i18nKey: "ui.picker.tag_cat_pos",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>`,
                tags: ["pos", "move", "org", "an"]
            },
            {
                title: "Color & Transparency",
                i18nKey: "ui.picker.tag_cat_color",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
                tags: ["c", "1c", "2c", "3c", "4c", "alpha", "1a", "2a", "3a", "4a"]
            },
            {
                title: "Scale & Rotation",
                i18nKey: "ui.picker.tag_cat_scale",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>`,
                tags: ["fscx", "fscy", "frz", "frx", "fry", "fax", "fay"]
            },
            {
                title: "Border, Shadow & Blur",
                i18nKey: "ui.picker.tag_cat_border",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 4v16M4 9h16"/></svg>`,
                tags: ["bord", "xbord", "ybord", "shad", "xshad", "yshad", "blur", "be"]
            },
            {
                title: "Typography & Formatting",
                i18nKey: "ui.picker.tag_cat_typography",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>`,
                tags: ["fn", "fs", "fsp", "b", "i", "u", "s", "r", "q"]
            },
            {
                title: "Karaoke, Fades & Animations",
                i18nKey: "ui.picker.tag_cat_anim",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
                tags: ["k", "kf", "ko", "fad", "fade", "t"]
            },
            {
                title: "Clips & Vectors",
                i18nKey: "ui.picker.tag_cat_clips",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M6 3L18 21M18 3L6 21"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="19" r="2"/></svg>`,
                tags: ["clip", "iclip", "p", "pbo"]
            }
        ];

        function openTagGridPicker(node, widget, event) {
            const existing = document.getElementById("pyxis-tag-picker-overlay");
            if (existing) existing.remove();

            const overlay = document.createElement("div");
            overlay.id = "pyxis-tag-picker-overlay";
            overlay.className = "pyxis-tag-picker-overlay";

            const currentTag = (node.properties.tag_type || "pos").toLowerCase();

            const isEs = window.PyxisI18n && window.PyxisI18n.currentLang === "es";
            const pickerTitle = (window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.tag_title") : (isEs ? "Catálogo de Tags ASS (MultiTag)" : "ASS Tag Catalog (MultiTag)");
            const searchPlaceholder = (window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.tag_search") : "Search tag (e.g. \\pos, \\bord)...";

            overlay.innerHTML = `
                <div class="pyxis-tag-picker-dialog">
                    <div class="pyxis-tag-picker-header">
                        <div class="pyxis-tag-picker-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: var(--accent-primary, #8b5cf6); width:18px; height:18px;"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
                            <span>${pickerTitle}</span>
                        </div>
                        <input type="text" class="pyxis-tag-picker-search" id="pyxis-tag-picker-search-input" name="pyxis-tag-picker-search-input" placeholder="${searchPlaceholder}" autofocus>
                        <button class="pyxis-modal-close" id="btn-close-tag-picker" style="background:transparent; border:none; color:var(--text-muted); cursor:pointer;">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:18px; height:18px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div class="pyxis-tag-picker-body" id="pyxis-tag-picker-body-content">
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const searchInput = overlay.querySelector("#pyxis-tag-picker-search-input");
            const bodyContent = overlay.querySelector("#pyxis-tag-picker-body-content");
            const btnClose = overlay.querySelector("#btn-close-tag-picker");

            function renderTags(filterText = "") {
                const cleanFilter = filterText.toLowerCase().replace(/^\\/, "").trim();
                bodyContent.innerHTML = "";

                let matchCount = 0;

                TAG_CATEGORIES.forEach(cat => {
                    const matchingTags = cat.tags.filter(t => {
                        const def = TAG_DEFINITIONS[t];
                        const nameStr = def ? def.name.toLowerCase() : t;
                        const descStr = def ? def.desc.toLowerCase() : "";
                        return t.includes(cleanFilter) || nameStr.includes(cleanFilter) || descStr.includes(cleanFilter);
                    });

                    if (matchingTags.length > 0) {
                        matchCount += matchingTags.length;
                        const catDiv = document.createElement("div");
                        catDiv.className = "pyxis-tag-category";

                        const catTitle = document.createElement("div");
                        catTitle.className = "pyxis-tag-cat-title";
                        const catT = (window.PyxisI18n && typeof window.PyxisI18n.t === "function" && cat.i18nKey) ? window.PyxisI18n.t(cat.i18nKey, null, cat.title) : cat.title;
                        catTitle.innerHTML = `${cat.icon || ""} <span>${catT}</span>`;
                        catDiv.appendChild(catTitle);

                        const grid = document.createElement("div");
                        grid.className = "pyxis-tag-grid";

                        matchingTags.forEach(t => {
                            const def = TAG_DEFINITIONS[t];
                            const label = "\\" + t;
                            const translatedDesc = window.PyxisI18n ? window.PyxisI18n.getTagDesc(t) : "";
                            const titleAttr = translatedDesc || (def ? def.desc || def.name : t);

                            const btn = document.createElement("button");
                            btn.className = "pyxis-tag-btn" + (t === currentTag ? " active" : "");
                            btn.innerText = label;
                            btn.setAttribute("title", titleAttr);

                            btn.onclick = () => {
                                selectTag(t);
                            };

                            grid.appendChild(btn);
                        });

                        catDiv.appendChild(grid);
                        bodyContent.appendChild(catDiv);
                    }
                });

                if (matchCount === 0) {
                    const emptyMsg = isEs ? `No se encontraron tags que coincidan con "${filterText}"` : `No tags matching "${filterText}"`;
                    bodyContent.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px; font-size: 13px;">${emptyMsg}</div>`;
                }
            }

            function selectTag(tagKey) {
                overlay.remove();
                if (node.properties.tag_type !== tagKey) {
                    node.properties.tag_type = tagKey;
                    if (widget) widget.value = tagKey;
                    if (typeof node.updateTagInputs === "function") {
                        node.updateTagInputs();
                    }
                    if (window.PyxisUndoManager) {
                        window.PyxisUndoManager.recordState("tag-type-change");
                    }
                    if (node.setDirtyCanvas) {
                        node.setDirtyCanvas(true, true);
                    }
                }
            }

            renderTags();

            if (searchInput) {
                searchInput.oninput = function() {
                    renderTags(this.value);
                };
                setTimeout(() => searchInput.focus(), 20);
            }

            if (btnClose) {
                btnClose.onclick = () => overlay.remove();
            }

            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };

            const escKeyHandler = (e) => {
                if (e.key === "Escape") {
                    overlay.remove();
                    window.removeEventListener("keydown", escKeyHandler);
                }
            };
            window.addEventListener("keydown", escKeyHandler);
        }

        const SYS_VAR_CATEGORIES = [
            {
                title: "Línea (l. / line.)",
                i18nKey: "ui.categories.line",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M4 6h16M4 12h16M4 18h10"/></svg>`,
                vars: [
                    "l.actor", "l.alpha1", "l.alpha2", "l.alpha3", "l.alpha4",
                    "l.bold", "l.bottom", "l.center", "l.color1", "l.color2", "l.color3", "l.color4",
                    "l.descend", "l.descent", "l.dur", "l.duration", "l.effect", "l.end_time", "l.extlead",
                    "l.fontname", "l.fontsize", "l.height", "l.i", "l.italic", "l.layer", "l.left",
                    "l.margin_b", "l.margin_l", "l.margin_r", "l.margin_t", "l.margin_v", "l.mid_time", "l.middle",
                    "l.n", "l.outline", "l.raw_text", "l.right", "l.scale_x", "l.scale_y", "l.shadow",
                    "l.spacing", "l.start_time", "l.style", "l.text", "l.top", "l.width", "l.x", "l.y"
                ]
            },
            {
                title: "Syllable (syl)",
                i18nKey: "ui.categories.syl",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M4 7h16M4 17h16M7 4v16M17 4v16"/></svg>`,
                vars: [
                    "syl.bottom", "syl.center", "syl.descend", "syl.descent", "syl.dur", "syl.duration",
                    "syl.end_time", "syl.extlead", "syl.height", "syl.i", "syl.left", "syl.mid_time",
                    "syl.middle", "syl.n", "syl.postspace", "syl.postspacewidth", "syl.prespace",
                    "syl.prespacewidth", "syl.right", "syl.start_time", "syl.syl_end", "syl.syl_mid",
                    "syl.syl_start", "syl.text", "syl.top", "syl.width", "syl.x", "syl.y"
                ]
            },
            {
                title: "Character (char)",
                i18nKey: "ui.categories.char",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>`,
                vars: [
                    "char.bottom", "char.center", "char.char_end", "char.char_mid", "char.char_start",
                    "char.descend", "char.descent", "char.dur", "char.duration", "char.end_time",
                    "char.extlead", "char.height", "char.i", "char.left", "char.mid_time",
                    "char.middle", "char.n", "char.right", "char.start_time", "char.syl_end",
                    "char.syl_mid", "char.syl_start", "char.text", "char.top", "char.width", "char.x", "char.y"
                ]
            },
            {
                title: "Word (word)",
                i18nKey: "ui.categories.word",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 15h10M7 9h4"/></svg>`,
                vars: [
                    "word.bottom", "word.center", "word.descend", "word.descent", "word.dur", "word.duration",
                    "word.end_time", "word.extlead", "word.height", "word.i", "word.left", "word.mid_time",
                    "word.middle", "word.n", "word.right", "word.start_time", "word.text", "word.top",
                    "word.width", "word.word_end", "word.word_mid", "word.word_start", "word.x", "word.y"
                ]
            },
            {
                title: "Effect & Modulation (fx)",
                i18nKey: "ui.categories.fx",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
                vars: [
                    "fx.dur", "fx.end_time", "fx.i", "fx.module", "fx.n", "fx.pos_x", "fx.pos_y", "fx.start_time"
                ]
            },
            {
                title: "Loops & Globals",
                i18nKey: "ui.categories.loops",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>`,
                vars: [
                    "frame_dur", "i", "j", "maxj", "module", "n", "ratio"
                ]
            },
            {
                title: "Temporal Offset (time)",
                i18nKey: "ui.categories.time",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
                vars: [
                    "time.lead_in", "time.lead_out", "time.loop_1", "time.loop_2", "time.middle_1", "time.middle_2"
                ]
            },
            {
                title: "Ink Metrics (ink)",
                i18nKey: "ui.categories.ink",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
                vars: [
                    "ink.bottom", "ink.center", "ink.char.bottom", "ink.char.center", "ink.char.height",
                    "ink.char.left", "ink.char.middle", "ink.char.right", "ink.char.top", "ink.char.width",
                    "ink.char.x", "ink.char.y", "ink.height", "ink.l.bottom", "ink.l.center", "ink.l.height",
                    "ink.l.left", "ink.l.middle", "ink.l.right", "ink.l.top", "ink.l.width", "ink.l.x", "ink.l.y",
                    "ink.left", "ink.middle", "ink.right", "ink.syl.bottom", "ink.syl.center", "ink.syl.height",
                    "ink.syl.left", "ink.syl.middle", "ink.syl.right", "ink.syl.top", "ink.syl.width",
                    "ink.syl.x", "ink.syl.y", "ink.top", "ink.width", "ink.word.bottom", "ink.word.center",
                    "ink.word.height", "ink.word.left", "ink.word.middle", "ink.word.right", "ink.word.top",
                    "ink.word.width", "ink.word.x", "ink.word.y", "ink.x", "ink.y"
                ]
            },
            {
                title: "Meta / Project (meta)",
                i18nKey: "ui.categories.meta",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
                vars: [
                    "meta.res_x", "meta.res_y"
                ]
            },
            {
                title: "Neighbors & Context (prev / next)",
                i18nKey: "ui.categories.neighbors",
                icon: `<svg class="svg-icon" viewBox="0 0 24 24" style="width:14px; height:14px; stroke:var(--accent-primary, #8b5cf6); fill:none; stroke-width:2;"><path d="m11 17-5-5 5-5M18 17l-5-5 5-5"/></svg>`,
                vars: [
                    "has_next", "has_prev", "is_first", "is_last",
                    "next.bottom", "next.center", "next.dur", "next.duration", "next.end_time", "next.height",
                    "next.left", "next.middle", "next.right", "next.start_time", "next.text", "next.top",
                    "next.width", "next.x", "next.y",
                    "prev.bottom", "prev.center", "prev.dur", "prev.duration", "prev.end_time", "prev.height",
                    "prev.left", "prev.middle", "prev.right", "prev.start_time", "prev.text", "prev.top",
                    "prev.width", "prev.x", "prev.y"
                ]
            }
        ];

        const ALL_SYS_VARS_LIST = SYS_VAR_CATEGORIES.flatMap(c => c.vars);

        function openSysVarGridPicker(node, widget, event) {
            const existing = document.getElementById("pyxis-sysvar-picker-overlay");
            if (existing) existing.remove();

            const overlay = document.createElement("div");
            overlay.id = "pyxis-sysvar-picker-overlay";
            overlay.className = "pyxis-tag-picker-overlay";

            const currentVar = (node.properties.var_name || "syl.text").trim();

            overlay.innerHTML = `
                <div class="pyxis-tag-picker-dialog">
                    <div class="pyxis-tag-picker-header">
                        <div class="pyxis-tag-picker-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: var(--accent-primary, #8b5cf6); width:18px; height:18px; fill:none; stroke-width:2;"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
                            <span>${(window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.sysvar_title") : "Pyxis System Variables (Sys Var)"}</span>
                        </div>
                        <input type="text" class="pyxis-tag-picker-search" id="pyxis-sysvar-picker-search-input" name="pyxis-sysvar-picker-search-input" placeholder="${(window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.sysvar_search") : "Search variable (e.g. l.text, syl.dur, fx.pos_x)..."}" autofocus>
                        <button class="pyxis-modal-close" id="btn-close-sysvar-picker" style="background:transparent; border:none; color:var(--text-muted); cursor:pointer;">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:18px; height:18px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div class="pyxis-tag-picker-body" id="pyxis-sysvar-picker-body-content">
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const searchInput = overlay.querySelector("#pyxis-sysvar-picker-search-input");
            const bodyContent = overlay.querySelector("#pyxis-sysvar-picker-body-content");
            const btnClose = overlay.querySelector("#btn-close-sysvar-picker");

            function renderVars(filterText = "") {
                const cleanFilter = filterText.toLowerCase().trim();
                bodyContent.innerHTML = "";

                let matchCount = 0;

                SYS_VAR_CATEGORIES.forEach(cat => {
                    const matchingVars = cat.vars
                        .filter(v => v.toLowerCase().includes(cleanFilter))
                        .sort((a, b) => a.localeCompare(b));

                    if (matchingVars.length > 0) {
                        matchCount += matchingVars.length;
                        const catDiv = document.createElement("div");
                        catDiv.className = "pyxis-tag-category";

                        const catTitle = document.createElement("div");
                        catTitle.className = "pyxis-tag-cat-title";
                        const catT = (window.PyxisI18n && typeof window.PyxisI18n.t === "function" && cat.i18nKey) ? window.PyxisI18n.t(cat.i18nKey, null, cat.title) : cat.title;
                        catTitle.innerHTML = `${cat.icon || ""} <span>${catT}</span>`;
                        catDiv.appendChild(catTitle);

                        const grid = document.createElement("div");
                        grid.className = "pyxis-tag-grid";

                        matchingVars.forEach(v => {
                            const btn = document.createElement("button");
                            const isAct = (v === currentVar || (v.startsWith("l.") && currentVar === "line." + v.slice(2)) || (v.startsWith("line.") && currentVar === "l." + v.slice(5)));
                            btn.className = "pyxis-tag-btn" + (isAct ? " active" : "");
                            btn.innerText = v;
                            btn.setAttribute("title", v);

                            btn.onclick = () => {
                                selectVar(v);
                            };

                            grid.appendChild(btn);
                        });

                        catDiv.appendChild(grid);
                        bodyContent.appendChild(catDiv);
                    }
                });

                if (matchCount === 0) {
                    bodyContent.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px; font-size: 13px;">No se encontraron variables que coincidan con "${filterText}"</div>`;
                }

                setTimeout(() => {
                    const activeBtn = bodyContent.querySelector(".pyxis-tag-btn.active");
                    if (activeBtn) {
                        activeBtn.scrollIntoView({ block: "center", behavior: "instant" });
                    }
                }, 30);
            }

            function selectVar(vName) {
                overlay.remove();
                if (node.properties.var_name !== vName) {
                    node.properties.var_name = vName;
                    if (node.properties.modo !== undefined) delete node.properties.modo;
                    if (widget) widget.value = vName;
                    updateNodeModeInputs(node);
                    if (typeof node.updateSysVarInputs === "function") {
                        node.updateSysVarInputs();
                    }
                    if (window.PyxisUndoManager) {
                        window.PyxisUndoManager.recordState("sysvar-type-change");
                    }
                    if (node.setDirtyCanvas) {
                        node.setDirtyCanvas(true, true);
                    }
                }
            }

            renderVars();

            if (searchInput) {
                searchInput.oninput = function() {
                    renderVars(this.value);
                };
                setTimeout(() => searchInput.focus(), 20);
            }

            if (btnClose) {
                btnClose.onclick = () => overlay.remove();
            }

            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };

            const escKeyHandler = (e) => {
                if (e.key === "Escape") {
                    overlay.remove();
                    window.removeEventListener("keydown", escKeyHandler);
                }
            };
            window.addEventListener("keydown", escKeyHandler);
        }

        const MESH_DEFINITIONS = {
            "Grid 1D/2D": { cat: "Standard Grid", name: "Grid 1D/2D", desc: "Rectangular slicing by rows and columns", svg: `<path d="M 0 16 H 48 M 0 32 H 48 M 16 0 V 48 M 32 0 V 48" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" fill="none"/>` },
            "hex": { cat: "Polygonal & Organic", name: "hex (Hexagonal)", desc: "Honeycomb / hexagonal grid", svg: `<path d="M 16 4 L 32 4 L 40 18 L 32 32 L 16 32 L 8 18 Z M 40 18 L 48 18 M 32 32 L 40 46 M 16 32 L 8 46 M 8 18 L 0 18 M 40 18 L 48 32 L 40 46 L 24 46 L 16 32 M 8 18 L 0 32 L 8 46 L 16 46" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>` },
            "tri": { cat: "Polygonal & Organic", name: "tri (Triangular)", desc: "Equilateral triangle grid", svg: `<polygon points="24,4 44,40 4,40" stroke="#a7f3d0" stroke-width="2" fill="none"/><line x1="24" y1="4" x2="24" y2="40" stroke="#a7f3d0" stroke-width="2"/><line x1="14" y1="22" x2="34" y2="22" stroke="#a7f3d0" stroke-width="2"/>` },
            "dia": { cat: "Polygonal & Organic", name: "dia (Diamond)", desc: "Diagonal rhombus grid", svg: `<path d="M 24 4 L 44 24 L 24 44 L 4 24 Z M 24 4 V 44 M 4 24 H 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "ring": { cat: "Technology & Networks", name: "ring (Rings)", desc: "Concentric radial circles", svg: `<circle cx="24" cy="24" r="6" stroke="#a7f3d0" stroke-width="2" fill="none"/><circle cx="24" cy="24" r="13" stroke="#a7f3d0" stroke-width="2" fill="none"/><circle cx="24" cy="24" r="20" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "voronoi": { cat: "Polygonal & Organic", name: "voronoi (Voronoi)", desc: "Organic tessellation / biological cells", svg: `<path d="M 8 8 L 24 16 L 40 8 M 24 16 L 20 36 M 24 16 L 38 28 M 8 8 L 4 28 L 20 36 M 40 8 L 44 26 L 38 28 M 20 36 L 24 44 M 38 28 L 24 44" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" fill="none"/>` },
            "delaunay": { cat: "Polygonal & Organic", name: "delaunay", desc: "Connected geometric triangulation", svg: `<path d="M 6 10 L 26 4 L 42 16 L 38 40 L 14 44 L 6 10 Z M 6 10 L 42 16 M 26 4 L 38 40 M 14 44 L 26 4 L 42 16 M 14 44 L 42 16" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" fill="none"/>` },
            "brick": { cat: "Architecture & Walls", name: "brick (Brick)", desc: "Offset brick wall", svg: `<path d="M 0 12 H 48 M 0 24 H 48 M 0 36 H 48 M 24 0 V 12 M 0 12 V 24 M 48 12 V 24 M 24 24 V 36 M 12 36 V 48 M 36 36 V 48" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "jigsaw": { cat: "Technology & Networks", name: "jigsaw (Puzzle)", desc: "Interlocking puzzle pieces", svg: `<path d="M 4 24 C 14 20 14 28 24 24 C 34 20 34 28 44 24 M 24 4 C 20 14 28 14 24 24 C 20 34 28 34 24 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "circuit": { cat: "Technology & Networks", name: "circuit (Circuit)", desc: "90-degree PCB traces", svg: `<path d="M 4 12 H 20 V 28 H 36 V 44 M 28 4 V 16 H 44 M 4 36 H 16 V 44" stroke="#a7f3d0" stroke-width="2" fill="none"/><circle cx="20" cy="12" r="3" fill="#a7f3d0"/><circle cx="36" cy="28" r="3" fill="#a7f3d0"/>` },
            "kagome": { cat: "Polygonal & Organic", name: "kagome (Japanese)", desc: "6-point tri-hexagonal weave", svg: `<path d="M 12 4 L 36 4 L 44 24 L 36 44 L 12 44 L 4 24 Z M 12 4 L 36 44 M 36 4 L 12 44 M 4 24 H 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "rhombille": { cat: "Polygonal & Organic", name: "rhombille (3D)", desc: "3D rhombic cubes", svg: `<path d="M 24 4 L 44 14 L 24 24 L 4 14 Z M 4 14 V 34 L 24 44 V 24 Z M 44 14 V 34 L 24 44 V 24 Z" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "herringbone": { cat: "Waves & Art", name: "herringbone (Chevron)", desc: "Herringbone / zigzag pattern", svg: `<path d="M 6 6 L 24 20 L 42 6 M 6 18 L 24 32 L 42 18 M 6 30 L 24 44 L 42 30 M 24 6 V 44 M 6 6 V 42 M 42 6 V 42 M 6 20 L 24 6 M 24 32 L 42 18 M 6 32 L 24 18 M 24 44 L 42 30" stroke="#a7f3d0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>` },
            "mondrian": { cat: "Architecture & Walls", name: "mondrian", desc: "Abstract rectangular composition", svg: `<path d="M 0 18 H 48 M 0 34 H 48 M 16 0 V 34 M 32 18 V 48 M 8 34 V 48" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "truchet": { cat: "Waves & Art", name: "truchet (Curves)", desc: "Interlaced modular arcs", svg: `<path d="M 0 24 A 24 24 0 0 1 24 0 M 24 48 A 24 24 0 0 1 48 24 M 24 0 A 24 24 0 0 1 48 24 M 0 24 A 24 24 0 0 0 24 48" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "scallop": { cat: "Waves & Art", name: "scallop (Scales)", desc: "Overlapping wave arcs", svg: `<path d="M 0 16 A 12 12 0 0 1 24 16 A 12 12 0 0 1 48 16 M -12 32 A 12 12 0 0 1 12 32 A 12 12 0 0 1 36 32 A 12 12 0 0 1 60 32" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "ashlar": { cat: "Architecture & Walls", name: "ashlar (Masonry)", desc: "Ashlar stone masonry wall", svg: `<path d="M 0 14 H 48 M 0 30 H 48 M 14 0 V 14 M 34 0 V 14 M 22 14 V 30 M 8 30 V 48 M 38 30 V 48" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "bez": { cat: "Waves & Art", name: "bez (Bézier)", desc: "Fluid waves in Bézier curves", svg: `<path d="M 0 12 C 16 0 32 24 48 12 M 0 24 C 16 12 32 36 48 24 M 0 36 C 16 24 32 48 48 36" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "octagon": { cat: "Polygonal & Organic", name: "octagon", desc: "Interlocking octagons and squares", svg: `<path d="M 12 4 H 36 L 44 12 V 36 L 36 44 H 12 L 4 36 V 12 Z M 12 4 V 44 M 36 4 V 44 M 4 12 H 44 M 4 36 H 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "ray": { cat: "Technology & Networks", name: "ray (Radial Rays)", desc: "Divergent fan rays", svg: `<path d="M 4 4 L 44 44 M 4 24 L 44 24 M 4 44 L 44 4 M 24 4 L 24 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "web": { cat: "Technology & Networks", name: "web (Spiderweb)", desc: "Concentric radial polygonal web", svg: `<path d="M 24 4 L 44 24 L 24 44 L 4 24 Z M 24 12 L 36 24 L 24 36 L 12 24 Z M 24 4 V 44 M 4 24 H 44 M 10 10 L 38 38 M 38 10 L 10 38" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "quad": { cat: "Architecture & Walls", name: "quad (Quadrilateral)", desc: "Progressive quadrilateral subdivision", svg: `<path d="M 4 4 H 44 V 44 H 4 Z M 4 24 H 44 M 24 4 V 44 M 14 4 V 24 M 4 14 H 24 M 24 34 H 44 M 34 24 V 44" stroke="#a7f3d0" stroke-width="2" fill="none"/>` },
            "pattern": { cat: "Architecture & Walls", name: "pattern (Modular)", desc: "Repeating pattern of composite shapes", svg: `<rect x="8" y="8" width="14" height="14" stroke="#a7f3d0" stroke-width="2" fill="none"/><rect x="26" y="26" width="14" height="14" stroke="#a7f3d0" stroke-width="2" fill="none"/><circle cx="33" cy="15" r="7" stroke="#a7f3d0" stroke-width="2" fill="none"/><circle cx="15" cy="33" r="7" stroke="#a7f3d0" stroke-width="2" fill="none"/>` }
        };

        function openMeshGridPicker(node, widget, event) {
            const existing = document.getElementById("pyxis-mesh-picker-overlay");
            if (existing) existing.remove();

            const overlay = document.createElement("div");
            overlay.id = "pyxis-mesh-picker-overlay";
            overlay.className = "pyxis-mesh-picker-overlay";

            const currentMesh = String(node.properties.mode || "Grid 1D/2D");

            overlay.innerHTML = `
                <div class="pyxis-mesh-picker-dialog">
                    <div class="pyxis-tag-picker-header">
                        <div class="pyxis-tag-picker-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: var(--accent-primary, #8b5cf6); width:18px; height:18px;"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                            <span>${window.t ? window.t("ui.picker.mesh_title") : "Mesh & Cut Patterns Gallery (Shape Slicer)"}</span>
                        </div>
                        <input type="text" class="pyxis-tag-picker-search" id="pyxis-mesh-picker-search-input" name="pyxis-mesh-picker-search-input" placeholder="${window.t ? window.t("ui.picker.mesh_search") : "Search engine (e.g. voronoi, hex, bez)..."}" autofocus>
                        <button class="pyxis-modal-close" id="btn-close-mesh-picker" style="background:transparent; border:none; color:var(--text-muted); cursor:pointer;">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:18px; height:18px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div class="pyxis-tag-picker-body" id="pyxis-mesh-picker-body-content">
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const searchInput = overlay.querySelector("#pyxis-mesh-picker-search-input");
            const bodyContent = overlay.querySelector("#pyxis-mesh-picker-body-content");
            const btnClose = overlay.querySelector("#btn-close-mesh-picker");

            const categories = Array.from(new Set(Object.values(MESH_DEFINITIONS).map(m => m.cat)));

            function renderMeshes(filterText = "") {
                const cleanFilter = filterText.toLowerCase().trim();
                bodyContent.innerHTML = "";
                let matchCount = 0;

                categories.forEach(catName => {
                    const keys = Object.keys(MESH_DEFINITIONS).filter(k => {
                        const m = MESH_DEFINITIONS[k];
                        if (m.cat !== catName) return false;
                        if (!cleanFilter) return true;
                        return k.toLowerCase().includes(cleanFilter) || m.name.toLowerCase().includes(cleanFilter) || m.desc.toLowerCase().includes(cleanFilter);
                    });

                    if (keys.length > 0) {
                        matchCount += keys.length;
                        const catDiv = document.createElement("div");
                        catDiv.className = "pyxis-tag-category";

                        const catTitle = document.createElement("div");
                        catTitle.className = "pyxis-tag-cat-title";
                        catTitle.innerHTML = `<span>${catName}</span>`;
                        catDiv.appendChild(catTitle);

                        const grid = document.createElement("div");
                        grid.className = "pyxis-mesh-grid";

                        keys.forEach(k => {
                            const def = MESH_DEFINITIONS[k];
                            const card = document.createElement("div");
                            card.className = "pyxis-mesh-card" + (k === currentMesh ? " active" : "");
                            
                            card.innerHTML = `
                                <div class="pyxis-mesh-svg-box">
                                    <svg viewBox="0 0 48 48" style="width:40px; height:40px;">
                                        ${def.svg}
                                    </svg>
                                </div>
                                <div class="pyxis-mesh-title">${def.name}</div>
                                <div class="pyxis-mesh-desc">${def.desc}</div>
                            `;

                            card.onclick = () => {
                                selectMesh(k);
                            };

                            grid.appendChild(card);
                        });

                        catDiv.appendChild(grid);
                        bodyContent.appendChild(catDiv);
                    }
                });

                if (matchCount === 0) {
                    bodyContent.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px; font-size: 13px;">${window.t ? window.t("ui.picker.mesh_not_found", {query: filterText}) : `No mesh engines found matching "${filterText}"`}</div>`;
                }
            }

            function selectMesh(meshKey) {
                overlay.remove();
                if (node.properties.mode !== meshKey) {
                    node.properties.mode = meshKey;
                    if (node.properties.modo !== undefined) delete node.properties.modo;
                    if (widget) widget.value = meshKey;
                    if (node.updateTagInputs) node.updateTagInputs();
                    else if (typeof updateNodeModeInputs === "function") updateNodeModeInputs(node);
                    if (window.PyxisUndoManager) {
                        window.PyxisUndoManager.recordState("mesh-mode-change");
                    }
                    if (node.setDirtyCanvas) {
                        node.setDirtyCanvas(true, true);
                    }
                }
            }

            renderMeshes();
            setTimeout(() => {
                const activeCard = bodyContent.querySelector(".pyxis-mesh-card.active");
                if (activeCard) {
                    activeCard.scrollIntoView({ block: "center", behavior: "instant" });
                }
            }, 30);

            if (searchInput) {
                searchInput.oninput = function() {
                    renderMeshes(this.value);
                };
                setTimeout(() => searchInput.focus(), 20);
            }

            if (btnClose) {
                btnClose.onclick = () => overlay.remove();
            }

            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };

            const escKeyHandler = (e) => {
                if (e.key === "Escape") {
                    overlay.remove();
                    window.removeEventListener("keydown", escKeyHandler);
                }
            };
            window.addEventListener("keydown", escKeyHandler);
        }

        const SHAPES_LIB_GALLERY_DEFINITIONS = {
            "circle": { cat: "shapes", name: "circle", desc: "circle (shapes)", path: "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0" },
            "triangle": { cat: "shapes", name: "triangle", desc: "triangle (shapes)", path: "m 50 0 l 0 86 l 100 86 l 50 0" },
            "rectangle": { cat: "shapes", name: "rectangle", desc: "rectangle (shapes)", path: "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0" },
            "circangle": { cat: "shapes", name: "circangle", desc: "circangle (shapes)", path: "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0" },
            "pixel": { cat: "shapes", name: "pixel", desc: "pixel (shapes)", path: "m 0 0 l 0 1 l 1 1 l 1 0" },
            "pentagon": { cat: "shapes", name: "pentagon", desc: "pentagon (shapes)", path: "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0" },
            "hexagon": { cat: "shapes", name: "hexagon", desc: "hexagon (shapes)", path: "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301" },
            "octagon": { cat: "shapes", name: "octagon", desc: "octagon (shapes)", path: "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0" },
            "diamond": { cat: "shapes", name: "diamond", desc: "diamond (shapes)", path: "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0" },
            "heart": { cat: "hearts", name: "heart", desc: "heart (hearts)", path: "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25" },
            "heart2t": { cat: "hearts", name: "heart2t", desc: "heart2t (hearts)", path: "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27" },
            "heartb": { cat: "hearts", name: "heartb", desc: "heartb (hearts)", path: "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28" },
            "shine1t": { cat: "shines", name: "shine1t", desc: "shine1t (shines)", path: "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50" },
            "shine2t": { cat: "shines", name: "shine2t", desc: "shine2t (shines)", path: "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50" },
            "shine3t": { cat: "shines", name: "shine3t", desc: "shine3t (shines)", path: "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0" },
            "shine4t": { cat: "shines", name: "shine4t", desc: "shine4t (shines)", path: "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50" },
            "clover": { cat: "specials", name: "clover", desc: "clover (specials)", path: "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99" },
            "feather": { cat: "specials", name: "feather", desc: "feather (specials)", path: "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74" },
            "feather2": { cat: "specials", name: "feather2", desc: "feather2 (specials)", path: "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9" },
            "gear": { cat: "specials", name: "gear", desc: "gear (specials)", path: "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49" },
            "bubble": { cat: "specials", name: "bubble", desc: "bubble (specials)", path: "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94" },
            "note1t": { cat: "music", name: "note1t", desc: "note1t (music)", path: "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70" },
            "note2t": { cat: "music", name: "note2t", desc: "note2t (music)", path: "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70" },
            "note3t": { cat: "music", name: "note3t", desc: "note3t (music)", path: "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29" },
            "note4t": { cat: "music", name: "note4t", desc: "note4t (music)", path: "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73" },
            "star": { cat: "stars", name: "star", desc: "star (stars)", path: "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36" },
            "star1t": { cat: "stars", name: "star1t", desc: "star1t (stars)", path: "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35" },
            "star2t": { cat: "stars", name: "star2t", desc: "star2t (stars)", path: "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29" },
            "star3t": { cat: "stars", name: "star3t", desc: "star3t (stars)", path: "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26" },
            "star4t": { cat: "stars", name: "star4t", desc: "star4t (stars)", path: "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43" },
            "star5t": { cat: "stars", name: "star5t", desc: "star5t (stars)", path: "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29" },
            "star6t": { cat: "stars", name: "star6t", desc: "star6t (stars)", path: "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35" },
            "star7t": { cat: "stars", name: "star7t", desc: "star7t (stars)", path: "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33" },
            "star8t": { cat: "stars", name: "star8t", desc: "star8t (stars)", path: "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36" },
            "star9t": { cat: "stars", name: "star9t", desc: "star9t (stars)", path: "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35" },
            "star10t": { cat: "stars", name: "star10t", desc: "star10t (stars)", path: "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29" },
            "sakura": { cat: "sakura", name: "sakura", desc: "sakura (sakura)", path: "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40" },
            "sakura1t": { cat: "sakura", name: "sakura1t", desc: "sakura1t (sakura)", path: "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53" },
            "sakura2t": { cat: "sakura", name: "sakura2t", desc: "sakura2t (sakura)", path: "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55" },
            "sakura3t": { cat: "sakura", name: "sakura3t", desc: "sakura3t (sakura)", path: "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49" },
            "sakura4t": { cat: "sakura", name: "sakura4t", desc: "sakura4t (sakura)", path: "m 42 59 l 18 59 b 0 59 0 74 0 86 l 25 86 b 36 86 40 70 47 62 l 25 73 l 42 59 m 48 65 l 35 86 b 26 101 38 107 50 114 l 63 93 b 69 85 57 71 53 62 l 51 87 l 48 65 m 57 62 l 69 85 b 77 100 89 92 100 85 l 89 64 b 83 55 67 57 56 57 l 78 71 l 57 62 m 58 55 l 84 55 b 100 55 100 40 100 29 l 76 29 b 65 29 61 43 53 53 l 76 42 l 58 55 m 52 49 l 64 30 b 75 14 62 7 50 0 l 38 18 b 32 29 43 40 47 53 l 50 27 l 52 49 m 44 53 l 33 30 b 24 15 10 23 0 30 l 12 50 b 19 59 35 57 44 57 l 25 43 l 44 53" },
            "sakura5t": { cat: "sakura", name: "sakura5t", desc: "sakura5t (sakura)", path: "m 43 55 b 33 49 4 55 4 65 b 4 76 14 90 24 90 b 33 90 27 74 43 61 l 23 68 l 43 55 m 49 61 b 38 65 27 93 35 99 b 44 105 61 104 66 96 b 72 89 55 85 54 64 l 49 85 l 49 61 m 55 59 b 55 70 75 93 85 88 b 93 83 100 66 96 59 b 91 50 80 63 61 56 l 77 69 l 55 59 m 58 52 b 68 58 98 52 98 41 b 98 31 87 18 77 18 b 68 18 74 33 58 46 l 78 39 l 58 52 m 52 46 b 63 41 74 12 66 6 b 57 0 39 2 33 10 b 29 18 45 22 48 43 l 52 21 l 52 46 m 45 46 b 46 36 25 12 15 18 b 6 24 0 41 5 49 b 10 58 20 43 40 50 l 23 38 l 45 46" },
            "sakura6t": { cat: "sakura", name: "sakura6t", desc: "sakura6t (sakura)", path: "m 46 75 b 29 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 67 68 b 61 85 85 87 100 81 b 96 65 81 48 70 61 l 82 71 l 67 68 m 53 34 b 72 31 64 10 50 0 b 37 10 29 32 46 34 l 50 21 l 53 34 m 69 48 b 79 60 96 43 100 28 b 85 22 61 25 67 41 l 82 38 l 69 48 m 34 41 b 39 25 15 22 0 28 b 3 43 22 60 31 48 l 18 38 l 34 41" },
            "sakura7t": { cat: "sakura", name: "sakura7t", desc: "sakura7t (sakura)", path: "m 46 75 b 28 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 66 68 b 61 85 85 87 100 81 b 96 65 81 48 69 61 l 82 71 l 66 68 m 53 34 b 72 31 64 10 50 0 b 37 10 28 31 46 34 l 50 21 l 53 34 m 69 48 b 81 60 96 43 100 28 b 85 22 61 25 66 41 l 82 38 l 69 48 m 33 41 b 39 25 15 22 0 28 b 4 43 19 60 30 48 l 18 38 l 33 41 m 55 42 b 55 34 44 34 44 42 b 44 50 55 50 55 42 m 55 67 b 55 59 44 59 44 67 b 44 75 55 75 55 67 m 44 48 b 44 40 33 40 33 48 b 33 56 44 56 44 48 m 44 61 b 44 53 33 53 33 61 b 33 69 44 69 44 61 m 66 48 b 66 40 55 40 55 48 b 55 56 66 56 66 48 m 66 61 b 66 53 55 53 55 61 b 55 69 66 69 66 61" },
            "snowflake1t": { cat: "snow", name: "snowflake1t", desc: "snowflake1t (snow)", path: "m 30 45 l 30 52 l 20 52 l 20 55 l 30 55 l 30 62 l 16 70 l 2 61 l 0 64 l 13 72 l 1 79 l 3 82 l 15 75 l 15 90 l 18 90 l 18 73 l 32 65 l 39 69 l 33 78 l 36 80 l 42 71 l 48 74 l 48 89 l 32 98 l 34 101 l 48 93 l 48 108 l 52 108 l 52 93 l 66 101 l 67 98 l 52 89 l 52 74 l 58 71 l 64 80 l 67 78 l 61 69 l 67 65 l 82 73 l 82 90 l 85 90 l 85 75 l 97 82 l 99 79 l 87 72 l 100 64 l 98 61 l 84 70 l 70 62 l 70 55 l 80 55 l 80 52 l 70 52 l 70 45 l 84 37 l 98 46 l 100 43 l 87 35 l 99 28 l 97 25 l 85 32 l 85 16 l 82 17 l 82 34 l 68 42 l 61 38 l 67 30 l 64 28 l 58 36 l 52 33 l 52 18 l 68 9 l 66 6 l 52 14 l 52 0 l 48 0 l 48 14 l 34 6 l 32 9 l 48 18 l 48 33 l 42 36 l 36 28 l 33 30 l 39 38 l 32 42 l 18 34 l 18 17 l 15 16 l 15 32 l 3 25 l 1 28 l 13 35 l 0 43 l 2 46 l 16 37 l 30 45 l 35 45 l 50 37 l 65 45 l 65 62 l 50 70 l 35 62 l 35 45" },
            "snowflake2t": { cat: "snow", name: "snowflake2t", desc: "snowflake2t (snow)", path: "m 18 45 l 14 29 l 6 31 l 8 39 l 0 41 l 2 49 l 18 45 l 21 44 l 32 42 l 42 47 l 32 53 l 21 51 l 19 59 l 27 60 l 23 62 l 8 59 l 5 66 l 13 68 l 11 76 l 19 77 l 23 62 l 27 60 l 25 68 l 33 70 l 35 60 l 46 54 l 46 65 l 38 72 l 35 75 l 22 87 l 28 93 l 35 87 l 42 93 l 48 87 l 35 75 l 38 72 l 45 78 l 50 73 l 56 78 l 62 72 l 65 75 l 52 87 l 59 93 l 65 87 l 71 93 l 78 86 l 65 75 l 62 72 l 54 65 l 54 54 l 65 60 l 67 70 l 75 68 l 73 60 l 77 62 l 80 77 l 89 76 l 87 68 l 95 67 l 93 59 l 77 62 l 73 60 l 80 59 l 78 51 l 68 53 l 58 47 l 68 42 l 78 44 l 81 45 l 97 49 l 100 41 l 92 39 l 94 31 l 86 29 l 81 45 l 78 44 l 80 37 l 73 35 l 75 26 l 67 24 l 67 21 l 84 26 l 86 18 l 77 15 l 79 7 l 71 5 l 67 21 l 67 24 l 65 35 l 54 40 l 54 29 l 63 22 l 57 16 l 50 22 l 50 17 l 62 6 l 56 0 l 50 6 l 44 0 l 38 6 l 50 17 l 50 22 l 43 16 l 37 22 l 46 29 l 46 40 l 35 35 l 33 24 l 33 21 l 29 5 l 21 7 l 23 15 l 14 18 l 16 26 l 33 21 l 33 24 l 25 26 l 27 35 l 19 37 l 21 44" },
            "snowflake3t": { cat: "snow", name: "snowflake3t", desc: "snowflake3t (snow)", path: "m 25 39 l 11 35 l 0 47 l 11 59 l 25 55 l 19 64 l 17 61 l 6 66 l 14 68 l 11 75 l 22 69 l 20 66 l 32 65 l 22 74 l 24 90 l 39 86 l 44 74 l 49 83 l 44 83 l 44 94 l 50 87 l 56 94 l 56 83 l 51 83 l 56 74 l 61 86 l 76 90 l 78 74 l 68 65 l 80 66 l 78 69 l 88 75 l 86 68 l 94 67 l 83 61 l 81 64 l 75 55 l 88 59 l 100 47 l 88 35 l 75 39 l 81 30 l 83 33 l 94 27 l 86 26 l 88 18 l 78 24 l 80 28 l 68 29 l 78 19 l 76 4 l 61 8 l 56 20 l 51 11 l 56 11 l 56 0 l 50 7 l 44 0 l 44 11 l 49 11 l 43 20 l 39 8 l 24 4 l 22 19 l 32 29 l 20 28 l 22 24 l 11 18 l 14 26 l 6 27 l 17 33 l 19 30 l 25 39 l 46 47 b 38 47 29 57 19 47 l 28 41 l 46 47 l 48 43 b 43 36 29 35 34 19 l 42 24 l 48 43 l 52 43 l 58 24 l 66 19 b 71 35 56 36 52 43 l 54 47 l 72 41 l 81 46 b 71 57 62 47 54 47 l 52 51 b 57 58 71 59 66 75 l 58 70 l 52 51 l 48 51 l 42 70 l 34 75 b 29 59 42 58 48 51 l 46 47" },
            "flower1t": { cat: "flowers", name: "flower1t", desc: "flower1t (flowers)", path: "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44" },
            "flower2t": { cat: "flowers", name: "flower2t", desc: "flower2t (flowers)", path: "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 43 15 b 43 6 55 6 55 15 b 55 24 43 24 43 15 m 9 42 b 9 33 21 33 21 42 b 21 51 9 51 9 42 m 23 82 b 23 73 35 73 35 82 b 35 91 23 91 23 82 m 66 82 b 66 73 78 73 78 82 b 78 91 66 91 66 82 m 78 40 b 78 31 90 31 90 40 b 90 49 78 49 78 40" },
            "flower3t": { cat: "flowers", name: "flower3t", desc: "flower3t (flowers)", path: "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 19 23 b 19 14 31 14 31 23 b 31 32 19 32 19 23 m 8 69 b 8 60 20 60 20 69 b 20 78 8 78 8 69 m 48 91 b 48 82 60 82 60 91 b 60 100 48 100 48 91 m 83 62 b 83 53 95 53 95 62 b 95 71 83 71 83 62 m 64 17 b 64 8 76 8 76 17 b 76 26 64 26 64 17 m 44 52 b 44 43 56 43 56 52 b 56 61 44 61 44 52" },
            "flower4t": { cat: "flowers", name: "flower4t", desc: "flower4t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 5 39 b 5 32 15 32 15 39 b 15 46 5 46 5 39 m 84 39 b 84 32 94 32 94 39 b 94 46 84 46 84 39 m 45 11 b 45 4 55 4 55 11 b 55 18 45 18 45 11 m 21 87 b 21 80 31 80 31 87 b 31 94 21 94 21 87 m 70 87 b 70 80 80 80 80 87 b 80 94 70 94 70 87" },
            "flower5t": { cat: "flowers", name: "flower5t", desc: "flower5t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53" },
            "flower6t": { cat: "flowers", name: "flower6t", desc: "flower6t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42 m 40 53 b 40 67 60 67 60 53 b 60 40 40 40 40 53" },
            "flower7t": { cat: "flowers", name: "flower7t", desc: "flower7t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42" },
            "flower8t": { cat: "flowers", name: "flower8t", desc: "flower8t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53" },
            "flower9t": { cat: "flowers", name: "flower9t", desc: "flower9t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53" },
            "flower10t": { cat: "flowers", name: "flower10t", desc: "flower10t (flowers)", path: "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 11 64 b 11 71 21 71 21 64 b 21 57 11 57 11 64 m 80 64 b 80 71 90 71 90 64 b 90 57 80 57 80 64 m 45 89 b 45 96 55 96 55 89 b 55 82 45 82 45 89 m 24 23 b 24 30 34 30 34 23 b 34 16 24 16 24 23 m 66 23 b 66 30 76 30 76 23 b 76 16 66 16 66 23" },
            "flower11t": { cat: "flowers", name: "flower11t", desc: "flower11t (flowers)", path: "m 100 88 b 79 99 57 89 57 62 b 80 75 100 37 100 88 m 49 66 b 49 92 92 92 49 116 b 28 104 25 80 49 66 m 41 62 b 19 75 38 110 0 88 b 0 65 18 48 41 62 m 41 54 b 20 40 0 77 0 28 b 19 17 41 26 41 54 m 49 49 b 49 23 8 23 49 0 b 68 11 71 36 49 49 m 57 54 b 80 40 58 5 100 28 b 100 54 81 67 57 54" },
            "flower12t": { cat: "flowers", name: "flower12t", desc: "flower12t (flowers)", path: "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58 m 24 82 b 24 90 12 90 12 82 b 12 74 24 74 24 82 m 60 97 b 60 105 48 105 48 97 b 48 89 60 89 60 97 m 93 76 b 93 84 81 84 81 76 b 81 68 93 68 93 76 m 91 34 b 91 42 79 42 79 34 b 79 26 91 26 91 34 m 54 17 b 54 25 42 25 42 17 b 42 9 54 9 54 17 m 20 39 b 20 47 8 47 8 39 b 8 31 20 31 20 39" },
            "flower13t": { cat: "flowers", name: "flower13t", desc: "flower13t (flowers)", path: "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58" },
            "flower14t": { cat: "flowers", name: "flower14t", desc: "flower14t (flowers)", path: "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58" },
            "flower15t": { cat: "flowers", name: "flower15t", desc: "flower15t (flowers)", path: "m 30 71 l 33 62 b 16 59 0 59 0 88 b 24 102 33 88 38 74 l 30 71 m 50 84 l 44 77 b 33 88 24 102 50 117 b 76 102 68 88 56 77 l 50 84 m 70 71 l 62 74 b 68 88 76 102 100 88 b 100 59 84 59 67 62 l 70 71 m 70 47 l 67 56 b 84 59 100 59 100 30 b 76 16 67 30 62 45 l 70 47 m 50 35 l 56 42 b 67 30 76 16 50 1 b 24 16 33 30 44 42 l 50 35 m 30 47 l 38 45 b 33 30 24 16 0 30 b 0 59 16 59 33 56 l 30 47 m 0 35 b 0 25 14 25 14 35 b 14 45 0 45 0 35 m 0 83 b 0 73 14 73 14 83 b 14 93 0 93 0 83 m 43 108 b 43 98 57 98 57 108 b 57 118 43 118 43 108 m 43 10 b 43 0 57 0 57 10 b 57 20 43 20 43 10 m 86 83 b 86 73 100 73 100 83 b 100 93 86 93 86 83 m 86 35 b 86 25 100 25 100 35 b 100 45 86 45 86 35" },
            "flower16t": { cat: "flowers", name: "flower16t", desc: "flower16t (flowers)", path: "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 26 29 b 26 19 40 19 40 29 b 40 39 26 39 26 29 m 60 29 b 60 19 74 19 74 29 b 74 39 60 39 60 29 m 9 58 b 9 48 23 48 23 58 b 23 68 9 68 9 58 m 77 58 b 77 48 91 48 91 58 b 91 68 77 68 77 58 m 26 87 b 26 77 40 77 40 87 b 40 97 26 97 26 87 m 60 87 b 60 77 74 77 74 87 b 74 97 60 97 60 87" },
            "flower17t": { cat: "flowers", name: "flower17t", desc: "flower17t (flowers)", path: "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46" },
            "flower18t": { cat: "flowers", name: "flower18t", desc: "flower18t (flowers)", path: "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76 m 5 35 b 5 28 15 28 15 35 b 15 42 5 42 5 35 m 5 81 b 5 74 15 74 15 81 b 15 88 5 88 5 81 m 85 81 b 85 74 95 74 95 81 b 95 88 85 88 85 81 m 85 35 b 85 28 95 28 95 35 b 95 42 85 42 85 35 m 45 104 b 45 97 55 97 55 104 b 55 111 45 111 45 104 m 45 12 b 45 5 55 5 55 12 b 55 19 45 19 45 12" },
            "flower19t": { cat: "flowers", name: "flower19t", desc: "flower19t (flowers)", path: "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76" },
            "flower20t": { cat: "flowers", name: "flower20t", desc: "flower20t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96" },
            "flower21t": { cat: "flowers", name: "flower21t", desc: "flower21t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96" },
            "flower22t": { cat: "flowers", name: "flower22t", desc: "flower22t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58" },
            "flower23t": { cat: "flowers", name: "flower23t", desc: "flower23t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 78 42 l 61 58 l 78 75 l 56 67 l 50 88 l 44 67 l 23 75 l 39 58 l 23 42 l 44 48 l 50 28 l 56 48" },
            "flower24t": { cat: "flowers", name: "flower24t", desc: "flower24t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 94 33 l 61 58 l 94 84 l 56 67 l 50 109 l 44 67 l 6 84 l 39 58 l 6 33 l 44 48 l 50 8 l 56 48" },
            "flower25t": { cat: "flowers", name: "flower25t", desc: "flower25t (flowers)", path: "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46" },
            "flower26t": { cat: "flowers", name: "flower26t", desc: "flower26t (flowers)", path: "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55" },
            "flower27t": { cat: "flowers", name: "flower27t", desc: "flower27t (flowers)", path: "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55" },
            "flower28t": { cat: "flowers", name: "flower28t", desc: "flower28t (flowers)", path: "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55" },
            "flower29t": { cat: "flowers", name: "flower29t", desc: "flower29t (flowers)", path: "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19" },
            "crystal17": { cat: "geometry", name: "crystal17", desc: "crystal17 (geometry)", path: "m 56 50 l 64 100 l 38 78 l 56 50 m 56 50 l 24 100 l 0 65 l 56 50 m 56 50 l 0 65 l 28 39 l 56 50 m 56 50 l 31 0 l 0 28 l 56 50 m 56 50 l 78 0 l 42 22 l 56 50 m 56 50 l 100 40 l 68 23 l 56 50 m 56 50 l 100 40 l 61 80 l 56 50 m 100 40 l 61 80 l 56 50 m 100 40 l 77 64 l 100 100 l 100 40 m 61 80 l 100 100 l 77 64 l 61 80 m 61 80 l 64 100 l 100 100 l 61 80 m 38 78 l 24 100 l 64 100 l 38 78 m 0 65 l 0 100 l 24 100 l 0 65 m 0 28 l 0 65 l 28 39 l 0 28 m 31 0 l 0 0 l 0 28 l 31 0 m 78 0 l 31 0 l 42 22 l 78 0 m 100 0 l 68 23 l 100 40 l 100 0 m 100 0 l 78 0 l 68 23 l 100 0" },
            "geometric10": { cat: "geometry", name: "geometric10", desc: "geometric10 (geometry)", path: "m 0 50 l 0 100 l 100 100 l 100 50 l 90 50 l 90 90 l 10 90 l 10 50 l 0 50 m 0 50 l 10 50 l 10 10 l 90 10 l 90 50 l 100 50 l 100 0 l 0 0 l 0 50 m 50 90 l 50 80 l 20 80 l 20 20 l 50 20 l 50 10 l 10 10 l 10 90 l 50 90 m 50 90 l 90 90 l 90 10 l 50 10 l 50 20 l 80 20 l 80 80 l 50 80 l 50 90 m 20 50 l 20 80 l 80 80 l 80 50 l 70 50 l 70 70 l 30 70 l 30 50 l 20 50 m 20 50 l 30 50 l 30 30 l 70 30 l 70 50 l 80 50 l 80 20 l 20 20 l 20 50 m 50 70 l 50 60 l 40 60 l 40 40 l 50 40 l 50 30 l 30 30 l 30 70 l 50 70 m 50 70 l 70 70 l 70 30 l 50 30 l 50 40 l 60 40 l 60 60 l 50 60 l 50 70 m 40 50 l 40 60 l 60 60 l 60 50 l 40 50 m 40 50 l 60 50 l 60 40 l 40 40 l 40 50" },
            "diagonal13r": { cat: "geometry", name: "diagonal13r", desc: "diagonal13r (geometry)", path: "m 15 0 l 0 0 l 0 15 l 15 0 m 15 0 l 0 15 l 0 30 l 30 0 l 15 0 m 30 0 l 0 30 l 0 45 l 45 0 l 30 0 m 45 0 l 0 45 l 0 60 l 60 0 l 45 0 m 60 0 l 0 60 l 0 75 l 75 0 l 60 0 m 75 0 l 0 75 l 0 90 l 90 0 l 75 0 m 90 0 l 0 90 l 0 100 l 5 100 l 100 5 l 100 0 l 90 0 m 100 5 l 5 100 l 20 100 l 100 20 l 100 5 m 100 20 l 20 100 l 35 100 l 100 35 l 100 20 m 100 35 l 35 100 l 50 100 l 100 50 l 100 35 m 100 50 l 50 100 l 65 100 l 100 65 l 100 50 m 100 65 l 65 100 l 80 100 l 100 80 l 100 65 m 100 80 l 80 100 l 100 100 l 100 80" },
            "diagonal13l": { cat: "geometry", name: "diagonal13l", desc: "diagonal13l (geometry)", path: "m 0 85 l 0 100 l 15 100 l 0 85 m 0 85 l 15 100 l 30 100 l 0 70 l 0 85 m 0 70 l 30 100 l 45 100 l 0 55 l 0 70 m 0 55 l 45 100 l 60 100 l 0 40 l 0 55 m 0 40 l 60 100 l 75 100 l 0 25 l 0 40 m 0 25 l 75 100 l 90 100 l 0 10 l 0 25 m 0 10 l 90 100 l 100 100 l 100 95 l 5 0 l 0 0 l 0 10 m 5 0 l 100 95 l 100 80 l 20 0 l 5 0 m 20 0 l 100 80 l 100 65 l 35 0 l 20 0 m 35 0 l 100 65 l 100 50 l 50 0 l 35 0 m 50 0 l 100 50 l 100 35 l 65 0 l 50 0 m 65 0 l 100 35 l 100 20 l 80 0 l 65 0 m 80 0 l 100 20 l 100 0 l 80 0" },
        };

        function getShapeDefinition(shapeNameOrPath) {
            if (!shapeNameOrPath) return null;
            let s = String(shapeNameOrPath).trim();
            if (s.startsWith("shape.")) {
                s = s.substring(6).trim();
            }
            if (typeof SHAPES_LIB_GALLERY_DEFINITIONS !== 'undefined') {
                return SHAPES_LIB_GALLERY_DEFINITIONS[s] || null;
            }
            return null;
        }

        const _PYXIS_BBOX_CACHE = new Map();
        const _PYXIS_PATH2D_CACHE = new Map();
        const _PYXIS_CACHE_MAX_ENTRIES = 600;

        function getAssPathBBox(assPath) {
            if (!assPath) return { minX: 0, minY: 0, maxX: 100, maxY: 100, w: 100, h: 100, cx: 50, cy: 50 };
            const cached = _PYXIS_BBOX_CACHE.get(assPath);
            if (cached) return cached;

            const tokens = assPath.trim().split(/\s+/);
            const nums = [];
            for (let i = 0; i < tokens.length; i++) {
                const n = parseFloat(tokens[i]);
                if (!isNaN(n)) nums.push(n);
            }
            if (nums.length < 2) {
                const def = { minX: 0, minY: 0, maxX: 100, maxY: 100, w: 100, h: 100, cx: 50, cy: 50 };
                _PYXIS_BBOX_CACHE.set(assPath, def);
                return def;
            }
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            for (let i = 0; i < nums.length - 1; i += 2) {
                const x = nums[i];
                const y = nums[i + 1];
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
            if (!isFinite(minX) || !isFinite(minY)) {
                const def = { minX: 0, minY: 0, maxX: 100, maxY: 100, w: 100, h: 100, cx: 50, cy: 50 };
                _PYXIS_BBOX_CACHE.set(assPath, def);
                return def;
            }
            const w = Math.max(0.001, maxX - minX);
            const h = Math.max(0.001, maxY - minY);
            const res = {
                minX: minX,
                minY: minY,
                maxX: maxX,
                maxY: maxY,
                w: w,
                h: h,
                cx: (minX + maxX) / 2,
                cy: (minY + maxY) / 2
            };

            if (_PYXIS_BBOX_CACHE.size >= _PYXIS_CACHE_MAX_ENTRIES) {
                const firstKey = _PYXIS_BBOX_CACHE.keys().next().value;
                _PYXIS_BBOX_CACHE.delete(firstKey);
            }
            _PYXIS_BBOX_CACHE.set(assPath, res);
            return res;
        }

        function getOrCreateAssPath2D(assPath) {
            if (!assPath) return null;
            let p2d = _PYXIS_PATH2D_CACHE.get(assPath);
            if (p2d) return p2d;

            const svgD = assPathToSvg(assPath);
            if (!svgD) return null;
            p2d = new Path2D(svgD);

            if (_PYXIS_PATH2D_CACHE.size >= _PYXIS_CACHE_MAX_ENTRIES) {
                const firstKey = _PYXIS_PATH2D_CACHE.keys().next().value;
                _PYXIS_PATH2D_CACHE.delete(firstKey);
            }
            _PYXIS_PATH2D_CACHE.set(assPath, p2d);
            return p2d;
        }

        function assPathToSvg(assPath) {
            if (!assPath) return "";
            const tokens = assPath.trim().split(/\s+/);
            let cmd = "";
            const svgTokens = [];
            let i = 0;
            while (i < tokens.length) {
                const t = tokens[i];
                if (!t) { i++; continue; }
                const lower = t.toLowerCase();
                if (lower === "m" || lower === "l" || lower === "b" || lower === "c") {
                    cmd = lower;
                    i++;
                    if (cmd === "c") svgTokens.push("Z");
                    continue;
                }
                if (cmd === "m" && i + 1 < tokens.length) {
                    svgTokens.push(`M ${tokens[i]} ${tokens[i+1]}`);
                    i += 2;
                } else if (cmd === "l" && i + 1 < tokens.length) {
                    svgTokens.push(`L ${tokens[i]} ${tokens[i+1]}`);
                    i += 2;
                } else if (cmd === "b" && i + 5 < tokens.length) {
                    svgTokens.push(`C ${tokens[i]} ${tokens[i+1]}, ${tokens[i+2]} ${tokens[i+3]}, ${tokens[i+4]} ${tokens[i+5]}`);
                    i += 6;
                } else {
                    i++;
                }
            }
            return svgTokens.join(" ");
        }

        function openShapesLibGridPicker(node) {
            const existing = document.getElementById("pyxis-shapes-picker-overlay");
            if (existing) existing.remove();

            const overlay = document.createElement("div");
            overlay.id = "pyxis-shapes-picker-overlay";
            overlay.className = "pyxis-mesh-picker-overlay";

            let currentShape = String((node.properties && node.properties.shape) || "circle");
            if (typeof SHAPES_LIB_ALIASES !== 'undefined' && SHAPES_LIB_ALIASES[currentShape]) {
                currentShape = SHAPES_LIB_ALIASES[currentShape];
            }

            overlay.innerHTML = `
                <div class="pyxis-mesh-picker-dialog">
                    <div class="pyxis-tag-picker-header">
                        <div class="pyxis-tag-picker-title">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="stroke: #8b5cf6; width:18px; height:18px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                            <span>${(window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.shapes_title") : "Vector Shapes Library (Shapes Library)"}</span>
                        </div>
                        <input type="text" class="pyxis-tag-picker-search" id="pyxis-shapes-picker-search-input" name="pyxis-shapes-picker-search-input" placeholder="${(window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("ui.picker.shapes_search") : "Search vector shape (e.g. star, heart, flower, gear)..."}" autofocus>
                        <button class="pyxis-modal-close" id="btn-close-shapes-picker" style="background:transparent; border:none; color:var(--text-muted); cursor:pointer;">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:18px; height:18px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div class="pyxis-tag-picker-body" id="pyxis-shapes-picker-body-content">
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const searchInput = overlay.querySelector("#pyxis-shapes-picker-search-input");
            const bodyContent = overlay.querySelector("#pyxis-shapes-picker-body-content");
            const btnClose = overlay.querySelector("#btn-close-shapes-picker");

            const categories = ["shapes", "hearts", "shines", "specials", "music", "stars", "sakura", "snow", "flowers", "geometry"];

            function renderShapes(filterText = "") {
                const cleanFilter = filterText.toLowerCase().trim();
                bodyContent.innerHTML = "";

                categories.forEach(catName => {
                    const matchedKeys = Object.keys(SHAPES_LIB_GALLERY_DEFINITIONS).filter(shapeKey => {
                        const item = SHAPES_LIB_GALLERY_DEFINITIONS[shapeKey];
                        if (item.cat !== catName) return false;
                        if (!cleanFilter) return true;
                        return shapeKey.toLowerCase().includes(cleanFilter) || item.name.toLowerCase().includes(cleanFilter);
                    });

                    if (matchedKeys.length === 0) return;

                    const section = document.createElement("div");
                    section.className = "pyxis-mesh-picker-section";
                    const catDisplay = (window.PyxisI18n && typeof window.PyxisI18n.t === "function") ? window.PyxisI18n.t("categories." + catName) : catName;
                    section.innerHTML = `<div class="pyxis-mesh-picker-section-title">${catDisplay} (${matchedKeys.length})</div>`;

                    const grid = document.createElement("div");
                    grid.className = "pyxis-mesh-grid";

                    matchedKeys.forEach(shapeKey => {
                        const def = SHAPES_LIB_GALLERY_DEFINITIONS[shapeKey];
                        const card = document.createElement("div");
                        const isActive = (shapeKey === currentShape || def.name === currentShape);
                        card.className = `pyxis-mesh-card ${isActive ? 'active' : ''}`;
                        
                        let svgContent = "";
                        if (def.name === "pixel" || shapeKey === "pixel") {
                            svgContent = `<svg viewBox="-20 -20 40 40" style="width:40px; height:40px;">
                                <rect x="-5" y="-5" width="10" height="10" fill="#a7f3d0" stroke="#a7f3d0" stroke-width="1.5" rx="1.5"/>
                            </svg>`;
                        } else {
                            const svgPath = assPathToSvg(def.path);
                            const bbox = getAssPathBBox(def.path);
                            const maxDim = Math.max(bbox.w, bbox.h);
                            const pad = maxDim * 0.12;
                            const vbX = bbox.cx - (maxDim / 2 + pad);
                            const vbY = bbox.cy - (maxDim / 2 + pad);
                            const vbSize = maxDim + pad * 2;

                            svgContent = `<svg viewBox="${vbX} ${vbY} ${vbSize} ${vbSize}" style="width:40px; height:40px;">
                                <path d="${svgPath}" fill="rgba(139, 92, 246, 0.3)" stroke="#a7f3d0" stroke-width="${vbSize * 0.035}" stroke-linejoin="round" stroke-linecap="round"/>
                            </svg>`;
                        }

                        card.innerHTML = `
                            <div class="pyxis-mesh-svg-box">
                                ${svgContent}
                            </div>
                            <div class="pyxis-mesh-title">${def.name}</div>
                            <div class="pyxis-mesh-desc" style="font-family: monospace; color: #a7f3d0; font-size: 10px;">shape.${shapeKey}</div>
                        `;

                        card.onclick = () => {
                            if (!node.properties) node.properties = {};
                            node.properties.category = catName;
                            node.properties.shape = shapeKey;
                            if (node.properties.categoria !== undefined) delete node.properties.categoria;
                            if (node.properties.forma !== undefined) delete node.properties.forma;
                            if (node.properties.modo !== undefined) delete node.properties.modo;
                            if (node.widgets) {
                                const w = node.widgets.find(w => w.name === "shape" || w.name === "mode");
                                if (w) {
                                    w.value = shapeKey;
                                    if (w.callback) w.callback(w.value);
                                }
                            }
                            node._cachedShapePath = null;
                            if (node.setDirtyCanvas) node.setDirtyCanvas(true, true);
                            overlay.remove();
                        };

                        grid.appendChild(card);
                    });

                    section.appendChild(grid);
                    bodyContent.appendChild(section);
                });
            }

            renderShapes();
            setTimeout(() => {
                const activeCard = bodyContent.querySelector(".pyxis-mesh-card.active");
                if (activeCard) {
                    activeCard.scrollIntoView({ block: "center", behavior: "instant" });
                }
            }, 30);

            if (searchInput) {
                searchInput.oninput = (e) => renderShapes(e.target.value);
                setTimeout(() => searchInput.focus(), 20);
            }

            if (btnClose) {
                btnClose.onclick = () => overlay.remove();
            }

            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };

            const escKeyHandler = (e) => {
                if (e.key === "Escape") {
                    overlay.remove();
                    document.removeEventListener("keydown", escKeyHandler);
                }
            };
            document.addEventListener("keydown", escKeyHandler);
        }

        function showFFmpegDownloadModal(onCompleteCallback) {
            const existing = document.querySelector(".pyxis-ffmpeg-modal-overlay");
            if (existing) existing.remove();

            const overlay = document.createElement("div");
            overlay.className = "pyxis-modal-overlay pyxis-ffmpeg-modal-overlay";

            const container = document.createElement("div");
            container.className = "pyxis-modal-dialog pyxis-ffmpeg-modal-dialog";
            container.style.width = "460px";
            container.style.padding = "16px 20px";
            container.style.gap = "10px";
            container.style.borderRadius = "12px";
            container.style.boxShadow = "0 16px 40px rgba(0, 0, 0, 0.6)";

            const titleText = window.t ? window.t("ffmpeg.title") : "FFmpeg Native Provisioning";
            const descText = window.t ? window.t("ffmpeg.desc") : "FFmpeg is required to process audio, render waveforms, and preview or export videos with hardsub subtitles. Would you like to download the official native build for your system? (~190 MB)";
            const dlBtnText = window.t ? window.t("ffmpeg.download_btn") : "Download FFmpeg";
            const cancelBtnText = window.t ? window.t("ffmpeg.cancel_btn") : "Cancel";

            container.innerHTML = `
                <div class="pyxis-modal-header" style="padding-bottom:10px; margin-bottom:0; border-bottom:1px solid var(--border-subtle, rgba(255,255,255,0.08));">
                    <div class="pyxis-modal-title" style="display:flex; align-items:center; gap:8px; font-weight:600; font-size:15px; color:var(--accent-primary, #22858c);">
                        <svg class="svg-icon" viewBox="0 0 24 24" style="width:20px; height:20px; fill:none; stroke:currentColor; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0;">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        <span>${titleText}</span>
                    </div>
                    <button class="pyxis-modal-close" id="btn-ffmpeg-modal-close" style="background:transparent; border:none; color:var(--text-muted); cursor:pointer; font-size:18px; line-height:1; padding:2px 6px;">&times;</button>
                </div>
                <div id="ffmpeg-modal-body" style="font-size:13px; line-height:1.45; color:var(--text-secondary); margin-bottom:0;">
                    ${descText}
                </div>
                <div id="ffmpeg-modal-progress-wrap" style="display:none; margin:0;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:5px; color:var(--text-main);">
                        <span id="ffmpeg-progress-status">Starting download...</span>
                        <span id="ffmpeg-progress-pct" style="font-weight:600; color:var(--accent-primary, #22858c);">0%</span>
                    </div>
                    <div style="width:100%; height:7px; background:var(--bg-input, rgba(0,0,0,0.3)); border-radius:4px; overflow:hidden;">
                        <div id="ffmpeg-progress-bar" style="width:0%; height:100%; background:var(--accent-primary, #22858c); transition:width 0.2s ease;"></div>
                    </div>
                </div>
                <div id="ffmpeg-modal-actions" style="display:flex; justify-content:flex-end; gap:10px; margin-top:2px;">
                    <button id="btn-ffmpeg-cancel" class="pyxis-btn pyxis-btn-secondary" style="padding:6px 14px; border-radius:6px; cursor:pointer; font-size:13px;">${cancelBtnText}</button>
                    <button id="btn-ffmpeg-download" class="pyxis-btn pyxis-btn-primary" style="padding:6px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px;">${dlBtnText}</button>
                </div>
            `;

            overlay.appendChild(container);
            document.body.appendChild(overlay);

            let pollInterval = null;
            function cleanup() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
                overlay.remove();
            }

            const btnClose = container.querySelector("#btn-ffmpeg-modal-close");
            const btnCancel = container.querySelector("#btn-ffmpeg-cancel");
            const btnDownload = container.querySelector("#btn-ffmpeg-download");
            const progressWrap = container.querySelector("#ffmpeg-modal-progress-wrap");
            const progressBar = container.querySelector("#ffmpeg-progress-bar");
            const progressStatus = container.querySelector("#ffmpeg-progress-status");
            const progressPct = container.querySelector("#ffmpeg-progress-pct");
            const actionsWrap = container.querySelector("#ffmpeg-modal-actions");

            if (btnClose) btnClose.onclick = () => { cleanup(); if (onCompleteCallback) onCompleteCallback(false); };
            if (btnCancel) btnCancel.onclick = () => { cleanup(); if (onCompleteCallback) onCompleteCallback(false); };

            if (btnDownload) {
                btnDownload.onclick = async () => {
                    actionsWrap.style.display = "none";
                    progressWrap.style.display = "block";
                    if (btnClose) btnClose.disabled = true;

                    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.start_ffmpeg_download) {
                        progressStatus.textContent = "Error: Backend API unavailable.";
                        return;
                    }

                    await window.pywebview.api.start_ffmpeg_download();

                    pollInterval = setInterval(async () => {
                        try {
                            const state = await window.pywebview.api.get_ffmpeg_download_progress();
                            if (!state) return;

                            const pct = Math.max(0, Math.min(100, state.progress || 0));
                            progressBar.style.width = pct + "%";
                            progressPct.textContent = pct + "%";

                            if (state.status === "resolving") {
                                progressStatus.textContent = window.t ? window.t("ffmpeg.status_resolving") : "Resolving release...";
                            } else if (state.status === "downloading") {
                                progressStatus.textContent = state.detail || (window.t ? window.t("ffmpeg.status_downloading", { percent: pct }) : `Downloading (${pct}%)...`);
                            } else if (state.status === "verifying") {
                                progressStatus.textContent = window.t ? window.t("ffmpeg.status_verifying") : "Verifying SHA-256...";
                            } else if (state.status === "extracting") {
                                progressStatus.textContent = window.t ? window.t("ffmpeg.status_extracting") : "Extracting native binary...";
                            } else if (state.status === "ready") {
                                clearInterval(pollInterval);
                                pollInterval = null;
                                progressBar.style.width = "100%";
                                progressPct.textContent = "100%";
                                progressStatus.textContent = window.t ? window.t("ffmpeg.status_ready") : "FFmpeg installed successfully!";
                                progressStatus.style.color = "var(--color-success, #4caf50)";
                                setTimeout(() => {
                                    cleanup();
                                    if (window.showPyxisToast) {
                                        window.showPyxisToast(window.t ? window.t("ffmpeg.status_ready") : "FFmpeg installed successfully!", "success");
                                    }
                                    if (onCompleteCallback) onCompleteCallback(true);
                                }, 1200);
                            } else if (state.status === "error") {
                                clearInterval(pollInterval);
                                pollInterval = null;
                                progressStatus.textContent = (window.t ? window.t("ffmpeg.status_error", { error: state.error }) : ("Error: " + state.error));
                                progressStatus.style.color = "var(--color-danger, #f44336)";
                                actionsWrap.style.display = "flex";
                                if (btnCancel) btnCancel.textContent = window.t ? window.t("preview.cancel") : "Close";
                                if (btnDownload) {
                                    btnDownload.textContent = "Retry";
                                    btnDownload.disabled = false;
                                }
                                if (btnClose) btnClose.disabled = false;
                            }
                        } catch (err) {
                            console.error("[Pyxis FFmpeg Poll Error]", err);
                        }
                    }, 300);
                };
            }
        }

        window.getAssPathBBox = getAssPathBBox;
        window.getOrCreateAssPath2D = getOrCreateAssPath2D;
        window.assPathToSvg = assPathToSvg;
        window.openShapesLibGridPicker = openShapesLibGridPicker;
        window.showFFmpegDownloadModal = showFFmpegDownloadModal;


