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

/* Persistencia temporal de Pyxis.
 * Se inicia solamente después de que index.html haya terminado de
 * cargar/restpyxisr el grafo. Esto evita sobrescribir una sesión válida
 * con graph.serialize() cuando todavía hay cero nodos.
 */
(function () {
    "use strict";

    var save_delay_ms = 100;
    var save_timer = null;
    var save_in_flight = false;
    var save_again = false;
    var last_saved_json = "";
    var started = false;

    function api_ready() {
        return window.pywebview && window.pywebview.api &&
            typeof window.pywebview.api.save_session === "function";
    }

    function graph_ready() {
        return window.graph && typeof window.graph.serialize === "function";
    }

    function initialization_finished() {
        return window.__pyxis_graph_initialized === true;
    }

    function sync_widgets() {
        if (typeof window.syncWidgetsToProperties === "function") {
            window.syncWidgetsToProperties();
            return;
        }
        if (!graph_ready() || !graph._nodes) return;
        graph._nodes.forEach(function (node) {
            if (!node.properties) node.properties = {};
            if (!node.widgets) return;
            node.widgets.forEach(function (widget) {
                if (widget.type !== "button" && widget.property !== undefined) {
                    if (widget.value !== undefined && widget.value !== null) {
                        node.properties[widget.property] = widget.value;
                    } else if (node.properties[widget.property] !== undefined) {
                        widget.value = node.properties[widget.property];
                    }
                }
            });
        });
    }

    function graph_json() {
        if (!graph_ready()) return "";
        sync_widgets();
        try {
            var serialized = graph.serialize();
            if (serialized && typeof serialized === "object") {
                if (!serialized.extra) serialized.extra = {};
                if (window.__pyxis_active_template_id) {
                    serialized.extra.active_template_id = window.__pyxis_active_template_id;
                    serialized.extra.active_template_name = window.__pyxis_active_template_name || "Plantilla";
                } else {
                    delete serialized.extra.active_template_id;
                    delete serialized.extra.active_template_name;
                }
            }
            return JSON.stringify(serialized);
        } catch (error) {
            console.error("Pyxis: no se pudo serializar la sesión", error);
            return "";
        }
    }

    function save_now() {
        if (!api_ready() || !initialization_finished()) return;

        var current_json = graph_json();
        if (!current_json || current_json === last_saved_json) return;

        if (save_in_flight) {
            save_again = true;
            return;
        }

        save_in_flight = true;
        window.pywebview.api.save_session(current_json).then(function (saved) {
            if (saved === true) last_saved_json = current_json;
        }).catch(function (error) {
            console.error("Pyxis: error guardando sesión", error);
        }).finally(function () {
            save_in_flight = false;
            if (save_again) {
                save_again = false;
                schedule_save(50);
            }
        });
    }

    function schedule_save(delay) {
        if (!initialization_finished()) return;
        if (save_timer !== null) clearTimeout(save_timer);
        var timeout = (delay !== undefined) ? delay : save_delay_ms;
        save_timer = setTimeout(function () {
            save_timer = null;
            save_now();
        }, timeout);
    }

    function hook_widgets() {
        if (!graph_ready() || !graph._nodes) return;
        graph._nodes.forEach(function (node) {
            if (!node.widgets) return;
            node.widgets.forEach(function (widget) {
                if (widget.__pyxis_persistence_hooked) return;
                var old_callback = widget.callback;
                widget.callback = function (value) {
                    if (old_callback) old_callback.apply(this, arguments);
                    schedule_save(50);
                    if (typeof window.updateTemplateUIState === "function") {
                        setTimeout(window.updateTemplateUIState, 50);
                    }
                };
                widget.__pyxis_persistence_hooked = true;
            });
        });
    }

    function on_graph_mutation() {
        hook_widgets();
        schedule_save(50);
        if (typeof window.updateTemplateUIState === "function") {
            setTimeout(window.updateTemplateUIState, 50);
        }
    }

    function start() {
        if (started || !api_ready() || !initialization_finished()) return;
        started = true;

        // 1. Hook on_change
        var old_on_change = graph.on_change;
        graph.on_change = function () {
            if (old_on_change) old_on_change.apply(this, arguments);
            on_graph_mutation();
        };

        // 2. Hook connection changes (critical for connecting / disconnecting wires)
        var old_onConnectionChange = graph.onConnectionChange;
        graph.onConnectionChange = function () {
            if (old_onConnectionChange) old_onConnectionChange.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onNodeConnectionChange = graph.onNodeConnectionChange;
        graph.onNodeConnectionChange = function () {
            if (old_onNodeConnectionChange) old_onNodeConnectionChange.apply(this, arguments);
            on_graph_mutation();
        };

        // 3. Hook node additions and removals
        var old_onNodeAdded = graph.onNodeAdded;
        graph.onNodeAdded = function () {
            if (old_onNodeAdded) old_onNodeAdded.apply(this, arguments);
            on_graph_mutation();
        };

        var old_onNodeRemoved = graph.onNodeRemoved;
        graph.onNodeRemoved = function () {
            if (old_onNodeRemoved) old_onNodeRemoved.apply(this, arguments);
            on_graph_mutation();
        };

        // 4. Hook afterChange
        var old_afterChange = graph.afterChange;
        graph.afterChange = function () {
            if (old_afterChange) old_afterChange.apply(this, arguments);
            on_graph_mutation();
        };

        hook_widgets();
        last_saved_json = graph_json();

        // 5. Lifecycle event listeners
        window.addEventListener("beforeunload", save_now);
        window.addEventListener("pagehide", save_now);
        window.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "hidden") save_now();
        });
        window.addEventListener("blur", save_now);

        // 6. Canvas mouseup hook (catches node movement and finished drags)
        if (window.canvas && window.canvas.canvas) {
            window.canvas.canvas.addEventListener("mouseup", function () {
                schedule_save(100);
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            });
            window.canvas.canvas.addEventListener("touchend", function () {
                schedule_save(100);
                if (typeof window.updateTemplateUIState === "function") {
                    setTimeout(window.updateTemplateUIState, 50);
                }
            });
        }
    }

    function wait_until_ready() {
        if (api_ready() && graph_ready() && initialization_finished()) {
            start();
        } else {
            setTimeout(wait_until_ready, 50);
        }
    }

    window.__pyxis_save_session_now = save_now;
    window.__pyxis_schedule_save = schedule_save;

    window.addEventListener("pywebviewready", wait_until_ready);
    wait_until_ready();
}());