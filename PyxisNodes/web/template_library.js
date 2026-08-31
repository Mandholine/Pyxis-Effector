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

/* Biblioteca permanente de templates Pyxis Engine 1.0.5.
 * Cargar después del script principal de index.html.
 */
(function () {
    "use strict";

    var selected_template_id = null;
    var modal = null;

    function api_ready() {
        return window.pywebview && window.pywebview.api;
    }

    function graph_ready() {
        return window.graph && typeof window.graph.serialize === "function";
    }

    function sync_graph_widgets() {
        if (typeof window.syncWidgetsToProperties === "function") {
            window.syncWidgetsToProperties();
            return;
        }
        if (!graph_ready() || !graph._nodes) return;
        graph._nodes.forEach(function (node) {
            if (!node.widgets || !node.properties) return;
            node.widgets.forEach(function (widget) {
                if (widget.type !== "button" && widget.property !== undefined && widget.value !== undefined) {
                    node.properties[widget.property] = widget.value;
                }
            });
        });
    }

    function update_checkpoint() {
        if (!graph_ready()) return;
        if (typeof window.syncWidgetsToProperties === "function") {
            window.syncWidgetsToProperties();
        }
        sync_graph_widgets();
        try {
            window.__pyxis_template_checkpoint = JSON.stringify(graph.serialize());
        } catch (e) {
            console.error("Pyxis: no se pudo guardar el checkpoint del template", e);
        }
    }

    function has_changes() {
        if (!graph_ready()) return false;
        if (typeof window.syncWidgetsToProperties === "function") {
            window.syncWidgetsToProperties();
        }
        sync_graph_widgets();
        var current_json = "";
        try {
            current_json = JSON.stringify(graph.serialize());
        } catch (e) {
            console.error("Pyxis: error al serializar grafo para verificar cambios", e);
            return false;
        }

        if (window.__pyxis_template_checkpoint === undefined || window.__pyxis_template_checkpoint === null) {
            return graph._nodes && graph._nodes.length > 0;
        }
        return current_json !== window.__pyxis_template_checkpoint;
    }

    function check_unknown_nodes(graph_data) {
        if (!graph_data || !Array.isArray(graph_data.nodes)) {
            return { valid: false, message: "El template no contiene un formato de grafo válido." };
        }
        if (graph_data.nodes.length === 0) {
            return { valid: false, message: "El template está vacío (no contiene nodos)." };
        }
        var unregistered = [];
        graph_data.nodes.forEach(function (node) {
            if (node && node.type && !LiteGraph.getNodeType(node.type)) {
                unregistered.push(node.type);
            }
        });
        if (unregistered.length > 0) {
            return { valid: true, unknown: unregistered };
        }
        return { valid: true, unknown: [] };
    }

    function show_confirm_dialog(title, text, on_confirm, on_cancel, confirm_btn_text) {
        var confirm_overlay = document.createElement("div");
        confirm_overlay.className = "pyxis-template-overlay";
        confirm_overlay.style.zIndex = "2100";
        confirm_btn_text = confirm_btn_text || (window.t ? window.t("common.confirm") : "Aceptar");
        var cancel_btn_text = window.t ? window.t("common.cancel") : "Cancelar";
        confirm_overlay.innerHTML = `
            <div class="pyxis-template-dialog" style="width: 440px;">
                <h2 style="color: #ef4444;">${title}</h2>
                <div style="margin: 12px 0 20px; line-height: 1.5; font-size: 14px; color: var(--text-main);">${text}</div>
                <div class="pyxis-template-actions" style="justify-content: flex-end;">
                    <button class="pyxis-btn" id="pyxis-confirm-cancel">${cancel_btn_text}</button>
                    <button class="pyxis-btn pyxis-btn-danger" id="pyxis-confirm-ok">${confirm_btn_text}</button>
                </div>
            </div>`;
        document.body.appendChild(confirm_overlay);

        confirm_overlay.querySelector("#pyxis-confirm-cancel").onclick = function () {
            confirm_overlay.remove();
            if (on_cancel) on_cancel();
        };

        confirm_overlay.querySelector("#pyxis-confirm-ok").onclick = function () {
            confirm_overlay.remove();
            if (on_confirm) on_confirm();
        };
    }

    function create_button(text, handler) {
        var button = document.createElement("button");
        button.className = "pyxis-btn";
        button.innerText = text;
        button.addEventListener("click", handler);
        return button;
    }

    function ensure_styles() {
        if (document.getElementById("pyxis-template-styles")) return;
        var style = document.createElement("style");
        style.id = "pyxis-template-styles";
        style.textContent = `
            .pyxis-template-button { margin-left: 8px; }
            .pyxis-template-overlay { position: fixed; inset: 0; z-index: 2000; background: rgba(0,0,0,.78); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); display:flex; align-items:center; justify-content:center; }
            .pyxis-template-dialog { width: 780px; max-height: 85vh; overflow:hidden; background: var(--bg-panel, #161b22); border: 1px solid var(--border-subtle, rgba(255,255,255,0.1)); border-radius: 14px; padding: 22px; color: var(--text-main, #f3f4f6); font-family: var(--font-sans, sans-serif); box-shadow: 0 20px 50px rgba(0,0,0,0.7); }
            .pyxis-template-dialog h2 { margin:0 0 14px; color: var(--accent-primary, #10b981); font-size: 18px; font-weight: 700; }
            .pyxis-template-toolbar { display:flex; gap:10px; margin-bottom:14px; }
            .pyxis-template-toolbar input, .pyxis-template-toolbar select { background: var(--bg-input, #12151b); color: var(--text-main, #f3f4f6); border:1px solid var(--border-subtle, rgba(255,255,255,0.1)); padding:9px 12px; border-radius:8px; font-family:inherit; font-size:13px; }
            .pyxis-template-toolbar input { flex:2; }
            .pyxis-template-toolbar select { flex:1; min-width: 140px; }
            .pyxis-template-list { max-height:48vh; overflow:auto; border:1px solid var(--border-subtle, rgba(255,255,255,0.1)); border-radius:8px; background: var(--bg-card, #181d24); }
            .pyxis-template-row { display:flex; align-items:center; gap:12px; padding:12px 14px; border-bottom:1px solid var(--border-subtle, rgba(255,255,255,0.06)); cursor:pointer; transition: background 0.15s ease; }
            .pyxis-template-row:hover, .pyxis-template-row.selected { background: rgba(16, 185, 129, 0.12); }
            .pyxis-template-star { font-size: 18px; cursor: pointer; color: #555; user-select: none; transition: color 0.15s, transform 0.15s; }
            .pyxis-template-star.active { color: #ffd700; }
            .pyxis-template-star:hover { transform: scale(1.25); }
            .pyxis-template-badge { background: rgba(16, 185, 129, 0.2); color: var(--accent-primary, #10b981); font-size: 11px; padding: 3px 8px; border-radius: 12px; border: 1px solid var(--accent-primary, #10b981); margin-left: 6px; font-weight: bold; }
            .pyxis-template-info { flex:1; min-width:0; }
            .pyxis-template-name { color: var(--accent-primary, #10b981); font-weight:bold; display: flex; align-items: center; font-size: 14px; }
            .pyxis-template-comment, .pyxis-template-meta { color: var(--text-muted, #9ca3af); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:2px; }
            .pyxis-template-actions { display:flex; align-items: center; gap:10px; margin-top:16px; }
            .pyxis-template-empty { color: var(--text-muted, #9ca3af); padding:30px; text-align:center; font-size: 14px; }
            .pyxis-template-error { color:#ef4444; min-height:18px; margin-top:8px; font-size:13px; }
        `;
        document.head.appendChild(style);
    }

    function close_modal(targetEl) {
        if (targetEl && targetEl.target) {
            targetEl = targetEl.target;
        }
        if (targetEl && typeof targetEl.closest === "function") {
            var overlay = targetEl.closest(".pyxis-template-overlay");
            if (overlay) overlay.remove();
        } else if (modal && modal.parentNode) {
            modal.remove();
            modal = null;
        } else {
            document.querySelectorAll(".pyxis-template-overlay").forEach(function (el) {
                try { el.remove(); } catch (e) {}
            });
            modal = null;
        }
        selected_template_id = null;
    }

    function show_message(container, message, type) {
        var error = container.querySelector(".pyxis-template-error");
        if (error) {
            error.innerText = message || "";
            if (type === "success") {
                error.style.color = "var(--accent-primary, #10b981)";
            } else if (type === "info") {
                error.style.color = "var(--text-muted, #9ca3af)";
            } else {
                error.style.color = "#ef4444";
            }
        }
    }

    function save_template_with_id(name, comment, template_id) {
        var serialized = graph.serialize();
        return window.pywebview.api.save_template(name, comment, serialized, template_id).then(function (meta) {
            window.__pyxis_active_template_id = meta.template_id;
            window.__pyxis_active_template_name = meta.name;
            localStorage.setItem("pyxis_active_template_id", meta.template_id);
            localStorage.setItem("pyxis_active_template_name", meta.name);
            localStorage.setItem("pyxis_last_used_template_id", meta.template_id);
            update_checkpoint();
            if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
            if (typeof window.__pyxis_schedule_save === "function") window.__pyxis_schedule_save(50);
            return meta;
        });
    }

    function open_save_dialog_form(default_name, default_comment, target_template_id, on_save_success) {
        ensure_styles();
        var save_modal = document.createElement("div");
        save_modal.className = "pyxis-template-overlay";
        save_modal.style.zIndex = "2250";
        save_modal.innerHTML = `
            <div class="pyxis-template-dialog" style="width: 520px;">
                <h2>${target_template_id ? (window.t ? window.t("library.overwrite_title") : "Sobrescribir plantilla") : (window.t ? window.t("library.save_modal_title") : "Guardar plantilla")}</h2>
                <label style="font-size: 13px; color: var(--text-muted);">${window.t ? window.t("library.tpl_name") : "Name"}</label>
                <input id="pyxis-save-name" style="width:100%;box-sizing:border-box;margin:6px 0 14px;background:var(--bg-input);color:var(--text-main);border:1px solid var(--border-subtle);padding:10px;border-radius:8px;font-family:inherit;" maxlength="80" value="${default_name || ""}">
                <label style="font-size: 13px; color: var(--text-muted);">${window.t ? window.t("library.tpl_desc") : "Comentario (opcional)"}</label>
                <textarea id="pyxis-save-comment" style="width:100%;height:90px;box-sizing:border-box;margin-top:6px;background:var(--bg-input);color:var(--text-main);border:1px solid var(--border-subtle);padding:10px;border-radius:8px;resize:vertical;font-family:inherit;">${default_comment || ""}</textarea>
                <div class="pyxis-template-error"></div>
                <div class="pyxis-template-actions" style="justify-content: flex-end;">
                    <button class="pyxis-btn" id="pyxis-save-cancel">${window.t ? window.t("common.cancel") : "Cancelar"}</button>
                    <button class="pyxis-btn pyxis-btn-primary" id="pyxis-save-confirm">${window.t ? window.t("common.save") : "Guardar"}</button>
                </div>
            </div>`;
        document.body.appendChild(save_modal);

        save_modal.querySelector("#pyxis-save-cancel").onclick = function () {
            save_modal.remove();
        };
        save_modal.querySelector("#pyxis-save-confirm").onclick = async function () {
            var name = save_modal.querySelector("#pyxis-save-name").value.trim();
            var comment = save_modal.querySelector("#pyxis-save-comment").value.trim();
            if (!name) {
                show_message(save_modal, window.t ? window.t("library.prompt_name_required") : "Escribe un nombre para la plantilla.");
                return;
            }

            var serialized = graph.serialize();
            if (!serialized || !Array.isArray(serialized.nodes) || serialized.nodes.length === 0) {
                show_message(save_modal, window.t ? window.t("library.empty_graph_warning") : "El grafo actual está vacío. No se puede guardar una plantilla vacía.");
                return;
            }

            this.disabled = true;
            this.innerText = window.t ? window.t("common.saving") : "Guardando...";
            try {
                var meta = await save_template_with_id(name, comment, target_template_id);
                save_modal.remove();
                if (typeof on_save_success === "function") {
                    on_save_success(meta);
                }
            } catch (error) {
                this.disabled = false;
                this.innerText = window.t ? window.t("common.save") : "Guardar";
                show_message(save_modal, window.t ? window.t("library.error_save") : "No se pudo guardar la plantilla.");
                console.error(error);
            }
        };
        save_modal.querySelector("#pyxis-save-name").focus();
    }

    function show_unsaved_changes_dialog(on_save_library, on_save_as, on_discard, on_cancel) {
        var overlay = document.createElement("div");
        overlay.className = "pyxis-template-overlay";
        overlay.style.zIndex = "2200";
        overlay.innerHTML = `
            <div class="pyxis-template-dialog" style="width: 530px; padding: 24px; background: #161920; border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; box-shadow: 0 20px 40px rgba(0,0,0,0.7); color: #ffffff; font-family: system-ui, -apple-system, sans-serif;">
                <div style="display: flex; gap: 16px; align-items: flex-start;">
                    <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 10px; border: 1.5px solid #d97706; background: rgba(217, 119, 6, 0.12); display: flex; align-items: center; justify-content: center;">
                        <svg viewBox="0 0 24 24" style="width: 22px; height: 22px; stroke: #f59e0b; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                    </div>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 6px 0; font-size: 18px; font-weight: 700; color: #ffffff; line-height: 1.2;">${window.t ? window.t("library.unsaved_title") : "Cambios sin guardar"}</h3>
                        <p style="margin: 0; font-size: 13.5px; line-height: 1.45; color: #9ca3af;">
                            ${window.t ? window.t("library.unsaved_msg") : "Hiciste cambios en este template. Si cargas otro, los perderás.<br>¿Seguro de que quieres continuar?"}
                        </p>
                    </div>
                </div>
                
                <div style="height: 1px; background: rgba(255, 255, 255, 0.08); margin: 20px 0 18px 0;"></div>
                
                <div style="display: flex; justify-content: flex-end; gap: 10px; align-items: center;">
                    <button id="pyxis-unsaved-cancel" style="background: #272a30; border: 1px solid #3a3f4a; color: #e5e7eb; padding: 9px 18px; border-radius: 8px; font-size: 13.5px; font-weight: 600; cursor: pointer; transition: all 0.15s ease;">
                        ${window.t ? window.t("common.cancel") : "Cancelar"}
                    </button>
                    <button id="pyxis-unsaved-discard" style="background: rgba(220, 38, 38, 0.18); border: 1px solid #b91c1c; color: #fca5a5; padding: 9px 18px; border-radius: 8px; font-size: 13.5px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.15s ease;">
                        <svg viewBox="0 0 24 24" style="width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                        ${window.t ? window.t("library.discard") : "Descartar"}
                    </button>
                    <button id="pyxis-unsaved-save-lib" style="background: #059669; border: 1px solid #10b981; color: #ffffff; padding: 9px 20px; border-radius: 8px; font-size: 13.5px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 7px; transition: all 0.15s ease; box-shadow: 0 2px 8px rgba(5, 150, 105, 0.25);">
                        <svg viewBox="0 0 24 24" style="width: 15px; height: 15px; stroke: currentColor; fill: none; stroke-width: 2;"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                        ${window.t ? window.t("library.save_and_continue") : "Guardar en biblioteca"}
                    </button>
                </div>
            </div>`;
        document.body.appendChild(overlay);

        var btnCancel = overlay.querySelector("#pyxis-unsaved-cancel");
        var btnDiscard = overlay.querySelector("#pyxis-unsaved-discard");
        var btnSave = overlay.querySelector("#pyxis-unsaved-save-lib");

        if (btnCancel) {
            btnCancel.onclick = function () {
                overlay.remove();
                if (on_cancel) on_cancel();
            };
        }
        if (btnSave) {
            btnSave.onclick = function () {
                overlay.remove();
                if (on_save_library) on_save_library();
            };
        }
        if (btnDiscard) {
            btnDiscard.onclick = function () {
                overlay.remove();
                if (on_discard) on_discard();
            };
        }
    }

    function open_save_dialog(on_save_success) {
        if (!graph_ready()) {
            alert(window.t ? window.t("library.canvas_not_ready") : "El lienzo de nodos no está listo.");
            return;
        }
        sync_graph_widgets();

        var serialized = graph.serialize();
        if (!serialized || !Array.isArray(serialized.nodes) || serialized.nodes.length === 0) {
            alert(window.t ? window.t("library.empty_graph_warning") : "El grafo actual está vacío. No se puede guardar un template vacío.");
            return;
        }

        if (window.__pyxis_active_template_id && window.__pyxis_active_template_name) {
            ensure_styles();
            var choice_modal = document.createElement("div");
            choice_modal.className = "pyxis-template-overlay";
            choice_modal.style.zIndex = "2250";
            choice_modal.innerHTML = `
                <div class="pyxis-template-dialog" style="width: 480px;">
                    <h2>${window.t ? window.t("library.save_modal_title") : "Guardar plantilla"}</h2>
                    <p style="margin: 12px 0 20px; font-size: 14px; color: var(--text-main);">
                        ${window.t ? window.t("library.overwrite_msg", { name: window.__pyxis_active_template_name }) : `Estás trabajando sobre <strong>${window.__pyxis_active_template_name}</strong>. ¿Cómo deseas guardar los cambios?`}
                    </p>
                    <div class="pyxis-template-actions" style="flex-direction: column; gap: 10px; align-items: stretch;">
                        <button class="pyxis-btn pyxis-btn-primary" id="pyxis-save-overwrite" style="padding: 11px;">${window.t ? window.t("library.overwrite_btn") : `Sobrescribir "${window.__pyxis_active_template_name}"`}</button>
                        <button class="pyxis-btn" id="pyxis-save-as-disk" style="padding: 11px;">${window.t ? window.t("library.save_as_disk") : "Guardar como archivo en disco (.json)"}</button>
                        <button class="pyxis-btn" id="pyxis-save-as-lib" style="padding: 11px;">${window.t ? window.t("library.save_as_new_lib") : "Guardar como nueva plantilla en Biblioteca..."}</button>
                        <button class="pyxis-btn" id="pyxis-save-choice-cancel" style="padding: 8px; margin-top: 5px;">${window.t ? window.t("common.cancel") : "Cancelar"}</button>
                    </div>
                </div>`;
            document.body.appendChild(choice_modal);

            choice_modal.querySelector("#pyxis-save-choice-cancel").onclick = function () { choice_modal.remove(); };
            choice_modal.querySelector("#pyxis-save-overwrite").onclick = async function () {
                choice_modal.remove();
                try {
                    var meta = await save_template_with_id(
                        window.__pyxis_active_template_name,
                        null,
                        window.__pyxis_active_template_id
                    );
                    if (typeof on_save_success === "function") {
                        on_save_success(meta);
                    }
                } catch (err) {
                    alert(window.t ? window.t("library.error_overwrite") : "Error al sobrescribir el template.");
                }
            };
            choice_modal.querySelector("#pyxis-save-as-disk").onclick = function () {
                choice_modal.remove();
                open_save_as_dialog().then(function (saved) {
                    if (saved && typeof on_save_success === "function") on_save_success();
                });
            };
            choice_modal.querySelector("#pyxis-save-as-lib").onclick = function () {
                var prev_name = window.__pyxis_active_template_name;
                choice_modal.remove();
                open_save_dialog_form(prev_name + " (Copia)", "", null, on_save_success);
            };
        } else {
            open_save_dialog_form("", "", null, on_save_success);
        }
    }

    function render_templates(container, templates, search_text, sort_by) {
        var list = container.querySelector(".pyxis-template-list");
        list.innerHTML = "";
        var query = (search_text || "").toLowerCase();
        var last_used_id = localStorage.getItem("pyxis_last_used_template_id");

        var filtered = templates.filter(function (item) {
            return !query || (item.name + " " + (item.comment || "")).toLowerCase().indexOf(query) >= 0;
        });

        filtered.sort(function (a, b) {
            var favA = a.is_favorite ? 1 : 0;
            var favB = b.is_favorite ? 1 : 0;

            var valA, valB;
            switch (sort_by) {
                case "updated_desc":
                    valA = a.updated_at || a.created_at || "";
                    valB = b.updated_at || b.created_at || "";
                    return (favB - favA) || valB.localeCompare(valA);
                case "updated_asc":
                    valA = a.updated_at || a.created_at || "";
                    valB = b.updated_at || b.created_at || "";
                    return (favB - favA) || valA.localeCompare(valB);
                case "name_asc":
                    valA = (a.name || "").toLowerCase();
                    valB = (b.name || "").toLowerCase();
                    return valA.localeCompare(valB);
                case "name_desc":
                    valA = (a.name || "").toLowerCase();
                    valB = (b.name || "").toLowerCase();
                    return valB.localeCompare(valA);
                case "nodes_desc":
                    valA = a.node_count || 0;
                    valB = b.node_count || 0;
                    return valB - valA;
                case "nodes_asc":
                    valA = a.node_count || 0;
                    valB = b.node_count || 0;
                    return valA - valB;
                default:
                    return (favB - favA);
            }
        });

        if (!filtered.length) {
            list.innerHTML = '<div class="pyxis-template-empty">' + (window.t ? window.t("library.empty") : "No se encontraron templates.") + '</div>';
            return;
        }

        filtered.forEach(function (item) {
            var row = document.createElement("div");
            row.className = "pyxis-template-row";
            if (selected_template_id === item.template_id) {
                row.classList.add("selected");
            }

            var is_last = (item.template_id === last_used_id);
            var badge_html = is_last ? '<span class="pyxis-template-badge">' + (window.t ? window.t("library.last_used") : "Último usado") + '</span>' : '';
            var star_class = item.is_favorite ? 'pyxis-template-star active' : 'pyxis-template-star';

            row.innerHTML = `
                <div class="${star_class}" title="${window.t ? window.t("library.favorite_title") : "Marcar como favorito"}">★</div>
                <div class="pyxis-template-info">
                    <div class="pyxis-template-name"><span class="name-text"></span>${badge_html}</div>
                    <div class="pyxis-template-comment"></div>
                    <div class="pyxis-template-meta"></div>
                </div>`;

            row.querySelector(".name-text").innerText = item.name || (window.t ? window.t("library.unnamed") : "Sin nombre");
            row.querySelector(".pyxis-template-comment").innerText = item.comment || (window.t ? window.t("library.no_comment") : "Sin comentario");
            row.querySelector(".pyxis-template-meta").innerText =
                (item.node_count || 0) + " " + (window.t ? window.t("library.nodes_count") : "nodos") + " · " + (item.updated_at || item.created_at || "");

            row.querySelector(".pyxis-template-star").onclick = async function (e) {
                e.stopPropagation();
                try {
                    var new_state = await window.pywebview.api.toggle_favorite(item.template_id);
                    item.is_favorite = new_state;
                    render_templates(container, templates, search_text, sort_by);
                } catch (err) {
                    console.error("Error al cambiar favorito", err);
                }
            };

            row.onclick = function () {
                selected_template_id = item.template_id;
                container.querySelectorAll(".pyxis-template-row").forEach(function (element) {
                    element.classList.remove("selected");
                });
                row.classList.add("selected");

                var del_btn = container.querySelector("#pyxis-template-delete");
                var dup_btn = container.querySelector("#pyxis-template-duplicate");
                var exp_btn = container.querySelector("#pyxis-template-export");
                if (del_btn) del_btn.style.display = "inline-block";
                if (dup_btn) dup_btn.style.display = "inline-block";
                if (exp_btn) exp_btn.style.display = "inline-block";
            };
            list.appendChild(row);
        });
    }

    async function open_library() {
        if (window.LiteGraph && typeof window.LiteGraph.closeAllContextMenus === "function") {
            window.LiteGraph.closeAllContextMenus();
        }
        ensure_styles();
        modal = document.createElement("div");
        modal.className = "pyxis-template-overlay";
        modal.innerHTML = `
            <div class="pyxis-template-dialog">
                <h2>${window.t ? window.t("library.title") : "Biblioteca de Plantillas"}</h2>
                <div class="pyxis-template-toolbar">
                    <input id="pyxis-template-search" placeholder="${window.t ? window.t("library.search_placeholder") : "Buscar por nombre o comentario..."}">
                    <select id="pyxis-template-sort">
                        <option value="updated_desc">${window.t ? window.t("library.sort_updated_desc") : "Fecha (más reciente)"}</option>
                        <option value="updated_asc">${window.t ? window.t("library.sort_updated_asc") : "Fecha (más antiguo)"}</option>
                        <option value="name_asc">${window.t ? window.t("library.sort_name_asc") : "Nombre (A-Z)"}</option>
                        <option value="name_desc">${window.t ? window.t("library.sort_name_desc") : "Nombre (Z-A)"}</option>
                        <option value="nodes_desc">${window.t ? window.t("library.sort_nodes_desc") : "Nodos (mayor a menor)"}</option>
                        <option value="nodes_asc">${window.t ? window.t("library.sort_nodes_asc") : "Nodos (menor a mayor)"}</option>
                    </select>
                    <button class="pyxis-btn" id="pyxis-template-import" title="${window.t ? window.t("library.import_tooltip") : "Importar plantilla desde archivo (.json)"}">
                        <svg class="svg-icon" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <span>${window.t ? window.t("library.import") : "Importar"}</span>
                    </button>
                    <button class="pyxis-btn pyxis-btn-icon" id="pyxis-template-refresh" title="${window.t ? window.t("library.refresh_tooltip") : "Refrescar biblioteca"}">
                        <svg class="svg-icon" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                    </button>
                </div>
                <div class="pyxis-template-list"><div class="pyxis-template-empty">${window.t ? window.t("common.loading") : "Cargando..."}</div></div>
                <div class="pyxis-template-error"></div>
                <div class="pyxis-template-actions">
                    <button class="pyxis-btn pyxis-btn-danger" id="pyxis-template-delete" style="display:none;">${window.t ? window.t("common.delete") : "Eliminar"}</button>
                    <button class="pyxis-btn" id="pyxis-template-duplicate" style="display:none;" title="${window.t ? window.t("library.duplicate_tooltip") : "Duplicar plantilla seleccionada"}">${window.t ? window.t("library.duplicate") : "Duplicar"}</button>
                    <button class="pyxis-btn" id="pyxis-template-export" style="display:none;" title="${window.t ? window.t("library.export_tooltip") : "Exportar plantilla seleccionada como archivo .json"}">${window.t ? window.t("library.export") : "Exportar"}</button>
                    <span style="flex:1;"></span>
                    <button class="pyxis-btn" id="pyxis-library-close">${window.t ? window.t("common.close") : "Cerrar"}</button>
                    <button class="pyxis-btn pyxis-btn-primary" id="pyxis-template-load">${window.t ? window.t("library.load") : "Cargar Plantilla"}</button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        var templates = [];
        var search = modal.querySelector("#pyxis-template-search");
        var sort_select = modal.querySelector("#pyxis-template-sort");
        
        var refresh = async function () {
            try {
                templates = await window.pywebview.api.list_templates();
                render_templates(modal, templates, search.value, sort_select.value);
                var del_btn = modal.querySelector("#pyxis-template-delete");
                var dup_btn = modal.querySelector("#pyxis-template-duplicate");
                var exp_btn = modal.querySelector("#pyxis-template-export");
                if (del_btn) del_btn.style.display = selected_template_id ? "inline-block" : "none";
                if (dup_btn) dup_btn.style.display = selected_template_id ? "inline-block" : "none";
                if (exp_btn) exp_btn.style.display = selected_template_id ? "inline-block" : "none";
            } catch (error) {
                show_message(modal, window.t ? window.t("library.read_error") : "No se pudo leer la biblioteca.");
                console.error(error);
            }
        };

        search.oninput = function () { render_templates(modal, templates, search.value, sort_select.value); };
        sort_select.onchange = function () { render_templates(modal, templates, search.value, sort_select.value); };
        modal.querySelector("#pyxis-template-refresh").onclick = refresh;
        modal.querySelector("#pyxis-library-close").onclick = close_modal;
        
        modal.querySelector("#pyxis-template-import").onclick = async function () {
            try {
                var imported = await window.pywebview.api.import_template();
                if (imported) {
                    selected_template_id = imported.template_id;
                    await refresh();
                    show_message(modal, window.t ? window.t("library.import_success") : "Template importado correctamente.", "success");
                }
            } catch (err) {
                show_message(modal, err.message || (window.t ? window.t("library.import_error") : "Error al importar el template."), "error");
            }
        };

        modal.querySelector("#pyxis-template-export").onclick = async function () {
            if (!selected_template_id) return;
            try {
                var ok = await window.pywebview.api.export_template(selected_template_id);
                if (ok) {
                    show_message(modal, window.t ? window.t("library.export_success") : "Template exportado correctamente.", "success");
                } else {
                    show_message(modal, window.t ? window.t("library.export_cancelled") : "Exportación cancelada.", "info");
                }
            } catch (err) {
                show_message(modal, (window.t ? window.t("library.export_error") : "Error al exportar template: ") + (err.message || err), "error");
            }
        };

        modal.querySelector("#pyxis-template-duplicate").onclick = async function () {
            if (!selected_template_id) return;
            var item = templates.find(t => t.template_id === selected_template_id);
            if (!item) return;

            show_confirm_dialog(
                window.t ? window.t("library.duplicate_confirm_title") : "¿Duplicar template?",
                window.t ? window.t("library.duplicate_confirm_msg", { name: item.name }) : `Se creará una copia independiente del template "${item.name}".`,
                async function () {
                    try {
                        var doc = await window.pywebview.api.load_template(selected_template_id);
                        var copy_meta = await window.pywebview.api.save_template(
                            item.name + " (Copia)",
                            item.comment || "",
                            doc.graph
                        );
                        selected_template_id = copy_meta.template_id;
                        await refresh();
                        show_message(modal, window.t ? window.t("library.duplicate_success") : "Template duplicado correctamente.", "success");
                    } catch (err) {
                        show_message(modal, window.t ? window.t("library.error_duplicate") : "No se pudo duplicar el template.", "error");
                    }
                },
                null,
                window.t ? window.t("library.duplicate") : "Duplicar"
            );
        };

        modal.querySelector("#pyxis-template-delete").onclick = function () {
            if (!selected_template_id) return;
            var item = templates.find(t => t.template_id === selected_template_id);
            if (!item) return;

            show_confirm_dialog(
                window.t ? window.t("library.delete_confirm_title") : "¿Eliminar template?",
                window.t ? window.t("library.delete_confirm_msg", { name: item.name }) : `¿Estás seguro de que deseas eliminar permanentemente "${item.name}"? Esta acción no se puede deshacer.`,
                async function () {
                    try {
                        var deletedId = selected_template_id;
                        await window.pywebview.api.delete_template(deletedId);
                        if (window.__pyxis_active_template_id === deletedId) {
                            window.__pyxis_active_template_id = null;
                            window.__pyxis_active_template_name = null;
                            localStorage.removeItem("pyxis_active_template_id");
                            localStorage.removeItem("pyxis_active_template_name");
                            localStorage.removeItem("pyxis_last_used_template_id");
                            if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
                        }
                        selected_template_id = null;
                        await refresh();
                    } catch (err) {
                        show_message(modal, window.t ? window.t("library.error_delete") : "No se pudo eliminar el template.");
                    }
                },
                null,
                window.t ? window.t("common.delete") : "Eliminar"
            );
        };

        modal.querySelector("#pyxis-template-load").onclick = function () {
            if (!selected_template_id) {
                show_message(modal, window.t ? window.t("library.select_template_prompt") : "Selecciona un template.");
                return;
            }
            var btn = this;
            btn.disabled = true;
            btn.innerText = window.t ? window.t("common.loading") : "Cargando...";

            async function proceed_with_load() {
                try {
                    var result = await window.pywebview.api.load_template(selected_template_id);
                    var check = check_unknown_nodes(result.graph);
                    if (!check.valid) {
                        throw new Error(check.message);
                    }

                    if (check.unknown && check.unknown.length > 0) {
                        show_confirm_dialog(
                            window.t ? window.t("library.unknown_nodes_title") : "Nodos desconocidos detectados",
                            window.t ? window.t("library.unknown_nodes_msg", { nodes: check.unknown.join(", ") }) : `El template contiene tipos de nodos que no están registrados en el entorno actual: <strong>${check.unknown.join(", ")}</strong>.<br><br>¿Deseas cargarlo de todos modos? Se podrían perder conexiones o provocar comportamientos inesperados.`,
                            function () {
                                do_load_graph(result);
                            },
                            function () {
                                btn.disabled = false;
                                btn.innerText = window.t ? window.t("library.load_btn", null, "Cargar") : "Cargar";
                            },
                            window.t ? window.t("library.load_anyway") : "Cargar de todos modos"
                        );
                    } else {
                        do_load_graph(result);
                    }
                } catch (error) {
                    btn.disabled = false;
                    btn.innerText = window.t ? window.t("library.load_btn", null, "Cargar") : "Cargar";
                    show_message(modal, error.message || (window.t ? window.t("library.error_load") : "No se pudo cargar el template."));
                    console.error(error);
                }
            }

            function do_load_graph(result) {
                window.__pyxis_is_loading_template = true;
                const btnTop = document.getElementById("btn-quick-save-template");
                if (btnTop) btnTop.style.display = "none";

                if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.destroyAllPlayers === "function") {
                    window.PyxisNodePlayerManager.destroyAllPlayers();
                }

                graph.configure(result.graph);
                if (typeof window.resetView === "function") window.resetView();
                if (typeof window.syncWidgetsToProperties === "function") window.syncWidgetsToProperties();
                
                const meta = result.metadata || {};
                window.__pyxis_active_template_id = meta.template_id || selected_template_id;
                window.__pyxis_active_template_name = meta.name || "Plantilla";
                if (window.__pyxis_active_template_id) {
                    localStorage.setItem("pyxis_active_template_id", window.__pyxis_active_template_id);
                    localStorage.setItem("pyxis_active_template_name", window.__pyxis_active_template_name);
                    localStorage.setItem("pyxis_last_used_template_id", window.__pyxis_active_template_id);
                }

                update_checkpoint();
                
                setTimeout(function() {
                    if (typeof window.syncWidgetsToProperties === "function") window.syncWidgetsToProperties();
                    update_checkpoint();
                    window.__pyxis_is_loading_template = false;
                    if (window.PyxisUndoManager) {
                        window.PyxisUndoManager.initInitialState();
                    }
                    if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
                }, 150);
                
                close_modal();
            }

            if (has_changes()) {
                show_unsaved_changes_dialog(
                    function () {
                        btn.disabled = false;
                        btn.innerText = window.t ? window.t("library.load_btn", null, "Cargar") : "Cargar";
                        open_save_dialog(async function () {
                            await proceed_with_load();
                        });
                    },
                    async function () {
                        var saved = await open_save_as_dialog();
                        if (saved) {
                            await proceed_with_load();
                        } else {
                            btn.disabled = false;
                            btn.innerText = window.t ? window.t("library.load_btn", null, "Cargar") : "Cargar";
                        }
                    },
                    async function () {
                        await proceed_with_load();
                    },
                    function () {
                        btn.disabled = false;
                        btn.innerText = window.t ? window.t("library.load_btn", null, "Cargar") : "Cargar";
                    }
                );
            } else {
                proceed_with_load();
            }
        };
        await refresh();
    }

    async function open_save_as_dialog() {
        if (!graph_ready()) {
            alert(window.t ? window.t("library.canvas_not_ready") : "El lienzo de nodos no está listo.");
            return false;
        }
        if (!api_ready()) {
            alert(window.t ? window.t("library.api_not_ready") : "La API pywebview no está disponible en este momento.");
            return false;
        }
        sync_graph_widgets();

        var serialized = graph.serialize();
        if (!serialized || !Array.isArray(serialized.nodes) || serialized.nodes.length === 0) {
            alert(window.t ? window.t("library.empty_graph_warning") : "El grafo actual está vacío. No se puede guardar un template vacío.");
            return false;
        }

        var default_name = window.__pyxis_active_template_name || "template";
        try {
            var meta = await window.pywebview.api.save_template_as(serialized, default_name);
            if (meta) {
                window.__pyxis_active_template_id = meta.template_id;
                window.__pyxis_active_template_name = meta.name;
                update_checkpoint();
                if (typeof window.updateTemplateUIState === "function") window.updateTemplateUIState();
                return true;
            }
            return false;
        } catch (err) {
            alert((window.t ? window.t("library.error_save_disk") : "Error al guardar como archivo: ") + (err.message || err));
            return false;
        }
    }

    window.open_template_library_modal = open_library;
    window.open_save_dialog = open_save_dialog;
    window.open_save_as_dialog = open_save_as_dialog;

    function install_toolbar() {
        window.open_template_library_modal = open_library;
        window.open_save_dialog = open_save_dialog;
        window.open_save_as_dialog = open_save_as_dialog;
    }

    function wait_ready() {
        window.open_template_library_modal = open_library;
        window.open_save_dialog = open_save_dialog;
        window.open_save_as_dialog = open_save_as_dialog;
        window.has_template_changes = has_changes;
        window.update_template_checkpoint = update_checkpoint;
        window.update_checkpoint = update_checkpoint;

        if (api_ready() && graph_ready() && window.__pyxis_graph_initialized === true) {
            if (!window.__pyxis_active_template_id) {
                var storedId = localStorage.getItem("pyxis_active_template_id");
                var storedName = localStorage.getItem("pyxis_active_template_name");
                if (storedId && storedName) {
                    window.__pyxis_active_template_id = storedId;
                    window.__pyxis_active_template_name = storedName;
                }
            }
            update_checkpoint();
            install_toolbar();
            if (typeof window.updateTemplateUIState === "function") {
                window.updateTemplateUIState();
            }
        } else {
            setTimeout(wait_ready, 50);
        }
    }

    window.addEventListener("pywebviewready", wait_ready);
    wait_ready();
}());
