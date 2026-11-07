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
 * @file canvas_controller.js
 * @description Core canvas controller and graph lifecycle manager for Pyxis Effector.
 * Coordinates LiteGraph.js instance initialisation, viewport navigation (pan, zoom, fit),
 * undo/redo command pattern integration, generation pipeline execution, workload estimation,
 * and diagnostic pre-generation validation dialogues.
 * @module PyxisCanvasController
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */
        /* =============================================================================
           ESTÁNDAR DE CAPAS Y JERARQUÍA Z-INDEX (UI STACKING ARCHITECTURE)
           =============================================================================
           * Tier 0: Canvas (#node_canvas: 1, fondo: 0)
           * Tier 1: Nodos y Previews intercalados (baseZ: 1000 + nodeIdx*1000, fgCanvas: segmentZ)
           * Tier 2: Herramientas contextuales, buscador y barra superior (.graphdialog: 80000, inputs inline: 90000, .top-bar / .litecontextmenu: 100000)
           * Tier 3: Flotantes desanclados (#pyxis-floating-players-container: 150000, wrapper: 150010, resizer: 150050)
           * Tier 4: Modales y Pantalla Completa (.pyxis-template-overlay / .pyxis-modal-overlay / pickers: 2000000, subdiálogos: 2000010 - 2000500)
           * Tier 5: Diálogos de confirmación (#pyxis-confirm-modal: 5000000)
           * Tier 6: Reproductor en Fullscreen (.pyxis-player-fullscreen: 10000000, controles: 10000010)
           * Tier 7: Notificaciones Toast (#pyxis-toast-container: 50000000)
           * Tier 8: Pantalla de carga inicial (#pyxis-loading-overlay: 100000000)
           Consulta pyxis_ui.css para la documentación detallada.
           ============================================================================= */

        window.onerror = function (msg, url, lineNo, columnNo, error) {
            const errStr = `${msg} at ${lineNo}:${columnNo}`;
            console.error("[Pyxis JS ERROR]", errStr, error);
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.log_js_error === "function") {
                window.pywebview.api.log_js_error(errStr);
            }
            return false;
        };

        window.addEventListener("unhandledrejection", function (event) {
            const reason = event.reason;
            const errStr = `Unhandled Promise Rejection: ${reason && reason.stack ? reason.stack : reason}`;
            console.error("[Pyxis JS PROMISE REJECTION]", errStr);
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.log_js_error === "function") {
                window.pywebview.api.log_js_error(errStr);
            }
        });

        window.gridMode = 0;
        window.backgroundImageSettings = {
            path: "",
            mode: "contain",
            opacity: 0.5
        };
        let bgImageElement = null;

        function normalizeSize(size, defaultW, defaultH) {
            if (Array.isArray(size) && size.length >= 2) {
                return [Number(size[0]), Number(size[1])];
            }
            if (size && typeof size === "object") {
                let w = Number(size[0] !== undefined ? size[0] : (size["0"] !== undefined ? size["0"] : defaultW));
                let h = Number(size[1] !== undefined ? size[1] : (size["1"] !== undefined ? size["1"] : defaultH));
                return [w, h];
            }
            return [defaultW, defaultH];
        }

        function showPyxisToast(message, type = "success", duration = 2400, params = null) {
            let toastContainer = document.getElementById("pyxis-toast-container");
            if (!toastContainer) {
                toastContainer = document.createElement("div");
                toastContainer.id = "pyxis-toast-container";
                toastContainer.className = "pyxis-toast-container";
                toastContainer.style.cssText = "position: fixed; z-index: 50000000; display: flex; flex-direction: column; gap: 6px; pointer-events: none;";
                document.body.appendChild(toastContainer);
            }

            const isKey = typeof message === "string" && (message.startsWith("toast.") || message.startsWith("preview.") || message.startsWith("common."));
            const finalMsg = (window.t && isKey) ? window.t(message, params) : message;

            const toast = document.createElement("div");
            let bgColor = "#064e3b";
            let borderColor = "#10b981";
            let textColor = "#a7f3d0";
            let iconSvg = `<svg style="width:14px;height:14px;color:#10b981;flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;

            if (type === "loading") {
                bgColor = "#082f49";
                borderColor = "#0284c7";
                textColor = "#bae6fd";
                iconSvg = `<svg class="pyxis-spin" style="width:14px;height:14px;color:#38bdf8;flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
            } else if (type === "source" || type === "note" || type === "info") {
                bgColor = "#064e3b";
                borderColor = "#10b981";
                textColor = "#a7f3d0";
                iconSvg = `<svg style="width:14px;height:14px;color:#10b981;flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M9 12h6"/><path d="M9 16h6"/></svg>`;
            } else if (type === "warning") {
                bgColor = "#78350f";
                borderColor = "#f59e0b";
                textColor = "#fde68a";
                iconSvg = `<svg style="width:14px;height:14px;color:#f59e0b;flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 1 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
            } else if (type === "error") {
                bgColor = "#7f1d1d";
                borderColor = "#ef4444";
                textColor = "#fca5a5";
                iconSvg = `<svg style="width:14px;height:14px;color:#ef4444;flex-shrink:0;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
            }

            toast.style.cssText = `background: ${bgColor}; border: 1px solid ${borderColor}; color: ${textColor}; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: sans-serif; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 14px rgba(0,0,0,0.4); pointer-events: none; opacity: 0; transform: translateY(8px); transition: all 0.2s ease;`;
            toast.innerHTML = `${iconSvg}<span ${isKey ? `data-i18n="${message}"` : ""}>${finalMsg}</span>`;
            
            toastContainer.appendChild(toast);

            requestAnimationFrame(() => {
                toast.style.opacity = "1";
                toast.style.transform = "translateY(0)";
            });

            let dismissTimer = null;
            if (duration > 0) {
                dismissTimer = setTimeout(() => {
                    toast.style.opacity = "0";
                    toast.style.transform = "translateY(8px)";
                    setTimeout(() => toast.remove(), 200);
                }, duration);
            }

            return {
                element: toast,
                close: function() {
                    if (dismissTimer) clearTimeout(dismissTimer);
                    toast.style.opacity = "0";
                    toast.style.transform = "translateY(8px)";
                    setTimeout(() => toast.remove(), 200);
                }
            };
        }
        window.showPyxisToast = showPyxisToast;

        function updateTemplateUIState() {
            const btnTop = document.getElementById("btn-quick-save-template");
            if (window.__pyxis_is_loading_template) {
                if (btnTop) btnTop.style.display = "none";
                return;
            }

            const activeId = window.__pyxis_active_template_id;
            const activeName = window.__pyxis_active_template_name;

            if (!btnTop) return;

            if (!activeId || !activeName) {
                btnTop.style.display = "none";
                return;
            }

            let hasChanges = false;
            if (typeof window.has_template_changes === "function") {
                hasChanges = window.has_template_changes();
            } else {
                hasChanges = true;
            }

            if (hasChanges) {
                if (btnTop.style.display !== "inline-flex") {
                    btnTop.style.display = "inline-flex";
                }
                btnTop.setAttribute("data-tooltip", `Save changes in "${activeName}" (1 click)`);
            } else {
                btnTop.style.display = "none";
            }
        }
        window.updateTemplateUIState = updateTemplateUIState;

        window.addEventListener("mouseup", () => setTimeout(updateTemplateUIState, 50));
        window.addEventListener("keyup", () => setTimeout(updateTemplateUIState, 50));

        async function quickSaveActiveTemplate() {
            const activeId = window.__pyxis_active_template_id;
            const activeName = window.__pyxis_active_template_name;

            if (!activeId || !activeName) {
                if (typeof window.open_template_save_dialog === "function") {
                    window.open_template_save_dialog();
                }
                return;
            }

            const activeGraph = window.graph || (typeof graph !== "undefined" ? graph : null);
            const activeCanvas = window.canvas || (typeof canvas !== "undefined" ? canvas : null);
            if (!activeGraph || typeof activeGraph.serialize !== "function") return;

            if (typeof window.syncWidgetsToProperties === "function") {
                window.syncWidgetsToProperties();
            }

            if (activeCanvas && activeCanvas.ds) {
                activeGraph.extra = activeGraph.extra || {};
                activeGraph.extra.canvas_zoom = activeCanvas.ds.scale;
                activeGraph.extra.canvas_offset = [activeCanvas.ds.offset[0], activeCanvas.ds.offset[1]];
            }

            const serialized = activeGraph.serialize();
            if (!serialized || !Array.isArray(serialized.nodes) || serialized.nodes.length === 0) {
                showPyxisToast("toast.graph_empty", "warning");
                return;
            }
            if (serialized) {
                serialized.extra = serialized.extra || {};
                if (activeCanvas && activeCanvas.ds) {
                    serialized.extra.canvas_zoom = activeCanvas.ds.scale;
                    serialized.extra.canvas_offset = [activeCanvas.ds.offset[0], activeCanvas.ds.offset[1]];
                }
            }

            try {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.save_template) {
                    const meta = await window.pywebview.api.save_template(activeName, "", serialized, activeId);
                    window.__pyxis_active_template_id = meta.template_id;
                    window.__pyxis_active_template_name = meta.name;
                    if (meta.template_id) {
                        localStorage.setItem("pyxis_active_template_id", meta.template_id);
                        localStorage.setItem("pyxis_active_template_name", meta.name);
                        localStorage.setItem("pyxis_last_used_template_id", meta.template_id);
                        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_user_config === "function") {
                            window.pywebview.api.save_user_config({
                                active_template_id: meta.template_id,
                                active_template_name: meta.name
                            });
                        }
                    }
                    if (typeof window.syncWidgetsToProperties === "function") {
                        window.syncWidgetsToProperties();
                    }
                    if (typeof window.update_checkpoint === "function") {
                        window.update_checkpoint();
                    } else if (typeof window.update_template_checkpoint === "function") {
                        window.update_template_checkpoint();
                    }
                    if (typeof window.__pyxis_schedule_save === "function") {
                        window.__pyxis_schedule_save(50);
                    }
                    const btnTop = document.getElementById("btn-quick-save-template");
                    if (btnTop) btnTop.style.display = "none";
                    updateTemplateUIState();
                    showPyxisToast("toast.template_saved", "success");
                }
            } catch (err) {
                console.error("Pyxis: Error saving template changes", err);
                showPyxisToast("toast.template_save_error", "error");
            }
        }
        window.quickSaveActiveTemplate = quickSaveActiveTemplate;

        let __pyxis_save_timer = null;
        function scheduleSessionSave(delayMs = 100) {
            const activeGraph = window.graph || (typeof graph !== "undefined" ? graph : null);
            const activeCanvas = window.canvas || (typeof canvas !== "undefined" ? canvas : null);
            if (window.__pyxis_is_loading_template || !activeGraph || typeof activeGraph.serialize !== "function") return;
            if (__pyxis_save_timer) clearTimeout(__pyxis_save_timer);
            __pyxis_save_timer = setTimeout(async () => {
                __pyxis_save_timer = null;
                try {
                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_session === "function") {
                        if (typeof window.syncWidgetsToProperties === "function") {
                            window.syncWidgetsToProperties();
                        }
                        const serialized = activeGraph.serialize();
                        if (serialized && Array.isArray(serialized.nodes) && serialized.nodes.length > 0) {
                            if (!serialized.extra) serialized.extra = {};
                            serialized.extra.active_template_id = window.__pyxis_active_template_id || null;
                            serialized.extra.active_template_name = window.__pyxis_active_template_name || null;
                            if (activeCanvas && activeCanvas.ds) {
                                serialized.extra.canvas_zoom = activeCanvas.ds.scale;
                                serialized.extra.canvas_offset = [activeCanvas.ds.offset[0], activeCanvas.ds.offset[1]];
                            }
                            await window.pywebview.api.save_session(serialized);
                        }
                    }
                } catch (e) {
                    console.warn("[Pyxis scheduleSessionSave warning]", e);
                }
            }, delayMs);
        }
        window.__pyxis_schedule_save = scheduleSessionSave;

        function triggerSave() {
            if (typeof window.open_save_dialog === "function") {
                window.open_save_dialog();
            } else {
                alert(window.PyxisI18n ? PyxisI18n.t("ui.notifications.saving_init") : "Saving module is initializing...");
            }
        }

        function triggerSaveAs() {
            if (typeof window.open_save_as_dialog === "function") {
                window.open_save_as_dialog();
            } else {
                alert(window.PyxisI18n ? PyxisI18n.t("ui.notifications.saving_init") : "Saving module is initializing...");
            }
        }

        function triggerLibrary() {
            if (typeof window.open_template_library_modal === "function") {
                window.open_template_library_modal();
            } else {
                alert(window.PyxisI18n ? PyxisI18n.t("ui.notifications.library_init") : "Template library is initializing...");
            }
        }

        if (LiteGraph.clearRegisteredTypes) LiteGraph.clearRegisteredTypes();
        else LiteGraph.registered_node_types = {};

        LiteGraph.NODE_TITLE_COLOR = "#FFFFFF";
        LiteGraph.NODE_TEXT_COLOR = "#FFFFFF";
        LiteGraph.NODE_SELECTED_TITLE_COLOR = "#FFFFFF";
        LiteGraph.NODE_BOX_OUTLINE_COLOR = "rgba(255, 255, 255, 0.2)";
        LiteGraph.NODE_TITLE_HEIGHT = 30;
        LiteGraph.NODE_SLOT_HEIGHT = 20;
        LiteGraph.NODE_WIDGET_HEIGHT = 26;

        var graph = new LGraph();
        var canvas = new LGraphCanvas("#node_canvas", graph);
        window.graph = graph;
        window.canvas = canvas;
        window.graphcanvas = canvas;

        if (canvas && canvas.canvas) {
            canvas.canvas.addEventListener("wheel", function(e) {
                if (canvas && typeof canvas.processMouseWheel === "function") {
                    canvas.processMouseWheel(e);
                }
            }, { passive: false });
        }

        if (canvas && canvas.ds) {
            const _origOnRedraw = canvas.ds.onredraw;
            canvas.ds.onredraw = function(ds) {
                if (_origOnRedraw) _origOnRedraw.apply(this, arguments);
                if (typeof window.__pyxis_schedule_save === "function") {
                    window.__pyxis_schedule_save(150);
                }
            };
        }
        canvas.background_color = (window.PyxisThemeManager && window.PyxisThemeManager.THEMES && typeof window.PyxisThemeManager.getCurrentTheme === 'function' && window.PyxisThemeManager.THEMES[window.PyxisThemeManager.getCurrentTheme()]) ? window.PyxisThemeManager.THEMES[window.PyxisThemeManager.getCurrentTheme()].canvasBg : "#0d0f12";
        window.addEventListener("resize", () => canvas.resize());
        setTimeout(() => canvas.resize(), 50);

        window.addEventListener("pyxis:languageChanged", () => {
            if (window.PyxisI18n && typeof window.PyxisI18n.applyToDOM === "function") {
                window.PyxisI18n.applyToDOM(document);
            }
            if (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers) {
                for (const nId in window.PyxisNodePlayerManager.activePlayers) {
                    const p = window.PyxisNodePlayerManager.activePlayers[nId];
                    if (p && p.node) {
                        const curSrc = (p.node.properties && p.node.properties.preview_source) || "base";
                        const hasAegi = (p.hasAegisub !== undefined) ? p.hasAegisub : (window.PyxisPreviewConfig && window.PyxisPreviewConfig.has_aegisub);
                        if (typeof window.PyxisNodePlayerManager.updateSourceButtonUI === "function") {
                            window.PyxisNodePlayerManager.updateSourceButtonUI(nId, curSrc, hasAegi);
                        }
                    }
                }
            }
            if (window.graph && window.graph._nodes) {
                window.graph._nodes.forEach(node => {
                    const isPreviewer = node && (node.type === "System/Previewer" || node.type === "Previewer" || (node.title && (node.title.includes("Previewer") || node.title.includes("Previsualizador"))));
                    if (!isPreviewer) {
                        if (typeof node.computeSize === "function") {
                            node.size = node.computeSize();
                        }
                    }
                    if (typeof node.updateVarsSize === "function") {
                        node.updateVarsSize();
                    }
                    if (typeof node.setDirtyCanvas === "function") {
                        node.setDirtyCanvas(true, true);
                    }
                });
            }
            if (canvas && typeof canvas.draw === "function") {
                canvas.draw(true, true);
            }
        });

        (function () {
            // Re-export canonicalize in window scope for compatibility and determinism
            window.canonicalize = window.canonicalize || function(obj) {
                if (obj === null || typeof obj !== "object") return obj;
                if (Array.isArray(obj)) return obj.map(window.canonicalize);
                const sortedKeys = Object.keys(obj).sort();
                const result = {};
                for (let i = 0; i < sortedKeys.length; i++) {
                    const key = sortedKeys[i];
                    if (key === "viewport_zoom" || key === "viewport_pan_x" || key === "viewport_pan_y" || key === "viewport_custom") {
                        continue;
                    }
                    result[key] = window.canonicalize(obj[key]);
                }
                return result;
            };

            const closeContextMenusIfOutside = (e) => {
                if (window.LiteGraph && typeof window.LiteGraph.closeAllContextMenus === "function") {
                    if (!e.target || typeof e.target.closest !== "function" || !e.target.closest(".litecontextmenu")) {
                        window.LiteGraph.closeAllContextMenus();
                    }
                }
            };

            window.addEventListener("pointerdown", closeContextMenusIfOutside, true);
            window.addEventListener("mousedown", closeContextMenusIfOutside, true);
            window.addEventListener("blur", () => {
                if (window.LiteGraph && typeof window.LiteGraph.closeAllContextMenus === "function") {
                    window.LiteGraph.closeAllContextMenus();
                }
            });

            window.addEventListener("keydown", function (e) {
                const isCtrl = e.ctrlKey || e.metaKey;
                if (!isCtrl || e.altKey) return;

                const k = (e.key || "").toLowerCase();
                const isZ = (k === "z" || e.code === "KeyZ" || e.keyCode === 90);
                const isY = (k === "y" || e.code === "KeyY" || e.keyCode === 89);

                if (!isZ && !isY) return;

                const target = e.target;
                const isTyping = target && (
                    (target.tagName === "INPUT" && target.type !== "button" && target.type !== "submit") ||
                    target.tagName === "TEXTAREA" ||
                    target.isContentEditable ||
                    (target.classList && target.classList.contains("ace_text-input"))
                );

                // If user is currently typing in an input/textarea, do NOT intercept graph undo/redo!
                // Let the browser/input handle its native text editing undo.
                if (isTyping) {
                    return;
                }

                const isAnyModalOpen = () => {
                    const modals = document.querySelectorAll(".pyxis-template-overlay, .pyxis-settings-overlay, .pyxis-modal-overlay, .pyxis-theme-settings-overlay, .pyxis-mesh-picker-overlay");
                    for (let i = 0; i < modals.length; i++) {
                        const m = modals[i];
                        if (m.offsetParent !== null || (window.getComputedStyle(m).display !== "none" && window.getComputedStyle(m).visibility !== "hidden")) {
                            return true;
                        }
                    }
                    return false;
                };

                if (isAnyModalOpen()) return;

                e.preventDefault();
                e.stopPropagation();
                if (typeof e.stopImmediatePropagation === "function") {
                    e.stopImmediatePropagation();
                }

                if (window.pyxisCommandManager) {
                    if (isZ) {
                        if (e.shiftKey) {
                            window.pyxisCommandManager.redo();
                        } else {
                            window.pyxisCommandManager.undo();
                        }
                    } else if (isY) {
                        window.pyxisCommandManager.redo();
                    }
                }
            }, true);
        })();

        // --- Hooking Granular Command Pattern with LiteGraph ---
        const nodeDragStartPositions = new Map();

        if (canvas && canvas.canvas) {
            canvas.canvas.addEventListener("pointerdown", function(e) {
                nodeDragStartPositions.clear();
                if (graph && Array.isArray(graph._nodes)) {
                    graph._nodes.forEach(n => {
                        if (n && n.pos) {
                            nodeDragStartPositions.set(n.id, [n.pos[0], n.pos[1]]);
                        }
                    });
                }
            }, true);
        }

        canvas.onNodeMoved = function(node) {
            if (window.__pyxis_is_restoring_state || (window.PyxisUndoManager && window.PyxisUndoManager.isExecuting())) return;
            
            const moves = [];
            if (graph && Array.isArray(graph._nodes) && nodeDragStartPositions.size > 0) {
                graph._nodes.forEach(n => {
                    const startPos = nodeDragStartPositions.get(n.id);
                    if (startPos && (startPos[0] !== n.pos[0] || startPos[1] !== n.pos[1])) {
                        moves.push({
                            id: n.id,
                            from: [startPos[0], startPos[1]],
                            to: [n.pos[0], n.pos[1]]
                        });
                        nodeDragStartPositions.set(n.id, [n.pos[0], n.pos[1]]);
                    }
                });
            }

            if (moves.length > 0 && window.pyxisCommandManager && window.MoveNodesCommand) {
                const nodeDesc = node ? (node.title || node.type || `#${node.id}`) : "node";
                const desc = moves.length === 1 ? `move-node: ${nodeDesc}` : `move ${moves.length} nodes`;
                const cmd = new window.MoveNodesCommand(moves, desc);
                window.pyxisCommandManager.execute(cmd, true);
            }

            if (typeof window.updateTemplateUIState === "function") {
                window.updateTemplateUIState();
            }
        };

        const origBeforeChange = graph.beforeChange;
        graph.beforeChange = function() {
            if (origBeforeChange) origBeforeChange.apply(this, arguments);
        };

        const origGraphChange = graph.change;
        graph.change = function() {
            // Note: Camera navigation, pan, and zoom trigger graph.change() internally in LiteGraph.
            // We strictly DO NOT record undo states here to prevent viewport movements from polluting history!
            if (origGraphChange) origGraphChange.apply(this, arguments);
            if (typeof window.updateTemplateUIState === "function") {
                window.updateTemplateUIState();
            }
        };

        const origOnNodeAdded = graph.onNodeAdded;
        graph.onNodeAdded = function(node) {
            if (origOnNodeAdded) origOnNodeAdded.apply(this, arguments);
            if (!window.__pyxis_is_restoring_state && !window.__pyxis_is_loading_template && !window.__pyxis_is_pasting && !(window.PyxisUndoManager && window.PyxisUndoManager.isExecuting())) {
                if (window.pyxisCommandManager && window.AddNodeCommand && node) {
                    const nodeDesc = node.title || node.type || `#${node.id}`;
                    const cmd = new window.AddNodeCommand(node, `add-node: ${nodeDesc}`);
                    window.pyxisCommandManager.execute(cmd, true);
                }
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            }
        };

        const origDeleteSelectedNodes = canvas.deleteSelectedNodes;
        canvas.deleteSelectedNodes = function() {
            if (window.__pyxis_is_restoring_state || (window.PyxisUndoManager && window.PyxisUndoManager.isExecuting()) || window.__pyxis_is_loading_template) {
                return origDeleteSelectedNodes.apply(this, arguments);
            }

            const nodesToDelete = [];
            for (const id in this.selected_nodes) {
                const n = this.selected_nodes[id];
                if (n && !n.block_delete) {
                    nodesToDelete.push(n);
                }
            }

            if (nodesToDelete.length === 0) {
                return origDeleteSelectedNodes.apply(this, arguments);
            }

            const cmd = (window.pyxisCommandManager && window.RemoveNodesCommand) ? new window.RemoveNodesCommand(nodesToDelete) : null;
            window.__pyxis_batch_removing = true;
            try {
                origDeleteSelectedNodes.apply(this, arguments);
            } finally {
                window.__pyxis_batch_removing = false;
            }

            if (cmd && window.pyxisCommandManager) {
                window.pyxisCommandManager.execute(cmd, true);
            }
            if (typeof window.updateTemplateUIState === "function") {
                setTimeout(window.updateTemplateUIState, 50);
            }
        };

        const origGraphRemove = graph.remove;
        graph.remove = function(node) {
            if (window.__pyxis_is_restoring_state || (window.PyxisUndoManager && window.PyxisUndoManager.isExecuting()) || window.__pyxis_is_loading_template || window.__pyxis_batch_removing) {
                return origGraphRemove.apply(this, arguments);
            }

            const cmd = (node && window.pyxisCommandManager && window.RemoveNodesCommand) ? new window.RemoveNodesCommand(node) : null;
            const res = origGraphRemove.apply(this, arguments);
            if (cmd && window.pyxisCommandManager) {
                window.pyxisCommandManager.execute(cmd, true);
            }
            if (typeof window.updateTemplateUIState === "function") {
                setTimeout(window.updateTemplateUIState, 50);
            }
            return res;
        };

        const origNodeConnect = LiteGraph.LGraphNode.prototype.connect;
        LiteGraph.LGraphNode.prototype.connect = function(slot, target_node, target_slot) {
            const res = origNodeConnect.apply(this, arguments);
            if (res && !window.__pyxis_is_restoring_state && !window.__pyxis_is_loading_template && !window.__pyxis_is_pasting && !(window.PyxisUndoManager && window.PyxisUndoManager.isExecuting())) {
                const targetId = (typeof target_node === "object" && target_node) ? target_node.id : target_node;
                if (window.pyxisCommandManager && window.ConnectLinkCommand) {
                    const cmd = new window.ConnectLinkCommand(this.id, slot, targetId, target_slot, res.id);
                    window.pyxisCommandManager.execute(cmd, true);
                }
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            }
            return res;
        };

        const origNodeDisconnectInput = LiteGraph.LGraphNode.prototype.disconnectInput;
        LiteGraph.LGraphNode.prototype.disconnectInput = function(slot) {
            if (window.__pyxis_is_restoring_state || window.__pyxis_is_loading_template || (window.PyxisUndoManager && window.PyxisUndoManager.isExecuting()) || window.__pyxis_batch_removing) {
                return origNodeDisconnectInput.apply(this, arguments);
            }

            let linkInfo = null;
            if (this.inputs && this.inputs[slot] && this.graph && this.graph.links) {
                const lId = this.inputs[slot].link;
                if (lId != null) {
                    linkInfo = this.graph.links[lId];
                }
            }

            const res = origNodeDisconnectInput.apply(this, arguments);
            if (res && linkInfo && window.pyxisCommandManager && window.DisconnectLinkCommand) {
                const cmd = new window.DisconnectLinkCommand(linkInfo.origin_id, linkInfo.origin_slot, linkInfo.target_id, linkInfo.target_slot, linkInfo.id);
                window.pyxisCommandManager.execute(cmd, true);
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            }
            return res;
        };

        const origPasteFromClipboard = canvas.pasteFromClipboard;
        if (origPasteFromClipboard) {
            canvas.pasteFromClipboard = function() {
                const beforeSnap = (typeof window.getSafeSnapshot === "function") ? window.getSafeSnapshot() : null;
                window.__pyxis_is_pasting = true;
                let res;
                try {
                    res = origPasteFromClipboard.apply(this, arguments);
                } finally {
                    window.__pyxis_is_pasting = false;
                }
                const afterSnap = (typeof window.getSafeSnapshot === "function") ? window.getSafeSnapshot() : null;
                if (beforeSnap && afterSnap && beforeSnap !== afterSnap && window.pyxisCommandManager && window.FallbackSnapshotCommand) {
                    const cmd = new window.FallbackSnapshotCommand(beforeSnap, afterSnap, "paste");
                    window.pyxisCommandManager.execute(cmd, true);
                }
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
                return res;
            };
        }

        function closeAllActiveNodeEditors(save = true) {
            let hadActiveEditor = false;
            if (typeof currentPromptFinish === "function") {
                hadActiveEditor = true;
                try {
                    currentPromptFinish(save);
                } catch(e) {}
                currentPromptFinish = null;
            }
            const promptOverlay = document.getElementById("pyxis-inline-input-overlay");
            if (promptOverlay && promptOverlay.style.display !== "none") {
                hadActiveEditor = true;
                promptOverlay.style.display = "none";
                promptOverlay.onkeydown = null;
                promptOverlay.onblur = null;
                promptOverlay.oninput = null;
                promptOverlay._finish = null;
            }

            const multiLine = document.getElementById("pyxis-inline-textarea-overlay");
            if (multiLine && multiLine.style.display !== "none") {
                hadActiveEditor = true;
                multiLine.onkeydown = null;
                multiLine.onblur = null;
                multiLine.oninput = null;
                if (save && typeof multiLine._finish === "function") {
                    try { multiLine._finish(true); } catch(e) {}
                } else {
                    multiLine.style.display = "none";
                    multiLine._finish = null;
                }
            }

            const singleLine = document.getElementById("pyxis-inline-text-editor");
            if (singleLine) {
                hadActiveEditor = true;
                singleLine.onblur = null;
                singleLine.onkeydown = null;
                singleLine.oninput = null;
                if (save && typeof singleLine._saveAndClose === "function") {
                    try { singleLine._saveAndClose(); } catch(e) {}
                } else {
                    if (singleLine.parentNode) singleLine.parentNode.removeChild(singleLine);
                }
            }

            const varsEditor = document.getElementById("pyxis-inline-vars-editor-container");
            if (varsEditor) {
                hadActiveEditor = true;
                if (typeof varsEditor._saveAndClose === "function") {
                    try { varsEditor._saveAndClose(); } catch(e) {}
                } else if (varsEditor.parentNode) {
                    varsEditor.parentNode.removeChild(varsEditor);
                }
            }

            const canvasObj = LGraphCanvas.active_canvas || window.canvas;
            if (canvasObj && canvasObj.prompt_box) {
                hadActiveEditor = true;
                try {
                    if (typeof canvasObj.prompt_box.close === "function") {
                        canvasObj.prompt_box.close();
                    }
                } catch(e) {}
                canvasObj.prompt_box = null;
            }
            const dialogs = document.querySelectorAll(".graphdialog");
            if (dialogs.length > 0) {
                hadActiveEditor = true;
                dialogs.forEach(d => {
                    try {
                        if (typeof d.close === "function") d.close();
                        else if (d.parentNode) d.parentNode.removeChild(d);
                    } catch(e) {}
                });
            }
            if (hadActiveEditor && typeof window.updateTemplateUIState === "function") {
                setTimeout(window.updateTemplateUIState, 50);
            }
        }
        window.closeAllActiveNodeEditors = closeAllActiveNodeEditors;

        let currentPromptFinish = null;

        LGraphCanvas.prototype.prompt = function(title, value, callback, event, multiline) {
            if (currentPromptFinish) {
                currentPromptFinish(true);
                currentPromptFinish = null;
            }

            const canvasEl = this.canvas;
            if (!canvasEl) return;
            const rect = canvasEl.getBoundingClientRect();
            const scale = this.ds.scale || 1.0;
            const offset = this.ds.offset || [0, 0];

            let clickedNode = null;
            if (event && this.graph) {
                const mouseCanvasX = (event.clientX - rect.left - offset[0] * scale) / scale;
                const mouseCanvasY = (event.clientY - rect.top - offset[1] * scale) / scale;
                clickedNode = this.graph.getNodeOnPos(mouseCanvasX, mouseCanvasY);
            }

            const node = (clickedNode)
                ? clickedNode
                : ((this.node_widget && this.node_widget[0])
                    ? this.node_widget[0]
                    : ((this.selected_nodes && Object.keys(this.selected_nodes).length > 0)
                        ? Object.values(this.selected_nodes)[0]
                        : (this.current_node || this.node_over)));

            let widget = (clickedNode && clickedNode === (this.node_widget && this.node_widget[0])) ? this.node_widget[1] : null;

            if (event && node && node.widgets) {
                const mouseScreenY = event.clientY;
                const nodeScreenY = rect.top + (node.pos[1] + offset[1]) * scale;
                const relYInNode = (mouseScreenY - nodeScreenY) / scale;

                const foundW = node.widgets.find(w => {
                    if (w.last_y === undefined) return false;
                    const topY = w.last_y;
                    const calcH = (w.computeSize) ? w.computeSize(node.size[0])[1] : 18;
                    const bottomY = w.last_y + calcH;
                    return relYInNode >= (topY - 2) && relYInNode <= (bottomY + 2);
                });

                if (foundW) {
                    widget = foundW;
                }
            }

            let targetX = event ? event.clientX : (rect.left + rect.width / 2);
            let targetY = event ? event.clientY : (rect.top + rect.height / 2);
            let widgetW = 160 * scale;
            let widgetH = 26 * scale;

            const isSalidaNode = (node && (node.title === "Output" || (node.type && String(node.type).includes("Output"))));
            const isPolaresNode = !!(node && (
                node.category === "Time" ||
                node.category === "Audio" ||
                node.title === "Polar to Cartesian" ||
                node.title === "Concatenate" ||
                node.title === "Previewer" ||
                node.title === "Modulator" ||
                node.title === "Waveform" ||
                node.title === "Lead In" || node.title === "Lead Out" ||
                node.title === "Middle 1" || node.title === "Middle 2" ||
                node.title === "Loop 1" || node.title === "Loop 2" ||
                node.title === "Ipol" ||
                node.title === "Synced" ||
                node.title === "Text to Shape" ||
                node.title === "IMG to Shape" ||
                node.title === "Bezier Curve" ||
                node.title === "Curva Bézier" ||
                node.title === "Text on Path" ||
                node.title === "Concentric Borders" ||
                node.title === "Bordes Concéntricos" ||
                node.title === "Move Tag" ||
                node.title === "Move Text" ||
                (node.type && (
                    String(node.type).includes("Polares") ||
                    String(node.type).includes("Concatenate") ||
                    String(node.type).includes("Previewer") ||
                    String(node.type).includes("Text to Shape") ||
                    String(node.type).includes("Text on Path") ||
                    String(node.type).includes("Concentric") ||
                    String(node.type).includes("Bordes") ||
                    String(node.type).includes("IMG to Shape") ||
                    String(node.type).includes("Bezier") ||
                    String(node.type).includes("Curva") ||
                    String(node.type).includes("preview") ||
                    String(node.type).includes("Time") ||
                    String(node.type).includes("Audio") ||
                    String(node.type).includes("Interpolator") ||
                    String(node.type).includes("Move Tag") ||
                    String(node.type).includes("Move Text")
                ))
            ));
            const isInlineWidgetNode = isSalidaNode || isPolaresNode;
            const promptMargin = isInlineWidgetNode ? 22 : 12;

            if (node && node.pos) {
                const nodeScreenX = rect.left + (node.pos[0] + offset[0]) * scale;
                const nodeScreenY = rect.top + (node.pos[1] + offset[1]) * scale;
                
                const lastY = (widget && widget.last_y !== undefined) ? widget.last_y : null;
                const wY = lastY !== null ? (lastY * scale) : (38 * scale);
                const wX = promptMargin * scale;
                
                if (isSalidaNode) {
                    const minSalidaBoxW = 75;
                    const promptVal = (widget && widget.value !== undefined && widget.value !== null)
                        ? String(widget.value)
                        : (value !== undefined && value !== null ? String(value) : "");
                    const dispText = promptVal.length > 0 ? promptVal : (widget ? widget.name || title || "" : title || "");
                    const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(dispText, "bold 11px Consolas, monospace") : (dispText.length * 6.0);
                    const calcW = Math.max(minSalidaBoxW, Math.ceil(tw + 25));
                    const maxW = Math.max(minSalidaBoxW, (node.size ? node.size[0] : 200) - promptMargin - 20);
                    widgetW = Math.min(maxW, calcW) * scale;
                    widgetH = 18 * scale;
                } else if (isPolaresNode) {
                    const promptVal = (widget && widget.value !== undefined && widget.value !== null)
                        ? String(widget.value)
                        : (value !== undefined && value !== null ? String(value) : "");
                    const dispText = promptVal.length > 0 ? promptVal : (widget ? widget.name || title || "" : title || "");
                    const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(dispText, "bold 11px Consolas, monospace") : (dispText.length * 6.0);
                    const calcW = Math.max(65, Math.ceil(tw + 36));
                    const maxW = Math.max(50, (node.size ? node.size[0] : 200) - promptMargin - 20);
                    widgetW = Math.min(maxW, calcW) * scale;
                    widgetH = 18 * scale;
                } else if (isInlineWidgetNode) {
                    const promptVal = (widget && widget.value !== undefined && widget.value !== null)
                        ? String(widget.value)
                        : (value !== undefined && value !== null ? String(value) : "");
                    const dispText = promptVal.length > 0 ? promptVal : (widget ? widget.name || title || "" : title || "");
                    const calcW = Math.max(120, dispText.length * 8.5 + 24);
                    widgetW = Math.min(node.size[0] - promptMargin - 12, calcW) * scale;
                    widgetH = 26 * scale;
                } else {
                    widgetW = (node.size[0] - 24) * scale;
                    widgetH = 26 * scale;
                }

                if (!isInlineWidgetNode) {
                    const calcH = (widget && widget.computeSize) ? widget.computeSize(node.size[0])[1] : 26;
                    widgetH = calcH * scale;
                }

                targetX = nodeScreenX + wX;
                targetY = nodeScreenY + wY;
            }

            let overlay = document.getElementById("pyxis-inline-input-overlay");
            if (!overlay) {
                overlay = document.createElement("textarea");
                overlay.id = "pyxis-inline-input-overlay";
                overlay.name = "pyxis-inline-input-overlay";
                document.body.appendChild(overlay);
            }

            const initialVal = (widget && widget.value !== undefined && widget.value !== null)
                ? String(widget.value)
                : (value !== undefined && value !== null ? String(value) : "");

            const initialLines = Math.max(1, initialVal.split('\n').length);
            const curH = initialLines === 1 ? widgetH : Math.max(widgetH, (initialLines * 22 + 6) * scale);

            overlay.style.boxSizing = "border-box";
            overlay.style.margin = "0";
            overlay.style.position = "fixed";
            overlay.style.left = Math.max(0, targetX) + "px";
            overlay.style.top = Math.max(0, targetY) + "px";
            overlay.style.width = Math.max(65 * scale, widgetW) + "px";
            overlay.style.height = curH + "px";
            overlay.style.lineHeight = isPolaresNode ? (Math.max(14, 18 * scale) + "px") : (initialLines === 1 ? (Math.max(16, (widgetH - 6) / scale) + "px") : "18px");
            overlay.style.zIndex = "2000100";
            overlay.style.background = "#12161f";
            overlay.style.color = "#a7f3d0";
            overlay.style.border = "1.5px solid #8b5cf6";
            overlay.style.borderRadius = (isPolaresNode || isSalidaNode) ? "5px" : (initialLines === 1 ? "13px" : "8px");
            overlay.style.padding = isSalidaNode ? ("0px " + Math.max(2, Math.round(10 * scale)) + "px 0px " + Math.max(2, Math.round(6 * scale)) + "px") : ((isPolaresNode) ? ("0px " + Math.max(2, Math.round(6 * scale)) + "px 0px " + Math.max(4, Math.round(8 * scale)) + "px") : (initialLines === 1 ? "3px 10px 0 10px" : "4px 10px"));
            overlay.style.fontFamily = (isPolaresNode || isSalidaNode) ? "Consolas, monospace" : "monospace";
            overlay.style.fontSize = (isPolaresNode || isSalidaNode) ? (Math.max(9, Math.round(11 * scale)) + "px") : (Math.max(11, Math.min(15, 12 * scale)) + "px");
            overlay.style.fontWeight = "bold";
            overlay.style.boxShadow = "0 0 12px rgba(139, 92, 246, 0.7)";
            overlay.style.outline = "none";
            overlay.style.resize = "none";
            overlay.style.overflow = "hidden";
            overlay.style.scrollBehavior = "auto";
            overlay.style.display = "block";
            overlay.style.whiteSpace = initialLines === 1 ? "nowrap" : "pre-wrap";

            overlay.spellcheck = false;
            overlay.value = initialVal;

            if (!isSalidaNode) {
                overlay.onscroll = function() {
                    overlay.scrollLeft = 0;
                };
            }

            const syncSizeAndNode = () => {
                if (!isMultilineNode) {
                    overlay.value = overlay.value.replace(/[\r\n]+/g, " ");
                }
                if (widget) {
                    widget.value = overlay.value;
                    if (widget.property && node && node.properties) {
                        node.properties[widget.property] = overlay.value;
                    }
                }
                if (node && node.computeSize) {
                    node.size = node.computeSize();
                }

                const lines = overlay.value.split('\n');
                const lCount = Math.max(1, lines.length);
                const nextH = lCount === 1 ? widgetH : Math.max(widgetH, (lCount * 22 + 6) * scale);
                
                let nextW = widgetW;
                if (isSalidaNode) {
                    const minSalidaBoxW = 75;
                    const promptVal = overlay.value || (widget ? widget.name || title || "" : title || "");
                    const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(promptVal, "bold 11px Consolas, monospace") : (promptVal.length * 6.0);
                    const calcW = Math.max(minSalidaBoxW, Math.ceil(tw + 25));
                    const maxW = Math.max(minSalidaBoxW, (node.size ? node.size[0] : 200) - promptMargin - 20);
                    nextW = Math.min(maxW, calcW) * scale;
                } else if (isPolaresNode) {
                    const promptVal = overlay.value || (widget ? widget.name || title || "" : title || "");
                    const tw = (typeof getExactTextWidth === "function") ? getExactTextWidth(promptVal, "bold 11px Consolas, monospace") : (promptVal.length * 6.0);
                    const calcW = Math.max(65, Math.ceil(tw + 36));
                    const maxW = Math.max(50, (node.size ? node.size[0] : 200) - promptMargin - 20);
                    nextW = Math.min(maxW, calcW) * scale;
                } else if (isInlineWidgetNode) {
                    const promptVal = overlay.value || (widget ? widget.name || title || "" : title || "");
                    const calcW = Math.max(120, promptVal.length * 8.5 + 24);
                    const maxNodeW = node && node.size ? node.size[0] : 200;
                    nextW = Math.min(maxNodeW - promptMargin - 12, calcW) * scale;
                } else {
                    nextW = (node && node.size) ? Math.max(widgetW, (node.size[0] - 24) * scale) : widgetW;
                }
                
                overlay.style.width = nextW + "px";
                overlay.style.height = nextH + "px";
                if (isSalidaNode) {
                    overlay.style.borderRadius = "5px";
                    overlay.style.padding = "0px " + Math.max(2, Math.round(10 * scale)) + "px 0px " + Math.max(2, Math.round(6 * scale)) + "px";
                    overlay.style.lineHeight = (nextH - 3 * scale) + "px";
                } else if (isPolaresNode) {
                    overlay.style.borderRadius = "5px";
                    overlay.style.padding = "0px " + Math.max(2, Math.round(6 * scale)) + "px 0px " + Math.max(4, Math.round(8 * scale)) + "px";
                    overlay.style.lineHeight = (nextH - 3 * scale) + "px";
                    overlay.scrollLeft = 0;
                } else {
                    overlay.style.borderRadius = lCount === 1 ? "13px" : "8px";
                    overlay.style.padding = lCount === 1 ? "3px 10px 0 10px" : "4px 10px";
                    overlay.style.lineHeight = lCount === 1 ? (Math.max(16, (widgetH - 6) / scale) + "px") : "18px";
                }
                overlay.style.whiteSpace = lCount === 1 ? "nowrap" : "pre-wrap";

                if (this.setDirtyCanvas) {
                    this.setDirtyCanvas(true, true);
                }
                if (this.draw) {
                    this.draw(true, true);
                }
            };

            overlay.oninput = syncSizeAndNode;
            if (!isSalidaNode) {
                overlay.onkeyup = function() {
                    overlay.scrollLeft = 0;
                };
            }
            
            setTimeout(() => {
                overlay.focus();
                const len = overlay.value ? overlay.value.length : 0;
                if (typeof overlay.setSelectionRange === "function") {
                    overlay.setSelectionRange(len, len);
                }
                overlay.scrollLeft = 0;
            }, 10);

            let submitted = false;

            const finish = (save) => {
                if (submitted) return;
                submitted = true;
                overlay.style.display = "none";
                overlay.onkeydown = null;
                overlay.onblur = null;
                overlay.oninput = null;
                overlay._finish = null;
                currentPromptFinish = null;

                if (save) {
                    let newVal = overlay.value;
                    if (!isMultilineNode) {
                        newVal = newVal.replace(/[\r\n]+/g, " ");
                    }
                    if (widget) {
                        widget.value = newVal;
                        if (widget.property && node && node.properties) {
                            node.properties[widget.property] = newVal;
                        }
                    }
                    if (typeof callback === "function") {
                        callback(newVal);
                    }
                    if (node && node.computeSize) {
                        node.size = node.computeSize();
                    }
                    if (this.setDirtyCanvas) {
                        this.setDirtyCanvas(true, true);
                    }
                    if (window.PyxisUndoManager) {
                        window.PyxisUndoManager.recordState("inline-prompt");
                    }
                }
            };
            currentPromptFinish = finish;
            overlay._finish = finish;

            const isMultilineNode = multiline || (widget && (widget.type === "textarea" || (widget.options && widget.options.multiline))) || (node && (node.title === "Define Vars" || (node.type && (node.type.includes("Define Vars") || node.type.includes("Script") || node.type.includes("Código")))));

            overlay.onkeydown = function(e) {
                if (e.key === "Enter") {
                    if (!isMultilineNode) {
                        e.preventDefault();
                        finish(true);
                    } else if (!e.shiftKey) {
                        e.preventDefault();
                        finish(true);
                    }
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    finish(false);
                }
            };

            overlay.onblur = function() {
                finish(true);
            };
        };

        function _pyxisCubicBezier(p1x, p1y, p2x, p2y) {
            const cx = 3 * p1x;
            const bx = 3 * (p2x - p1x) - cx;
            const ax = 1 - cx - bx;
            const cy = 3 * p1y;
            const by = 3 * (p2y - p1y) - cy;
            const ay = 1 - cy - by;

            function sampleX(t) { return ((ax * t + bx) * t + cx) * t; }
            function sampleY(t) { return ((ay * t + by) * t + cy) * t; }
            function sampleDerivX(t) { return (3 * ax * t + 2 * bx) * t + cx; }

            return function(x) {
                if (x <= 0) return 0;
                if (x >= 1) return 1;
                let t = x;
                for (let i = 0; i < 8; i++) {
                    const x2 = sampleX(t) - x;
                    if (Math.abs(x2) < 1e-5) return sampleY(t);
                    const d2 = sampleDerivX(t);
                    if (Math.abs(d2) < 1e-5) break;
                    t = t - x2 / d2;
                }
                return sampleY(t);
            };
        }

        const _pyxisEaseCamera = _pyxisCubicBezier(0.16, 1, 0.3, 1);
        let _pyxis_pan_anim_id = null;

        function smoothPanAndZoomTo(targetX, targetY, targetScale = null, duration = 800) {
            if (_pyxis_pan_anim_id) {
                cancelAnimationFrame(_pyxis_pan_anim_id);
                _pyxis_pan_anim_id = null;
            }

            if (!canvas || !canvas.ds || !canvas.ds.offset) return;

            const startX = canvas.ds.offset[0];
            const startY = canvas.ds.offset[1];
            const startScale = canvas.ds.scale || 1.0;
            const endScale = (targetScale != null && targetScale > 0) ? targetScale : startScale;

            const dx = targetX - startX;
            const dy = targetY - startY;
            const dScale = endScale - startScale;

            if (Math.hypot(dx, dy) < 2 && Math.abs(dScale) < 0.005) {
                canvas.ds.offset[0] = targetX;
                canvas.ds.offset[1] = targetY;
                if (targetScale != null) canvas.ds.scale = endScale;
                canvas.setDirty(true, true);
                return;
            }

            const startTime = performance.now();

            function step(now) {
                const elapsed = now - startTime;
                const progress = Math.min(1.0, elapsed / duration);
                const factor = _pyxisEaseCamera(progress);

                canvas.ds.offset[0] = startX + dx * factor;
                canvas.ds.offset[1] = startY + dy * factor;
                if (Math.abs(dScale) > 0.0001) {
                    canvas.ds.scale = startScale + dScale * factor;
                }
                canvas.setDirty(true, true);

                if (progress < 1.0) {
                    _pyxis_pan_anim_id = requestAnimationFrame(step);
                } else {
                    canvas.ds.offset[0] = targetX;
                    canvas.ds.offset[1] = targetY;
                    if (targetScale != null) canvas.ds.scale = endScale;
                    canvas.setDirty(true, true);
                    _pyxis_pan_anim_id = null;
                }
            }

            _pyxis_pan_anim_id = requestAnimationFrame(step);
        }

        function resetView(animated = true) {
            if (typeof closeAllActiveNodeEditors === "function") closeAllActiveNodeEditors(true);
            if (!canvas || !canvas.canvas) return;
            canvas.resize();
            const w = (canvas.canvas.offsetWidth > 0) ? canvas.canvas.offsetWidth : (canvas.canvas.width > 0 ? canvas.canvas.width : 1280);
            const h = (canvas.canvas.offsetHeight > 0) ? canvas.canvas.offsetHeight : (canvas.canvas.height > 0 ? canvas.canvas.height : 720);
            
            let targetOffset = [0, 0];
            const targetScale = 1.0;

            if (graph._nodes && graph._nodes.length > 0) {
                let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                for (let i = 0; i < graph._nodes.length; ++i) {
                    let n = graph._nodes[i];
                    let sz = normalizeSize(n.size, 200, 100);
                    let nw = sz[0];
                    let nh = sz[1];
                    if (!n.pos || !Array.isArray(n.pos) || isNaN(n.pos[0]) || isNaN(n.pos[1])) {
                        n.pos = [200 + i * 250, 250];
                    }
                    if (n.pos[0] < minX) minX = n.pos[0];
                    if (n.pos[1] < minY) minY = n.pos[1];
                    if (n.pos[0] + nw > maxX) maxX = n.pos[0] + nw;
                    if (n.pos[1] + nh > maxY) maxY = n.pos[1] + nh;
                }
                let centerX = (minX + maxX) / 2;
                let centerY = (minY + maxY) / 2;
                targetOffset = [ Math.round((w / 2) - centerX), Math.round((h / 2) - centerY) ];
            }

            if (animated && typeof smoothPanAndZoomTo === "function") {
                smoothPanAndZoomTo(targetOffset[0], targetOffset[1], targetScale, 800);
            } else {
                canvas.ds.scale = targetScale;
                canvas.ds.offset = targetOffset;
                canvas.setDirty(true, true);
            }
        }

        function restoreGraphView(graphExtra) {
            if (!graphExtra) return false;
            if (typeof _pyxis_pan_anim_id !== "undefined" && _pyxis_pan_anim_id) {
                cancelAnimationFrame(_pyxis_pan_anim_id);
                _pyxis_pan_anim_id = null;
            }
            const zoom = (typeof graphExtra.canvas_zoom === "number") ? graphExtra.canvas_zoom : ((typeof graphExtra.zoom === "number") ? graphExtra.zoom : null);
            const offset = Array.isArray(graphExtra.canvas_offset) ? graphExtra.canvas_offset : (Array.isArray(graphExtra.offset) ? graphExtra.offset : null);
            if (zoom != null && zoom > 0 && offset && offset.length >= 2 && !isNaN(offset[0]) && !isNaN(offset[1])) {
                if (typeof closeAllActiveNodeEditors === "function") closeAllActiveNodeEditors(true);
                const activeCanvas = window.canvas || (typeof canvas !== "undefined" ? canvas : null);
                if (activeCanvas && activeCanvas.ds) {
                    if (typeof activeCanvas.resize === "function") activeCanvas.resize();
                    activeCanvas.ds.scale = zoom;
                    activeCanvas.ds.offset = new Float32Array([Number(offset[0]), Number(offset[1])]);
                    activeCanvas.setDirty(true, true);
                    if (typeof activeCanvas.draw === "function") activeCanvas.draw(true, true);
                    return true;
                }
            }
            return false;
        }
        window.restoreGraphView = restoreGraphView;

        function zoomIn() {
            if (typeof closeAllActiveNodeEditors === "function") closeAllActiveNodeEditors(true);
            canvas.setZoom(canvas.ds.scale * 1.2, [canvas.canvas.width / 2, canvas.canvas.height / 2]);
            if (typeof window.__pyxis_schedule_save === "function") window.__pyxis_schedule_save(100);
        }
        function zoomOut() {
            if (typeof closeAllActiveNodeEditors === "function") closeAllActiveNodeEditors(true);
            canvas.setZoom(canvas.ds.scale * 0.8, [canvas.canvas.width / 2, canvas.canvas.height / 2]);
            if (typeof window.__pyxis_schedule_save === "function") window.__pyxis_schedule_save(100);
        }

        function fitGraphView() {
            if (typeof closeAllActiveNodeEditors === "function") closeAllActiveNodeEditors(true);
            resetView();
            if (typeof window.__pyxis_schedule_save === "function") window.__pyxis_schedule_save(100);
        }

        function toggleGridMode() {
            window.gridMode = (window.gridMode + 1) % 3;
            canvas.draw(true, true);
            canvas.setDirty(true, true);
            if (window.PyxisThemeManager && window.PyxisThemeManager.saveConfig) {
                window.PyxisThemeManager.saveConfig();
            }
        }

        window.addEventListener("wheel", function(e) {
            if (e.target && typeof e.target.closest === "function" && (
                e.target.closest('#pyxis-inline-vars-editor-container') ||
                e.target.closest('.ace_editor') ||
                e.target.closest('#pyxis-inline-text-editor') ||
                e.target.closest('#pyxis-help-window') ||
                e.target.closest('#pyxis-diagnostics-panel') ||
                e.target.closest('#pyxis-debug-console-overlay') ||
                e.target.closest('#pyxis-telemetry-overlay') ||
                e.target.closest('.pyxis-modal-overlay') ||
                e.target.closest('.pyxis-template-overlay') ||
                e.target.closest('.pyxis-settings-overlay') ||
                e.target.closest('.pyxis-theme-settings-overlay') ||
                e.target.closest('.pyxis-mesh-picker-overlay') ||
                e.target.closest('.litecontextmenu')
            )) {
                return;
            }
            if (typeof closeAllActiveNodeEditors === "function") {
                closeAllActiveNodeEditors(true);
            }
            if (typeof window.__pyxis_schedule_save === "function") {
                window.__pyxis_schedule_save(200);
            }
        }, { passive: true });

        let videoTileLoopActive = false;
        let videoTileCallbackId = null;

        function stopVideoTileLoop() {
            videoTileLoopActive = false;
            const videoEl = document.getElementById("canvas_bg_video");
            if (videoEl && typeof videoEl.cancelVideoFrameCallback === "function" && videoTileCallbackId !== null) {
                try { videoEl.cancelVideoFrameCallback(videoTileCallbackId); } catch(e) {}
            }
            videoTileCallbackId = null;
        }

        function startVideoTileLoop() {
            if (videoTileLoopActive) return;
            videoTileLoopActive = true;
            const videoEl = document.getElementById("canvas_bg_video");
            const tileCanvas = document.getElementById("canvas_bg_video_tile");
            if (!videoEl || !tileCanvas) return;
            const ctx = tileCanvas.getContext("2d");

            function onFrame() {
                if (!videoTileLoopActive) return;
                const bgSettings = window.backgroundImageSettings || {};
                if (!bgSettings.hasBg || bgSettings.mode !== "tile") {
                    videoTileLoopActive = false;
                    return;
                }
                const cw = tileCanvas.clientWidth || window.innerWidth;
                const ch = tileCanvas.clientHeight || window.innerHeight;
                if (tileCanvas.width !== cw || tileCanvas.height !== ch) {
                    tileCanvas.width = cw;
                    tileCanvas.height = ch;
                }
                if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
                    ctx.clearRect(0, 0, tileCanvas.width, tileCanvas.height);
                    try {
                        const pattern = ctx.createPattern(videoEl, "repeat");
                        if (pattern) {
                            ctx.fillStyle = pattern;
                            ctx.fillRect(0, 0, tileCanvas.width, tileCanvas.height);
                        }
                    } catch(e) {}
                }
                if (typeof videoEl.requestVideoFrameCallback === "function") {
                    videoTileCallbackId = videoEl.requestVideoFrameCallback(onFrame);
                } else {
                    videoTileCallbackId = requestAnimationFrame(onFrame);
                }
            }

            if (typeof videoEl.requestVideoFrameCallback === "function") {
                videoTileCallbackId = videoEl.requestVideoFrameCallback(onFrame);
            } else {
                videoTileCallbackId = requestAnimationFrame(onFrame);
            }
        }

        window.updateBgMediaElement = function() {
            const videoEl = document.getElementById("canvas_bg_video");
            const tileCanvas = document.getElementById("canvas_bg_video_tile");
            if (!videoEl) return;
            const bgSettings = window.backgroundImageSettings || {};
            const isVideoBg = bgSettings.hasBg && (bgSettings.mediaType === "video" || bgSettings.videoUrl);
            if (isVideoBg && bgSettings.videoUrl) {
                const vUrl = bgSettings.videoUrl;
                videoEl.muted = true;
                videoEl.loop = true;
                videoEl.playsInline = true;
                videoEl.setAttribute("playsinline", "");
                videoEl.setAttribute("muted", "");
                videoEl.setAttribute("loop", "");
                if (bgSettings.posterUrl) {
                    videoEl.poster = bgSettings.posterUrl;
                }

                const activeTheme = (window.PyxisThemeManager && typeof window.PyxisThemeManager.getCurrentTheme === "function" && window.PyxisThemeManager.getCurrentTheme()) || "teal";
                const allThemes = (window.PyxisThemeManager && typeof window.PyxisThemeManager.getAllThemes === "function" && window.PyxisThemeManager.getAllThemes()) || {};
                const themeData = allThemes[activeTheme] || (window.PyxisThemeManager && window.PyxisThemeManager.THEMES && window.PyxisThemeManager.THEMES[activeTheme]) || {};
                const themeBg = themeData.canvasBg || "#081116";

                videoEl.style.backgroundColor = themeBg;
                if (tileCanvas) tileCanvas.style.backgroundColor = themeBg;

                const mode = bgSettings.mode || "contain";
                const opacity = (bgSettings.opacity !== undefined ? bgSettings.opacity : 0.85);

                if (mode === "tile") {
                    videoEl.style.display = "none";
                    if (tileCanvas) {
                        tileCanvas.style.display = "block";
                        tileCanvas.style.opacity = opacity;
                    }
                    startVideoTileLoop();
                } else {
                    stopVideoTileLoop();
                    if (tileCanvas) tileCanvas.style.display = "none";
                    videoEl.style.display = "block";
                    videoEl.style.opacity = opacity;

                    if (mode === "cover") {
                        videoEl.style.objectFit = "cover";
                        videoEl.style.objectPosition = "center";
                    } else if (mode === "stretch") {
                        videoEl.style.objectFit = "fill";
                        videoEl.style.objectPosition = "center";
                    } else if (mode === "center") {
                        videoEl.style.objectFit = "none";
                        videoEl.style.objectPosition = "center";
                    } else {
                        videoEl.style.objectFit = "contain";
                        videoEl.style.objectPosition = "center";
                    }
                }

                if (videoEl.src !== vUrl) {
                    videoEl.src = vUrl;
                    videoEl.load();
                }
                const playPromise = videoEl.play();
                if (playPromise !== undefined) {
                    playPromise.catch(e => {
                        console.log("Pyxis background video autoplay handled:", e);
                    });
                }
            } else {
                stopVideoTileLoop();
                if (tileCanvas) tileCanvas.style.display = "none";
                videoEl.style.display = "none";
                videoEl.pause();
                videoEl.removeAttribute("src");
                videoEl.load();
            }
        };

        document.addEventListener("visibilitychange", function() {
            const videoEl = document.getElementById("canvas_bg_video");
            if (videoEl) {
                if (document.hidden) {
                    videoEl.pause();
                    stopVideoTileLoop();
                } else if (window.backgroundImageSettings && (window.backgroundImageSettings.mediaType === "video" || window.backgroundImageSettings.videoUrl)) {
                    videoEl.play().then(() => {
                        if (window.backgroundImageSettings && window.backgroundImageSettings.mode === "tile") {
                            startVideoTileLoop();
                        }
                    }).catch(e => console.log("Video resume on visible:", e));
                }
            }
        });

        window.addEventListener("resize", function() {
            const tileCanvas = document.getElementById("canvas_bg_video_tile");
            if (tileCanvas && tileCanvas.style.display !== "none") {
                tileCanvas.width = tileCanvas.clientWidth || window.innerWidth;
                tileCanvas.height = tileCanvas.clientHeight || window.innerHeight;
            }
        });

        canvas.onRenderBackground = function(html_canvas, ctx) {
            try {
                ctx.save();
                const activeTheme = (window.PyxisThemeManager && typeof window.PyxisThemeManager.getCurrentTheme === "function" && window.PyxisThemeManager.getCurrentTheme()) || "teal";
                const allThemes = (window.PyxisThemeManager && typeof window.PyxisThemeManager.getAllThemes === "function" && window.PyxisThemeManager.getAllThemes()) || {};
                const themeData = allThemes[activeTheme] || (window.PyxisThemeManager && window.PyxisThemeManager.THEMES && window.PyxisThemeManager.THEMES[activeTheme]) || {};
                const themeBg = themeData.canvasBg || "#081116";

                const bgSettings = window.backgroundImageSettings || {};
                const isVideoBg = bgSettings.hasBg && (bgSettings.mediaType === "video" || bgSettings.videoUrl);

                if (isVideoBg) {
                    ctx.clearRect(0, 0, html_canvas.width, html_canvas.height);
                } else {
                    ctx.fillStyle = themeBg;
                    ctx.fillRect(0, 0, html_canvas.width, html_canvas.height);

                    if (bgSettings.dataUrl) {
                        const dataUrl = bgSettings.dataUrl;
                        if (!bgImageElement || bgImageElement.src !== dataUrl) {
                            bgImageElement = new Image();
                            bgImageElement.onload = function() {
                                if (canvas) { canvas.setDirty(true, true); canvas.draw(true, true); }
                            };
                            bgImageElement.src = dataUrl;
                        }
                        if (bgImageElement.complete && bgImageElement.naturalWidth > 0) {
                            ctx.globalAlpha = Math.min(1.0, Math.max(0.0, bgSettings.opacity));
                            
                            const w = html_canvas.width;
                            const h = html_canvas.height;
                            const imgW = bgImageElement.naturalWidth;
                            const imgH = bgImageElement.naturalHeight;
                            const mode = bgSettings.mode || "contain";

                            if (mode === "stretch") {
                                ctx.drawImage(bgImageElement, 0, 0, w, h);
                            } else if (mode === "center") {
                                ctx.drawImage(bgImageElement, (w - imgW) / 2, (h - imgH) / 2, imgW, imgH);
                            } else if (mode === "tile") {
                                const pattern = ctx.createPattern(bgImageElement, "repeat");
                                if (pattern) {
                                    ctx.fillStyle = pattern;
                                    ctx.fillRect(0, 0, w, h);
                                }
                            } else if (mode === "contain" || mode === "cover") {
                                const scaleX = w / imgW;
                                const scaleY = h / imgH;
                                const scale = (mode === "contain") ? Math.min(scaleX, scaleY) : Math.max(scaleX, scaleY);
                                const drawW = imgW * scale;
                                const drawH = imgH * scale;
                                ctx.drawImage(bgImageElement, (w - drawW) / 2, (h - drawH) / 2, drawW, drawH);
                            }
                        }
                    }
                }
            } catch (err) {
                console.error("Pyxis BG Render Error:", err);
            } finally {
                ctx.globalAlpha = 1.0;
                ctx.restore();
                ctx.globalAlpha = 1.0;
            }
            return true;
        };

        canvas.onDrawBackground = function(ctx, visible_area) {
            try {
                if (window.gridMode === 2) return;

                const step = 20;
                const majorStep = 100;
                const startX = Math.floor(visible_area[0] / step) * step;
                const endX = Math.ceil((visible_area[0] + visible_area[2]) / step) * step;
                const startY = Math.floor(visible_area[1] / step) * step;
                const endY = Math.ceil((visible_area[1] + visible_area[3]) / step) * step;

                if (window.gridMode === 0) {
                    ctx.lineWidth = 1;
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
                    ctx.beginPath();
                    for (let x = startX; x <= endX; x += step) {
                        if (x % majorStep !== 0) {
                            ctx.moveTo(x, startY); ctx.lineTo(x, endY);
                        }
                    }
                    for (let y = startY; y <= endY; y += step) {
                        if (y % majorStep !== 0) {
                            ctx.moveTo(startX, y); ctx.lineTo(endX, y);
                        }
                    }
                    ctx.stroke();

                    ctx.strokeStyle = "rgba(255, 255, 255, 0.09)";
                    ctx.beginPath();
                    for (let x = startX; x <= endX; x += step) {
                        if (x % majorStep === 0) {
                            ctx.moveTo(x, startY); ctx.lineTo(x, endY);
                        }
                    }
                    for (let y = startY; y <= endY; y += step) {
                        if (y % majorStep === 0) {
                            ctx.moveTo(startX, y); ctx.lineTo(endX, y);
                        }
                    }
                    ctx.stroke();
                } else if (window.gridMode === 1) {
                    ctx.fillStyle = "rgba(255, 255, 255, 0.18)";
                    for (let x = startX; x <= endX; x += step) {
                        for (let y = startY; y <= endY; y += step) {
                            ctx.fillRect(x - 0.75, y - 0.75, 1.5, 1.5);
                        }
                    }
                }
            } catch (err) {
                console.error("Pyxis Grid Draw Error:", err);
            }
        };

        function _drawRoundRectPath(ctx, x, y, w, h, r) {
            if (typeof ctx.roundRect === "function") {
                ctx.roundRect(x, y, w, h, [r]);
            } else {
                ctx.moveTo(x + r, y);
                ctx.arcTo(x + w, y, x + w, y + h, r);
                ctx.arcTo(x + w, y + h, x, y + h, r);
                ctx.arcTo(x, y + h, x, y, r);
                ctx.arcTo(x, y + w, y, r);
                ctx.closePath();
            }
        }

        function _drawProfessionalNodeGlow(ctx, node, now, roundRadius) {
            const remaining = node._pyxis_glow_until - now;
            if (remaining <= 0) return;

            const fade = Math.min(1.0, remaining / 600);
            const pulse = 0.78 + 0.22 * Math.sin(now / 140);
            const alpha = fade * pulse;

            const title_mode = node.constructor.title_mode;
            const render_title = !(title_mode === LiteGraph.TRANSPARENT_TITLE || title_mode === LiteGraph.NO_TITLE);
            const title_height = LiteGraph.NODE_TITLE_HEIGHT || 30;

            const is_collapsed = !!(node.flags && node.flags.collapsed);
            const nx = node.pos[0];
            const ny = render_title ? (node.pos[1] - title_height) : node.pos[1];
            const nw = (is_collapsed ? (node._collapsed_width || node.size[0]) : node.size[0]) + 1;
            const nh = render_title ? (is_collapsed ? title_height : (node.size[1] + title_height)) : node.size[1];
            const rad = roundRadius || 10;

            const isCrit = (node._pyxis_glow_severity === "critical" || node._pyxis_glow_color === "#ef4444");
            const baseColor = isCrit ? "#ef4444" : "#f59e0b";
            const highlightColor = isCrit ? "#fca5a5" : "#fef08a";
            const bloomRgba = isCrit ? "rgba(239, 68, 68," : "rgba(245, 158, 11,";

            ctx.save();

            // Pass 1: Broad atmospheric soft bloom
            ctx.shadowColor = baseColor;
            ctx.shadowBlur = 36;
            ctx.fillStyle = bloomRgba + (0.55 * alpha) + ")";
            ctx.beginPath();
            _drawRoundRectPath(ctx, nx - 4, ny - 4, nw + 8, nh + 8, rad + 4);
            ctx.fill();

            // Pass 2: High-density vibrant mid-aura
            ctx.shadowColor = baseColor;
            ctx.shadowBlur = 20;
            ctx.fillStyle = bloomRgba + (0.85 * alpha) + ")";
            ctx.beginPath();
            _drawRoundRectPath(ctx, nx - 2, ny - 2, nw + 4, nh + 4, rad + 2);
            ctx.fill();

            // Pass 3: Concentrated high-luminance corona right behind border
            ctx.shadowColor = highlightColor;
            ctx.shadowBlur = 12;
            ctx.lineWidth = 6;
            ctx.strokeStyle = bloomRgba + (0.95 * alpha) + ")";
            ctx.beginPath();
            _drawRoundRectPath(ctx, nx - 1, ny - 1, nw + 2, nh + 2, rad + 1);
            ctx.stroke();

            // Pass 4: Crisp radiant rim underneath node perimeter
            ctx.shadowBlur = 4;
            ctx.lineWidth = 2.5;
            ctx.strokeStyle = isCrit 
                ? ("rgba(254, 202, 202, " + (0.95 * alpha) + ")")
                : ("rgba(254, 240, 138, " + (0.95 * alpha) + ")");
            ctx.beginPath();
            _drawRoundRectPath(ctx, nx, ny, nw, nh, rad);
            ctx.stroke();

            ctx.restore();
        }

        const _origDrawNode = canvas.drawNode;
        canvas.drawNode = function(node, ctx) {
            // Render active glows ONCE per frame before any visible node is drawn,
            // placing the glow completely UNDER every node and embracing the full title bar.
            if (this._pyxis_last_glow_frame !== this.frame) {
                this._pyxis_last_glow_frame = this.frame;
                const now = Date.now();
                if (graph && graph._nodes) {
                    let hasActiveGlow = false;
                    for (let i = 0; i < graph._nodes.length; i++) {
                        const n = graph._nodes[i];
                        if (n._pyxis_glow_until && n._pyxis_glow_until > now) {
                            hasActiveGlow = true;
                            break;
                        }
                    }

                    if (hasActiveGlow) {
                        ctx.save();
                        // ctx in drawNode is already translated to node.pos; translate back to graph space
                        ctx.translate(-node.pos[0], -node.pos[1]);

                        for (let i = 0; i < graph._nodes.length; i++) {
                            const n = graph._nodes[i];
                            if (n._pyxis_glow_until && n._pyxis_glow_until > now) {
                                _drawProfessionalNodeGlow(ctx, n, now, this.round_radius || 8);
                            }
                        }

                        ctx.restore();

                        // Keep animation ticking smoothly while glowing
                        requestAnimationFrame(() => {
                            if (canvas) canvas.setDirty(true, false);
                        });
                    }
                }
            }

            return _origDrawNode.apply(this, arguments);
        };

        let isGenerating = false;
        let cancelRequested = false;
        let currentP = 0;
        let targetP = 0;
        let generatedLinesCount = 0;
        let currentProgressPhase = "";
        let currentProgressSpeed = 0;
        let _lastEstimationData = null;

        function showWorkloadEstimation() {
            if (isGenerating) return;
            const tooltip = document.getElementById("pyxis-estimation-tooltip");
            if (!tooltip) return;
            tooltip.style.display = "block";
            requestAnimationFrame(() => {
                tooltip.style.opacity = "1";
                tooltip.style.transform = "translateY(0)";
            });

            syncWidgetsToProperties();
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.estimate_workload_api === 'function') {
                window.pywebview.api.estimate_workload_api(graph.serialize()).then(data => {
                    if (!data) return;
                    _lastEstimationData = data;
                    updateEstimationUI(data);
                }).catch(e => {
                    console.warn("Error calculando estimación:", e);
                });
            }
        }

        function hideWorkloadEstimation() {
            const tooltip = document.getElementById("pyxis-estimation-tooltip");
            if (tooltip) {
                tooltip.style.opacity = "0";
                tooltip.style.transform = "translateY(-4px)";
                setTimeout(() => {
                    if (tooltip.style.opacity === "0") tooltip.style.display = "none";
                }, 150);
            }
        }

        function updateEstimationUI(data) {
            const linesVal = document.getElementById("est-lines-val");
            const inputsVal = document.getElementById("est-inputs-val");
            const unitsVal = document.getElementById("est-units-val");
            const peakSimVal = document.getElementById("est-peak-sim-val");
            const expRatioVal = document.getElementById("est-exp-ratio-val");
            const weightVal = document.getElementById("est-weight-val");
            const lastTelItem = document.getElementById("est-last-tel-item");
            const lastTelVal = document.getElementById("est-last-tel-val");
            const pillsRow = document.getElementById("est-profile-pills");
            const badge = document.getElementById("est-complexity-badge");
            const alertBox = document.getElementById("est-alert-msg");

            const unitLin = window.t ? window.t("estimation.unit_lines") : "lines";
            const unitU = window.t ? window.t("estimation.unit_units") : "u";

            if (linesVal) linesVal.innerText = (data.estimated_lines || 0).toLocaleString() + " " + unitLin;
            if (inputsVal) inputsVal.innerText = (data.input_lines || 0) + " " + unitLin;
            if (unitsVal) unitsVal.innerText = (data.base_units || 0) + " " + unitU;
            if (peakSimVal) {
                const pSim = Number(data.peak_simultaneous_lines || 0);
                peakSimVal.innerText = pSim.toLocaleString() + " " + unitLin;
                peakSimVal.style.color = pSim > 600 ? "#f43f5e" : (pSim > 220 ? "#fbbf24" : "#f8fafc");
            }
            if (expRatioVal) {
                const ratio = Number(data.expansion_ratio || 0);
                expRatioVal.innerText = ratio.toFixed(1) + "x";
            }
            if (weightVal) {
                const kb = Number(data.estimated_size_kb || 0);
                weightVal.innerText = kb >= 1024 ? (kb / 1024.0).toFixed(2) + " MB" : kb.toFixed(1) + " KB";
            }
            if (lastTelItem && lastTelVal) {
                const telMs = Number(data.last_telemetry_peak_ms || 0);
                const telPct = Number(data.last_telemetry_budget_pct || 0);
                if (telMs > 0) {
                    lastTelItem.style.display = "flex";
                    lastTelVal.innerText = `${telMs.toFixed(1)} ms (${telPct.toFixed(0)}%)`;
                    lastTelVal.style.color = telPct > 100 ? "#f43f5e" : (telPct > 75 ? "#fbbf24" : "#34d399");
                } else {
                    lastTelItem.style.display = "none";
                }
            }
            if (pillsRow) {
                const pills = [];
                if (data.has_fbf) {
                    pills.push(`<span class="est-profile-pill" style="border-color:var(--border-highlight);color:var(--doc-accent-bright);"><svg viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="8" y1="4" x2="8" y2="20"/><line x1="16" y1="4" x2="16" y2="20"/></svg>FBF</span>`);
                }
                if (data.has_slicer) {
                    pills.push(`<span class="est-profile-pill" style="border-color:rgba(168,85,247,0.45);color:#c084fc;"><svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>SLICER</span>`);
                }
                if (data.has_particles) {
                    pills.push(`<span class="est-profile-pill" style="border-color:rgba(244,63,94,0.45);color:#fb7185;"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><circle cx="5" cy="6" r="1.5"/><circle cx="19" cy="7" r="1.5"/><circle cx="6" cy="18" r="1.5"/><circle cx="18" cy="17" r="1.5"/></svg>PARTICLES</span>`);
                }
                if (data.has_audio) {
                    pills.push(`<span class="est-profile-pill" style="border-color:rgba(16,185,129,0.45);color:#34d399;"><svg viewBox="0 0 24 24"><line x1="4" y1="10" x2="4" y2="14"/><line x1="8" y1="6" x2="8" y2="18"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="16" y1="7" x2="16" y2="17"/><line x1="20" y1="10" x2="20" y2="14"/></svg>AUDIO</span>`);
                }
                if (data.has_script) {
                    pills.push(`<span class="est-profile-pill" style="border-color:rgba(245,158,11,0.45);color:#fbbf24;"><svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>SCRIPT</span>`);
                }
                if (pills.length > 0) {
                    pillsRow.innerHTML = pills.join("");
                    pillsRow.style.display = "flex";
                } else {
                    pillsRow.innerHTML = "";
                    pillsRow.style.display = "none";
                }
            }
            if (badge) {
                let badgeText = data.complexity || "Normal";
                const compStr = String(data.complexity_key || data.complexity || "").toLowerCase();
                if (window.t) {
                    if (compStr === "baja" || compStr === "low") {
                        badgeText = window.t("estimation.complexity_low");
                    } else if (compStr === "normal" || compStr === "media" || compStr === "medium" || compStr === "med") {
                        badgeText = window.t("estimation.complexity_normal");
                    } else if (compStr === "alta" || compStr === "high") {
                        badgeText = window.t("estimation.complexity_high");
                    } else if (compStr === "extrema" || compStr === "extreme") {
                        badgeText = window.t("estimation.complexity_extreme");
                    }
                }
                badge.innerText = badgeText;
                badge.style.color = data.complexity_color || "#60a5fa";
                badge.style.borderColor = (data.complexity_color || "#60a5fa") + "66";
                badge.style.background = (data.complexity_color || "#60a5fa") + "22";
            }
            if (alertBox) {
                alertBox.style.display = data.is_heavy ? "block" : "none";
                if (window.t) {
                    alertBox.innerText = window.t("estimation.heavy_alert");
                }
            }
        }

        window.addEventListener("pyxis:languageChanged", () => {
            if (_lastEstimationData) {
                updateEstimationUI(_lastEstimationData);
            }
            const codeModal = document.getElementById("pyxis-code-editor-modal");
            if (codeModal && codeModal.style.display !== "none") {
                refreshCodeTemplatesDropdown();
            }
        });

        let isHoveringGenerateBtn = false;

        function onGenerateBtnHover(hovering) {
            isHoveringGenerateBtn = hovering;
            if (!isGenerating) return;
            const label = document.getElementById("btn-generate-label");
            if (hovering) {
                if (label && !cancelRequested) label.innerText = window.t ? window.t("topbar.stop") : "Stop";
            }
        }

        window.__pyxis_on_progress = function (data) {
            if (typeof data === "number") {
                const numP = Math.min(100, Math.max(0, Math.floor(data)));
                targetP = Math.max(targetP, numP);
            } else if (typeof data === "object" && data !== null) {
                const pVal = (data.percent !== undefined) ? data.percent : (data.pct || 0);
                const numP = Math.min(100, Math.max(0, Math.floor(pVal)));
                targetP = Math.max(targetP, numP);
                if (data.lines_generated !== undefined) {
                    generatedLinesCount = Math.max(generatedLinesCount, data.lines_generated);
                }
                if (data.phase) {
                    currentProgressPhase = data.phase;
                }
                if (data.speed) {
                    currentProgressSpeed = data.speed;
                }
            }
        };

        let activeDiagnosticIssues = [];

        function _escapeDiag(str) {
            if (str == null) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        let lastFocusedDiagnosticNodeId = null;
        let lastFocusedDiagnosticSeverity = null;

        function focusAndGlowNode(nodeId, severity, durationMs = 5000) {
            if (!graph || nodeId == null) return;
            const node = graph.getNodeById(nodeId);
            if (!node || !canvas) return;

            lastFocusedDiagnosticNodeId = nodeId;
            lastFocusedDiagnosticSeverity = severity;

            canvas.deselectAllNodes();
            canvas.selectNode(node);

            // Compute available unobstructed canvas width (excluding the diagnostics panel if active)
            const panel = document.getElementById("pyxis-diagnostics-panel");
            const panelWidth = (panel && panel.classList.contains("is-active")) 
                ? panel.getBoundingClientRect().width 
                : 0;

            const visibleWidth = Math.max(100, canvas.canvas.width - panelWidth);
            const targetCenterX = visibleWidth / 2;
            const targetCenterY = canvas.canvas.height / 2;
            const title_mode = node.constructor.title_mode;
            const render_title = !(title_mode === LiteGraph.TRANSPARENT_TITLE || title_mode === LiteGraph.NO_TITLE);
            const title_height = LiteGraph.NODE_TITLE_HEIGHT || 30;
            const is_collapsed = !!(node.flags && node.flags.collapsed);
            const totalH = render_title ? (is_collapsed ? title_height : (node.size[1] + title_height)) : node.size[1];
            const topY = render_title ? (node.pos[1] - title_height) : node.pos[1];

            const nodeCenterX = node.pos[0] + (is_collapsed ? (node._collapsed_width || node.size[0]) : node.size[0]) / 2;
            const nodeCenterY = topY + totalH / 2;

            // Target scale: if currently at an extreme zoom, gently normalize to 1.0 for optimal readability
            const currentScale = (canvas.ds && canvas.ds.scale) ? canvas.ds.scale : 1.0;
            const targetScale = (currentScale < 0.65 || currentScale > 1.35) ? 1.0 : currentScale;

            const targetOffsetX = Math.round(targetCenterX / targetScale - nodeCenterX);
            const targetOffsetY = Math.round(targetCenterY / targetScale - nodeCenterY);

            smoothPanAndZoomTo(targetOffsetX, targetOffsetY, targetScale, 800);

            node._pyxis_glow_until = Date.now() + durationMs;
            node._pyxis_glow_color = (severity === "critical") ? "#ef4444" : "#f59e0b";
            node._pyxis_glow_severity = severity;
            canvas.setDirty(true, true);
        }

        function frameNodesOnCanvas(nodes, duration = 800, padding = 100) {
            if (!nodes || !nodes.length || !canvas || !canvas.canvas) return;

            canvas.resize();
            const w = (canvas.canvas.offsetWidth > 0) ? canvas.canvas.offsetWidth : (canvas.canvas.width > 0 ? canvas.canvas.width : 1280);
            const h = (canvas.canvas.offsetHeight > 0) ? canvas.canvas.offsetHeight : (canvas.canvas.height > 0 ? canvas.canvas.height : 720);

            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            const title_height = LiteGraph.NODE_TITLE_HEIGHT || 30;

            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                if (!node || !node.pos) continue;
                const title_mode = node.constructor.title_mode;
                const render_title = !(title_mode === LiteGraph.TRANSPARENT_TITLE || title_mode === LiteGraph.NO_TITLE);
                const is_collapsed = !!(node.flags && node.flags.collapsed);
                const nw = is_collapsed ? (node._collapsed_width || (node.size ? node.size[0] : 140)) : (node.size ? node.size[0] : 140);
                const nh = render_title ? (is_collapsed ? title_height : ((node.size ? node.size[1] : 60) + title_height)) : (node.size ? node.size[1] : 60);
                const topY = render_title ? (node.pos[1] - title_height) : node.pos[1];
                const leftX = node.pos[0];
                const rightX = leftX + nw;
                const bottomY = topY + nh;

                if (leftX < minX) minX = leftX;
                if (topY < minY) minY = topY;
                if (rightX > maxX) maxX = rightX;
                if (bottomY > maxY) maxY = bottomY;
            }

            if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) return;

            const bboxW = Math.max(50, maxX - minX);
            const bboxH = Math.max(50, maxY - minY);
            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;

            const padX = padding || 100;
            const padY = Math.round((padding || 100) * 0.9);
            const availW = Math.max(100, w - padX * 2);
            const availH = Math.max(100, h - padY * 2);

            let targetScale = Math.min(availW / bboxW, availH / bboxH);
            targetScale = Math.max(0.20, Math.min(1.0, targetScale));

            const targetCenterX = w / 2;
            const targetCenterY = h / 2;
            const targetOffsetX = Math.round(targetCenterX / targetScale - centerX);
            const targetOffsetY = Math.round(targetCenterY / targetScale - centerY);

            if (typeof smoothPanAndZoomTo === "function") {
                smoothPanAndZoomTo(targetOffsetX, targetOffsetY, targetScale, duration);
            } else {
                if (canvas.ds) {
                    canvas.ds.scale = targetScale;
                    canvas.ds.offset = [targetOffsetX, targetOffsetY];
                }
                canvas.setDirty(true, true);
            }
        }

        function showDiagnosticsModal(issues) {
            activeDiagnosticIssues = issues || [];
            const panel = document.getElementById("pyxis-diagnostics-panel");
            const listEl = document.getElementById("pyxis-diagnostics-items");
            const critBadge = document.getElementById("pyxis-diag-count-critical");
            const critText = document.getElementById("pyxis-diag-critical-text");
            const warnBadge = document.getElementById("pyxis-diag-count-warning");
            const warnText = document.getElementById("pyxis-diag-warning-text");

            if (!panel || !listEl) return;

            const criticalCount = activeDiagnosticIssues.filter(i => i.severity === "critical").length;
            const warningCount = activeDiagnosticIssues.filter(i => i.severity === "warning").length;

            if (critBadge && critText) {
                if (criticalCount > 0) {
                    critBadge.style.display = "inline-flex";
                    critText.innerText = window.t ? window.t("diagnostics.critical_count", { count: criticalCount }) : `${criticalCount} Critical Error(s)`;
                } else {
                    critBadge.style.display = "none";
                }
            }

            if (warnBadge && warnText) {
                if (warningCount > 0) {
                    warnBadge.style.display = "inline-flex";
                    warnText.innerText = window.t ? window.t("diagnostics.warning_count", { count: warningCount }) : `${warningCount} Warning(s)`;
                } else {
                    warnBadge.style.display = "none";
                }
            }

            listEl.innerHTML = "";
            activeDiagnosticIssues.forEach(issue => {
                const card = document.createElement("div");
                card.className = `pyxis-diagnostic-card ${issue.severity === "critical" ? "critical" : "warning"}`;
                card.onclick = () => {
                    if (issue.node_id != null) {
                        focusAndGlowNode(issue.node_id, issue.severity);
                    }
                };

                const isCrit = issue.severity === "critical";
                const sevBadgeText = isCrit 
                    ? (window.t ? window.t("diagnostics.badge_critical") : "Critical Conflict")
                    : (window.t ? window.t("diagnostics.badge_warning") : "Syntax Warning");
                
                const lineInfo = issue.line ? ` • ${(window.t ? window.t("diagnostics.line_label", { line: issue.line }) : "Line " + issue.line)}` : "";
                const locateLabel = window.t ? window.t("diagnostics.locate_node") : "Locate on canvas";
                const msgText = (window.t && issue.msg_key) ? window.t(issue.msg_key, issue.params, issue.error_msg) : (issue.error_msg || "");
                const sugText = (window.t && issue.sug_key) ? window.t(issue.sug_key, issue.params, issue.suggestion) : (issue.suggestion || "");

                card.innerHTML = `
                    <div class="pyxis-diagnostic-card-header">
                        <div class="pyxis-diagnostic-card-title-wrap">
                            <span class="${isCrit ? 'pyxis-badge-critical' : 'pyxis-badge-warning'}" style="padding: 2px 7px; font-size: 11px;">${sevBadgeText}</span>
                            <span class="pyxis-diagnostic-node-title">${_escapeDiag(issue.node_title || "Node")}${issue.node_id != null ? ' (ID: ' + issue.node_id + ')' : ''}</span>
                            <span class="pyxis-diagnostic-tag-badge">${_escapeDiag(issue.category || "General")}${_escapeDiag(issue.field ? ' / ' + issue.field : '')}${lineInfo}</span>
                        </div>
                    </div>
                    <div class="pyxis-diagnostic-msg">${_escapeDiag(msgText)}</div>
                    ${issue.code_snippet ? `<div class="pyxis-diagnostic-snippet">${_escapeDiag(issue.code_snippet)}</div>` : ''}
                    ${sugText ? `
                        <div class="pyxis-diagnostic-suggestion">
                            <svg class="svg-icon" viewBox="0 0 24 24" style="width:14px;height:14px;stroke:#38bdf8;fill:none;stroke-width:2;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                            <span>${_escapeDiag(sugText)}</span>
                        </div>
                    ` : ''}
                `;
                listEl.appendChild(card);
            });

            panel.classList.add("is-active");
            if (window.PyxisI18n && typeof window.PyxisI18n.updateDOM === "function") {
                window.PyxisI18n.updateDOM(panel);
            }

            // Immediately center and highlight the first problematic node in the unobstructed canvas area!
            const firstWithNode = activeDiagnosticIssues.find(i => i.node_id != null);
            if (firstWithNode) {
                lastFocusedDiagnosticNodeId = firstWithNode.node_id;
                lastFocusedDiagnosticSeverity = firstWithNode.severity;
                requestAnimationFrame(() => {
                    focusAndGlowNode(firstWithNode.node_id, firstWithNode.severity);
                });
            } else {
                lastFocusedDiagnosticNodeId = null;
                lastFocusedDiagnosticSeverity = null;
            }
        }

        function closeDiagnosticsModal(focusFirstNode = false) {
            const panel = document.getElementById("pyxis-diagnostics-panel");
            if (panel) panel.classList.remove("is-active");

            if (focusFirstNode && activeDiagnosticIssues && activeDiagnosticIssues.length > 0) {
                const now = Date.now();
                // Glow ALL nodes with problems for 2 seconds
                const nodeSeverityMap = new Map();
                activeDiagnosticIssues.forEach(issue => {
                    if (issue.node_id != null) {
                        const prevSev = nodeSeverityMap.get(issue.node_id);
                        if (!prevSev || issue.severity === "critical") {
                            nodeSeverityMap.set(issue.node_id, issue.severity);
                        }
                    }
                });

                const problematicNodes = [];
                nodeSeverityMap.forEach((sev, nid) => {
                    const n = graph ? graph.getNodeById(nid) : null;
                    if (n) {
                        n._pyxis_glow_until = now + 2000;
                        n._pyxis_glow_color = (sev === "critical") ? "#ef4444" : "#f59e0b";
                        n._pyxis_glow_severity = sev;
                        problematicNodes.push(n);
                    }
                });

                if (problematicNodes.length > 0) {
                    if (canvas && typeof canvas.selectNodes === "function") {
                        canvas.selectNodes(problematicNodes, false);
                    }
                    frameNodesOnCanvas(problematicNodes, 800, 100);
                } else {
                    const targetNodeId = lastFocusedDiagnosticNodeId != null 
                        ? lastFocusedDiagnosticNodeId 
                        : (activeDiagnosticIssues && activeDiagnosticIssues.find(i => i.node_id != null)?.node_id);
                    const targetSeverity = lastFocusedDiagnosticSeverity != null
                        ? lastFocusedDiagnosticSeverity
                        : (activeDiagnosticIssues && activeDiagnosticIssues.find(i => i.node_id != null)?.severity);
                    if (targetNodeId != null) {
                        focusAndGlowNode(targetNodeId, targetSeverity, 2000);
                    }
                }
                if (canvas) canvas.setDirty(true, true);
            }
        }

        function generateAnywayFromDiagnostics() {
            closeDiagnosticsModal(false);
            applyGraph();
        }

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                const diagPanel = document.getElementById("pyxis-diagnostics-panel");
                if (diagPanel && diagPanel.classList.contains("is-active")) {
                    closeDiagnosticsModal(true);
                }
            }
        });

        function handleGenerateClick() {
            if (isGenerating) {
                cancelRequested = true;
                const label = document.getElementById("btn-generate-label");
                if (label) label.innerText = window.t ? window.t("topbar.stopping") : "Stopping...";
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.cancel_generation === "function") {
                    window.pywebview.api.cancel_generation();
                }
                return;
            }

            syncWidgetsToProperties();

            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.validate_graph === "function") {
                window.pywebview.api.validate_graph(graph.serialize()).then(valRes => {
                    if (valRes && valRes.success && valRes.issues && valRes.issues.length > 0) {
                        showDiagnosticsModal(valRes.issues);
                    } else {
                        applyGraph();
                    }
                }).catch(err => {
                    console.warn("[Pyxis Linter] Validation check error, proceeding to apply graph:", err);
                    applyGraph();
                });
            } else {
                applyGraph();
            }
        }

                function formatProgressPhase(phaseText) {
            if (!phaseText) return "";
            const isEs = window.PyxisI18n && window.PyxisI18n.currentLang === "es";
            if (!isEs) return phaseText;
            if (phaseText.startsWith("Processing...")) return "Procesando...";
            if (phaseText.startsWith("Sorting ")) return phaseText.replace("Sorting ", "Ordenando ").replace(" deterministic layers...", " capas deterministas...");
            if (phaseText.startsWith("Assembling ASS text ")) return phaseText.replace("Assembling ASS text ", "Ensamblando texto ASS ").replace(" lines", " líneas");
            if (phaseText.startsWith("Completed. Transferring to Aegisub...")) return "Completado. Transfiriendo a Aegisub...";
            if (phaseText.startsWith("Generating...")) return phaseText.replace("Generating...", "Generando...").replace(" lines", " líneas");
            return phaseText;
        }

        function applyGraph() {
            hideWorkloadEstimation();
            syncWidgetsToProperties();
            const wrapper = document.querySelector(".btn-generate-wrapper");
            const btn = document.getElementById("btn-generate-main");
            const label = document.getElementById("btn-generate-label");
            const progressBar = document.getElementById("btn-progress-bar");

            isGenerating = true;
            cancelRequested = false;
            currentP = 1;
            targetP = 1;
            generatedLinesCount = 0;
            let displayLines = 0;
            currentProgressPhase = "";
            currentProgressSpeed = 0;
            const startTime = performance.now();

            if (wrapper) wrapper.classList.add("generating");
            if (btn) btn.classList.add("generating");
            if (progressBar) {
                progressBar.style.width = "1%";
                progressBar.style.background = "";
            }
            if (label) label.innerText = window.t ? window.t("topbar.generating") : "Generating...";

            const renderInterval = setInterval(() => {
                if (!isGenerating) {
                    clearInterval(renderInterval);
                    return;
                }
                const diff = targetP - currentP;
                if (diff > 0) {
                    currentP += Math.max(0.5, diff * 0.22);
                } else if (diff < 0) {
                    currentP = targetP;
                }

                if (generatedLinesCount > displayLines) {
                    displayLines += Math.max(1, Math.ceil((generatedLinesCount - displayLines) * 0.35));
                } else {
                    displayLines = generatedLinesCount;
                }
                
                const displayVal = Math.min(99, Math.floor(currentP));
                if (progressBar) progressBar.style.width = displayVal + "%";
                if (label) {
                    const unitLin = window.t ? window.t("estimation.unit_lines") : "lines";
                    if (cancelRequested) {
                        label.innerText = window.t ? window.t("topbar.stopping") : "Stopping...";
                    } else if (isHoveringGenerateBtn) {
                        label.innerText = window.t ? window.t("topbar.stop") : "Stop";
                    } else if (displayLines > 0) {
                        const lStr = Math.floor(displayLines).toLocaleString();
                        if (currentProgressSpeed > 0) {
                            label.innerText = `${lStr} ${unitLin} (${displayVal}%) • ${currentProgressSpeed.toLocaleString()} l/s`;
                        } else {
                            label.innerText = `${lStr} ${unitLin} (${displayVal}%)`;
                        }
                    } else if (currentProgressPhase) {
                        label.innerText = `${formatProgressPhase(currentProgressPhase)} (${displayVal}%)`;
                    } else {
                        const genText = window.t ? window.t("topbar.generating") : "Generating...";
                        label.innerText = `${genText} ${displayVal}%`;
                    }
                }
            }, 25);

            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.process_graph(graph.serialize()).then((res) => {
                    const elapsed = (performance.now() - startTime) / 1000.0;
                    if (res && res.cancelled) {
                        clearInterval(renderInterval);
                        finishGeneration(res, elapsed);
                        return;
                    }
                    targetP = 100;
                    const finishCheckInterval = setInterval(() => {
                        if (currentP >= 98 || !isGenerating) {
                            clearInterval(finishCheckInterval);
                            clearInterval(renderInterval);
                            currentP = 100;
                            finishGeneration(res, elapsed);
                        }
                    }, 30);
                }).catch(err => {
                    console.error("Error processing graph:", err);
                    clearInterval(renderInterval);
                    finishGeneration({ success: false, error: String(err) }, 0);
                });
            } else {
                const interval = setInterval(() => {
                    if (cancelRequested) {
                        clearInterval(interval);
                        clearInterval(renderInterval);
                        finishGeneration({ success: false, cancelled: true }, 0);
                        return;
                    }
                    targetP += 3;
                    generatedLinesCount += 120;
                    if (targetP >= 100) {
                        clearInterval(interval);
                        clearInterval(renderInterval);
                        targetP = 100; currentP = 100;
                        const elapsed = (performance.now() - startTime) / 1000.0;
                        finishGeneration({ success: true, lines_generated: generatedLinesCount }, elapsed);
                    }
                }, 35);
            }
        }

        function finishGeneration(result, elapsedSeconds) {
            const wrapper = document.querySelector(".btn-generate-wrapper");
            const btn = document.getElementById("btn-generate-main");
            const label = document.getElementById("btn-generate-label");
            const progressBar = document.getElementById("btn-progress-bar");

            const isCancel = cancelRequested || (result && result.cancelled);
            const isError = result && result.success === false && !isCancel;

            if (progressBar) {
                progressBar.style.width = "100%";
                if (isCancel) {
                    progressBar.style.background = "linear-gradient(90deg, #f43f5e, #e11d48)";
                } else if (isError) {
                    progressBar.style.background = "linear-gradient(90deg, #ef4444, #b91c1c)";
                } else {
                    progressBar.style.background = "var(--btn-finish-radial, var(--accent-gradient))";
                }
            }

            if (label) {
                if (isCancel) {
                    label.innerText = window.PyxisI18n ? PyxisI18n.t("ui.notifications.gen_cancelled") : "Generation cancelled";
                } else if (isError) {
                    label.innerText = window.PyxisI18n ? PyxisI18n.t("ui.notifications.gen_error") : "Generation error";
                } else {
                    const finalTotal = (result && result.lines_generated !== undefined) ? result.lines_generated : generatedLinesCount;
                    const timeStr = elapsedSeconds > 0 ? ` (${elapsedSeconds.toFixed(1)}s)` : "";
                    label.innerText = window.PyxisI18n ? PyxisI18n.t("ui.notifications.lines_created", { count: finalTotal.toLocaleString(), time: timeStr }) : `${finalTotal.toLocaleString()} lines created!${timeStr}`;
                }
            }

            if (isCancel || isError) {
                setTimeout(() => {
                    isGenerating = false;
                    cancelRequested = false;
                    generatedLinesCount = 0;
                    currentProgressPhase = "";
                    currentProgressSpeed = 0;
                    if (wrapper) wrapper.classList.remove("generating");
                    if (btn) btn.classList.remove("generating");
                    if (progressBar) {
                        progressBar.style.width = "0%";
                        progressBar.style.background = "";
                    }
                    if (label) label.innerText = window.t ? window.t("topbar.generate") : "Generate Layers";
                }, 1500);
            } else {
                setTimeout(() => {
                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.complete_and_hide === "function") {
                        window.pywebview.api.complete_and_hide();
                    }

                    isGenerating = false;
                    cancelRequested = false;
                    generatedLinesCount = 0;
                    currentProgressPhase = "";
                    currentProgressSpeed = 0;
                    if (wrapper) wrapper.classList.remove("generating");
                    if (btn) btn.classList.remove("generating");
                    if (progressBar) {
                        progressBar.style.width = "0%";
                        progressBar.style.background = "";
                    }
                    if (label) label.innerText = window.t ? window.t("topbar.generate") : "Generate Layers";
                }, 2200);
            }
        }

        function addProperties(node, definition) {
            if (definition && definition.properties) {
                try {
                    node.properties = JSON.parse(JSON.stringify(definition.properties));
                } catch(e) {
                    node.properties = Object.assign({}, definition.properties);
                }
            } else {
                node.properties = {};
            }
        }


        // --- Widget Sync & State Serialization ---
        function syncWidgetsToProperties() {
            if (!graph._nodes) return;
            graph._nodes.forEach(n => {
                if (!n.properties) n.properties = {};
                if (n.type === "System/Previewer" || n.type === "Previewer" || (n.title && n.title.includes("Previewer"))) {
                    const activeP = (window.PyxisNodePlayerManager && window.PyxisNodePlayerManager.activePlayers)
                        ? window.PyxisNodePlayerManager.activePlayers[String(n.id)]
                        : null;

                    // Si se está cargando un template y el reproductor aún no se ha instanciado por completo,
                    // proteger las propiedades cargadas del JSON para que no se sobreescriban con valores por defecto.
                    if (window.__pyxis_is_loading_template && (!activeP || !activeP.isInitialized)) {
                        // Preservar propiedades cargadas del template
                    } else if (activeP && activeP.isPinned) {
                        n.properties.is_pinned = true;
                        if (n.size && n.size[0] > 0) {
                            n.properties.pinned_width = Math.round(n.size[0]);
                        }
                        if (activeP.originalSize) {
                            n.properties.previewer_width = Math.round(activeP.originalSize[0]);
                            n.properties.previewer_height = Math.round(activeP.originalSize[1]);
                        }
                        if (activeP.wrapper) {
                            const fx = parseFloat(activeP.wrapper.style.left);
                            const fy = parseFloat(activeP.wrapper.style.top);
                            const fw = parseFloat(activeP.wrapper.style.width);
                            const fh = parseFloat(activeP.wrapper.style.height);
                            if (!isNaN(fx)) n.properties.floating_x = Math.round(fx);
                            else if (activeP.savedFloatingLeft) n.properties.floating_x = Math.round(parseFloat(activeP.savedFloatingLeft));
                            if (!isNaN(fy)) n.properties.floating_y = Math.round(fy);
                            else if (activeP.savedFloatingTop) n.properties.floating_y = Math.round(parseFloat(activeP.savedFloatingTop));
                            if (!isNaN(fw) && fw > 0) n.properties.floating_width = Math.round(fw);
                            else if (activeP.savedFloatingWidth) n.properties.floating_width = Math.round(parseFloat(activeP.savedFloatingWidth));
                            if (!isNaN(fh) && fh > 0) n.properties.floating_height = Math.round(fh);
                            else if (activeP.savedFloatingHeight) n.properties.floating_height = Math.round(parseFloat(activeP.savedFloatingHeight));
                        }
                    } else if (n.size && Array.isArray(n.size) && n.size[0] > 0 && n.size[1] >= 140) {
                        n.properties.is_pinned = false;
                        delete n.properties.pinned_width;
                        delete n.properties.floating_x;
                        delete n.properties.floating_y;
                        delete n.properties.floating_width;
                        delete n.properties.floating_height;
                        n.properties.previewer_width = Math.round(n.size[0]);
                        n.properties.previewer_height = Math.round(n.size[1]);
                    }

                    if (!window.__pyxis_is_loading_template || (activeP && activeP.isInitialized)) {
                        if (activeP && activeP.transformState) {
                            const ts = activeP.transformState;
                            const isCust = Boolean(ts.isCustom);
                            n.properties.viewport_zoom = isCust ? (ts.userZoom || 1.0) : 1.0;
                            n.properties.viewport_pan_x = isCust ? Math.round((ts.panX || 0) * 100) / 100 : 0;
                            n.properties.viewport_pan_y = isCust ? Math.round((ts.panY || 0) * 100) / 100 : 0;
                            n.properties.viewport_custom = isCust;
                        }
                    }
                }
                if (!n.widgets) return;
                n.widgets.forEach(w => {
                    if (w.type !== "button" && w.property) {
                        if (w.value !== undefined && w.value !== null) {
                            n.properties[w.property] = w.value;
                        } else if (n.properties[w.property] !== undefined) {
                            w.value = n.properties[w.property];
                        }
                    }
                });
            });
        }

        window.__pyxis_get_state = function () {
            if (!graph || typeof graph.serialize !== "function") {
                return "";
            }
            syncWidgetsToProperties();
            try {
                const serialized = graph.serialize();
                if (serialized && typeof serialized === "object") {
                    if (!serialized.extra) serialized.extra = {};
                    if (window.canvas && window.canvas.ds) {
                        serialized.extra.canvas_zoom = window.canvas.ds.scale;
                        if (window.canvas.ds.offset) {
                            serialized.extra.canvas_offset = [window.canvas.ds.offset[0], window.canvas.ds.offset[1]];
                        }
                    }
                    if (window.__pyxis_active_template_id) {
                        serialized.extra.active_template_id = window.__pyxis_active_template_id;
                        serialized.extra.active_template_name = window.__pyxis_active_template_name || "Template";
                    }
                }
                return JSON.stringify(serialized);
            } catch (error) {
                console.error("Pyxis: failed to serialize graph on close", error);
                return "";
            }
        };

window.syncWidgetsToProperties = typeof syncWidgetsToProperties === 'function' ? syncWidgetsToProperties : window.syncWidgetsToProperties;
